import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { generateDebrief, getVisitSession } from "../api/visits";
import { ApiError } from "../api/client";
import { Button } from "../components/Button";
import { useVisitFlow } from "../context/VisitFlowContext";
import { WorkerLayout } from "../layouts/WorkerLayout";
import type { DebriefResult, VisitFormData } from "../types/api";
import "./DebriefReviewPage.css";

/** One in-flight debrief per session — survives React StrictMode remounts. */
const inflightDebrief = new Map<string, Promise<DebriefResult>>();

async function recoverDebrief(sessionId: string): Promise<DebriefResult | null> {
  const session = await getVisitSession(sessionId);
  if (session.status === "debrief_ready" && session.debrief) {
    return session.debrief;
  }
  return null;
}

function startDebrief(
  sessionId: string,
  rawNotes: string,
  form: VisitFormData,
): Promise<DebriefResult> {
  const existing = inflightDebrief.get(sessionId);
  if (existing) return existing;

  const promise = generateDebrief(
    sessionId,
    rawNotes,
    form.field_photos,
    form.voice_memos,
  )
    .then((res) => res.debrief)
    .finally(() => {
      inflightDebrief.delete(sessionId);
    });

  inflightDebrief.set(sessionId, promise);
  return promise;
}

export function DebriefGeneratePage() {
  const navigate = useNavigate();
  const { sessionId, rawNotes, form, setDebrief, debrief } = useVisitFlow();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [recovering, setRecovering] = useState(false);

  useEffect(() => {
    if (!sessionId || !form) {
      navigate("/app/log", { replace: true });
      return;
    }
    if (debrief) {
      navigate("/app/log/debrief", { replace: true });
      return;
    }

    let showError = true;

    const finishWithDebrief = (result: DebriefResult) => {
      // Always write to context — provider survives StrictMode remounts.
      setDebrief(result);
      navigate("/app/log/debrief", { replace: true });
    };

    (async () => {
      try {
        const cached = await recoverDebrief(sessionId);
        if (cached) {
          finishWithDebrief(cached);
          return;
        }

        const result = await startDebrief(sessionId, rawNotes, form);
        finishWithDebrief(result);
      } catch (err) {
        try {
          const cached = await recoverDebrief(sessionId);
          if (cached) {
            finishWithDebrief(cached);
            return;
          }
        } catch {
          /* ignore recovery errors */
        }
        if (showError) {
          setError(err instanceof ApiError ? err.message : "Debrief generation failed");
          setLoading(false);
        }
      }
    })();

    return () => {
      showError = false;
    };
  }, [sessionId, rawNotes, form, debrief, setDebrief, navigate]);

  const handleRecover = async () => {
    if (!sessionId) return;
    setRecovering(true);
    setError("");
    try {
      const cached = await recoverDebrief(sessionId);
      if (cached) {
        setDebrief(cached);
        navigate("/app/log/debrief", { replace: true });
        return;
      }
      setError("No debrief found for this session yet. Try generating again in a minute.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load session");
    } finally {
      setRecovering(false);
      setLoading(false);
    }
  };

  const handleRetry = async () => {
    if (!sessionId || !form) return;
    setLoading(true);
    setError("");
    try {
      const cached = await recoverDebrief(sessionId);
      if (cached) {
        setDebrief(cached);
        navigate("/app/log/debrief", { replace: true });
        return;
      }
      const result = await startDebrief(sessionId, rawNotes, form);
      setDebrief(result);
      navigate("/app/log/debrief", { replace: true });
    } catch (err) {
      const cached = await recoverDebrief(sessionId).catch(() => null);
      if (cached) {
        setDebrief(cached);
        navigate("/app/log/debrief", { replace: true });
        return;
      }
      setError(err instanceof ApiError ? err.message : "Debrief generation failed");
      setLoading(false);
    }
  };

  return (
    <WorkerLayout title="Generating debrief" hideNav>
      <div className="debrief-loading animate-in">
        {loading && !error ? (
          <>
            <div className="debrief-loading__spinner" aria-hidden />
            <p>Analyzing your visit notes and context media…</p>
            <p className="debrief-loading__sub">This may take 10–20 seconds</p>
          </>
        ) : null}
        {error ? (
          <>
            <p className="debrief-loading__error">{error}</p>
            <p className="debrief-loading__sub">
              If processing finished on the server, use &quot;Continue to review&quot; below.
            </p>
            <div className="debrief-loading__actions">
              <Button onClick={handleRecover} loading={recovering}>
                Continue to review
              </Button>
              <Button variant="secondary" onClick={handleRetry}>
                Retry
              </Button>
              <Button variant="ghost" onClick={() => navigate("/app/log")}>
                Start over
              </Button>
            </div>
          </>
        ) : null}
      </div>
    </WorkerLayout>
  );
}
