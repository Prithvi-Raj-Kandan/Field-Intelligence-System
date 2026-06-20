import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getVisitSession, saveVisit } from "../api/visits";
import { ApiError } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { SentimentBadge } from "../components/SentimentBadge";
import { useVisitFlow } from "../context/VisitFlowContext";
import { WorkerLayout } from "../layouts/WorkerLayout";
import type { DebriefItem, DebriefResult, Sentiment } from "../types/api";
import "./DebriefReviewPage.css";

type SectionKey = "findings" | "blockers" | "follow_ups";

const sectionTitles: Record<SectionKey, string> = {
  findings: "Key findings",
  blockers: "Blockers observed",
  follow_ups: "Suggested follow-ups",
};

function EditableList({
  items,
  onChange,
}: {
  items: DebriefItem[];
  onChange: (items: DebriefItem[]) => void;
}) {
  const updateText = (index: number, text: string) => {
    const next = items.map((item, i) => (i === index ? { ...item, text } : item));
    onChange(next);
  };

  const remove = (index: number) => onChange(items.filter((_, i) => i !== index));

  const add = () => {
    onChange([...items, { type: items[0]?.type ?? "finding", text: "", source: "text" }]);
  };

  return (
    <ul className="debrief-list">
      {items.map((item, i) => (
        <li key={i} className="debrief-list__item">
          <input
            className="debrief-list__input"
            value={item.text}
            onChange={(e) => updateText(i, e.target.value)}
            placeholder="Enter item..."
          />
          <button type="button" className="debrief-list__remove" onClick={() => remove(i)} aria-label="Remove">
            ×
          </button>
        </li>
      ))}
      <li>
        <button type="button" className="debrief-list__add" onClick={add}>
          + Add item
        </button>
      </li>
    </ul>
  );
}

export function DebriefReviewPage() {
  const navigate = useNavigate();
  const { sessionId, rawNotes, debrief, setDebrief, setRawNotes, completeFlow, resetFlow } = useVisitFlow();
  const [local, setLocal] = useState<DebriefResult | null>(debrief);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [hydrating, setHydrating] = useState(!debrief);

  useEffect(() => {
    if (!sessionId) {
      navigate("/app/log", { replace: true });
      return;
    }
    if (debrief) {
      setLocal(debrief);
      setHydrating(false);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const session = await getVisitSession(sessionId);
        if (cancelled) return;
        if (session.debrief) {
          setDebrief(session.debrief);
          setLocal(session.debrief);
          if (session.raw_notes) setRawNotes(session.raw_notes);
        } else {
          navigate("/app/log/debrief/generate", { replace: true });
        }
      } catch {
        if (!cancelled) navigate("/app/log/debrief/generate", { replace: true });
      } finally {
        if (!cancelled) setHydrating(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [sessionId, debrief, setDebrief, setRawNotes, navigate]);

  if (!sessionId || hydrating || !local) {
    return (
      <WorkerLayout title="Review debrief" hideNav>
        <div className="debrief-loading">
          <div className="debrief-loading__spinner" aria-hidden />
          <p>Loading debrief…</p>
        </div>
      </WorkerLayout>
    );
  }

  const updateSection = (key: SectionKey, items: DebriefItem[]) => {
    setLocal((d) => (d ? { ...d, [key]: items } : d));
  };

  const handleSave = async () => {
    setError("");
    setLoading(true);
    try {
      await saveVisit(sessionId, local, rawNotes);
      completeFlow();
      navigate("/app/log/success");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Save failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <WorkerLayout title="Review debrief" hideNav>
      <div className="debrief-review animate-in">
        <div className="debrief-review__sentiment">
          <span>Community sentiment</span>
          <SentimentBadge
            sentiment={local.sentiment}
            onChange={(s: Sentiment) => setLocal((d) => (d ? { ...d, sentiment: s } : d))}
          />
        </div>

        {(Object.keys(sectionTitles) as SectionKey[]).map((key) => (
          <Card key={key} title={sectionTitles[key]}>
            <EditableList items={local[key]} onChange={(items) => updateSection(key, items)} />
          </Card>
        ))}

        {error ? <p className="debrief-review__error">{error}</p> : null}

        <div className="debrief-review__actions">
          <Button variant="secondary" onClick={() => { resetFlow(); navigate("/app/log"); }}>
            Discard
          </Button>
          <Button onClick={handleSave} loading={loading}>
            Save visit
          </Button>
        </div>
      </div>
    </WorkerLayout>
  );
}

export function SuccessPage() {
  const navigate = useNavigate();
  const { resetFlow } = useVisitFlow();

  const handleAnother = () => {
    resetFlow();
    navigate("/app/log");
  };

  return (
    <WorkerLayout title="Visit saved" hideNav>
      <div className="success-page animate-in">
        <div className="success-page__icon">✓</div>
        <h2>Visit saved successfully</h2>
        <p>Your debrief has been recorded and will feed into program analytics.</p>
        <Button fullWidth size="lg" onClick={handleAnother}>
          Log another visit
        </Button>
        <Button variant="ghost" fullWidth onClick={() => navigate("/app/visits")}>
          View previous visits
        </Button>
      </div>
    </WorkerLayout>
  );
}
