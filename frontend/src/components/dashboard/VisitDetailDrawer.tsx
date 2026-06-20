import { useEffect, useState } from "react";
import { getManagerVisit } from "../../api/managerVisits";
import { ApiError } from "../../api/client";
import { Button } from "../Button";
import { SentimentBadge } from "../SentimentBadge";
import type { DebriefItem, ManagerVisitDetail } from "../../types/api";
import "./VisitDetailDrawer.css";

const sectionTitles = {
  finding: "Key findings",
  blocker: "Blockers observed",
  follow_up: "Suggested follow-ups",
} as const;

function groupFindings(items: DebriefItem[]) {
  return {
    findings: items.filter((i) => i.type === "finding"),
    blockers: items.filter((i) => i.type === "blocker"),
    follow_ups: items.filter((i) => i.type === "follow_up"),
  };
}

interface VisitDetailDrawerProps {
  visitId: number | null;
  onClose: () => void;
}

export function VisitDetailDrawer({ visitId, onClose }: VisitDetailDrawerProps) {
  const [visit, setVisit] = useState<ManagerVisitDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!visitId) {
      setVisit(null);
      setError("");
      return;
    }
    setLoading(true);
    setError("");
    getManagerVisit(visitId)
      .then(setVisit)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load visit"))
      .finally(() => setLoading(false));
  }, [visitId]);

  if (!visitId) return null;

  const grouped = visit ? groupFindings(visit.findings) : null;

  return (
    <>
      <button type="button" className="visit-drawer__backdrop" aria-label="Close" onClick={onClose} />
      <aside className="visit-drawer" role="dialog" aria-modal="true" aria-labelledby="visit-drawer-title">
        <header className="visit-drawer__header">
          <h2 id="visit-drawer-title">Visit detail</h2>
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </header>

        {loading ? <p className="visit-drawer__muted">Loading…</p> : null}
        {error ? <p className="visit-drawer__error">{error}</p> : null}

        {visit && grouped ? (
          <div className="visit-drawer__body">
            <div className="visit-drawer__meta">
              <h3>{visit.location}</h3>
              <p>
                {visit.program_area} · {visit.visit_date}
              </p>
              {visit.stakeholders ? <p>Stakeholders: {visit.stakeholders}</p> : null}
              {visit.sentiment ? (
                <div className="visit-drawer__sentiment">
                  <span>Sentiment</span>
                  <SentimentBadge sentiment={visit.sentiment} />
                </div>
              ) : null}
            </div>

            <section className="visit-drawer__section">
              <h4>Field notes</h4>
              <p className="visit-drawer__notes">{visit.raw_notes}</p>
            </section>

            {visit.note_image_urls.length > 0 ? (
              <section className="visit-drawer__section">
                <h4>Note images</h4>
                <div className="visit-drawer__images">
                  {visit.note_image_urls.map((url) => (
                    <img key={url} src={url} alt="Visit note" loading="lazy" />
                  ))}
                </div>
              </section>
            ) : null}

            {visit.field_photo_urls.length > 0 ? (
              <section className="visit-drawer__section">
                <h4>Field photos</h4>
                <div className="visit-drawer__images">
                  {visit.field_photo_urls.map((url) => (
                    <img key={url} src={url} alt="Field photo" loading="lazy" />
                  ))}
                </div>
              </section>
            ) : null}

            {(["findings", "blockers", "follow_ups"] as const).map((key) => {
              const items = grouped[key];
              if (items.length === 0) return null;
              const type = key === "findings" ? "finding" : key === "blockers" ? "blocker" : "follow_up";
              return (
                <section key={key} className="visit-drawer__section">
                  <h4>{sectionTitles[type]}</h4>
                  <ul className="visit-drawer__list">
                    {items.map((item, i) => (
                      <li key={`${type}-${i}`}>{item.text}</li>
                    ))}
                  </ul>
                </section>
              );
            })}
          </div>
        ) : null}
      </aside>
    </>
  );
}
