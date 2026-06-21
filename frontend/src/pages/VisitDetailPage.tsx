import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getVisit } from "../api/visits";
import { ApiError } from "../api/client";
import { AuthenticatedAudio, AuthenticatedImage } from "../components/AuthenticatedMedia";
import { Card } from "../components/Card";
import { SentimentBadge } from "../components/SentimentBadge";
import { WorkerLayout } from "../layouts/WorkerLayout";
import type { DebriefItem, Sentiment, VisitDetail } from "../types/api";
import "./VisitDetailPage.css";

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

export function VisitDetailPage() {
  const { visitId } = useParams<{ visitId: string }>();
  const id = Number(visitId);
  const [visit, setVisit] = useState<VisitDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id || Number.isNaN(id)) {
      setError("Invalid visit");
      setLoading(false);
      return;
    }
    getVisit(id)
      .then(setVisit)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load visit"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <WorkerLayout title="Visit summary">
        <p className="visit-detail__muted">Loading…</p>
      </WorkerLayout>
    );
  }

  if (error || !visit) {
    return (
      <WorkerLayout title="Visit summary">
        <p className="visit-detail__error">{error || "Visit not found"}</p>
        <Link to="/app/visits">Back to visits</Link>
      </WorkerLayout>
    );
  }

  const grouped = groupFindings(visit.findings);

  return (
    <WorkerLayout title="Visit summary">
      <div className="visit-detail animate-in">
        <Link to="/app/visits" className="visit-detail__back">
          ← Back to visits
        </Link>

        <header className="visit-detail__header">
          <h2 className="visit-detail__location">{visit.location}</h2>
          <p className="visit-detail__meta">
            {visit.program_area} · {visit.visit_date}
          </p>
          {visit.stakeholders ? (
            <p className="visit-detail__meta">Stakeholders: {visit.stakeholders}</p>
          ) : null}
          {visit.sentiment ? (
            <div className="visit-detail__sentiment">
              <span>Community sentiment</span>
              <SentimentBadge sentiment={visit.sentiment as Sentiment} />
            </div>
          ) : null}
        </header>

        {visit.raw_notes ? (
          <Card title="Field notes">
            <p className="visit-detail__notes">{visit.raw_notes}</p>
          </Card>
        ) : null}

        {visit.voice_memo_paths.length > 0 ? (
          <Card title="Voice memos">
            <ul className="visit-detail__audio-list">
              {visit.voice_memo_paths.map((path, index) => (
                <li key={path}>
                  <span className="visit-detail__audio-label">Recording {index + 1}</span>
                  <AuthenticatedAudio path={path} />
                </li>
              ))}
            </ul>
          </Card>
        ) : null}

        {visit.note_image_paths.length > 0 ? (
          <Card title="Note images">
            <div className="visit-detail__photos">
              {visit.note_image_paths.map((path) => (
                <AuthenticatedImage key={path} path={path} alt="Visit note" />
              ))}
            </div>
          </Card>
        ) : null}

        {visit.field_photo_paths.length > 0 ? (
          <Card title="Context photos">
            <div className="visit-detail__photos">
              {visit.field_photo_paths.map((path) => (
                <AuthenticatedImage key={path} path={path} alt="Field context" />
              ))}
            </div>
          </Card>
        ) : null}

        {(Object.keys(sectionTitles) as Array<keyof typeof sectionTitles>).map((type) => {
          const key =
            type === "finding" ? "findings" : type === "blocker" ? "blockers" : "follow_ups";
          const items = grouped[key];
          if (items.length === 0) return null;
          return (
            <Card key={type} title={sectionTitles[type]}>
              <ul className="visit-detail__list">
                {items.map((item, i) => (
                  <li key={i}>{item.text}</li>
                ))}
              </ul>
            </Card>
          );
        })}
      </div>
    </WorkerLayout>
  );
}
