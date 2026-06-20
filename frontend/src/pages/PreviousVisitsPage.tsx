import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMyVisits } from "../api/visits";
import { ApiError } from "../api/client";
import { SentimentBadge } from "../components/SentimentBadge";
import { WorkerLayout } from "../layouts/WorkerLayout";
import type { Sentiment, VisitSummary } from "../types/api";
import "./PreviousVisitsPage.css";

export function PreviousVisitsPage() {
  const [visits, setVisits] = useState<VisitSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listMyVisits()
      .then(setVisits)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load visits"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <WorkerLayout title="Previous visits">
      <div className="visits-list animate-in">
        {loading ? <p className="visits-list__muted">Loading visits…</p> : null}
        {error ? <p className="visits-list__error">{error}</p> : null}
        {!loading && !error && visits.length === 0 ? (
          <div className="visits-list__empty">
            <p>No visits saved yet.</p>
            <Link to="/app/log">Log your first visit</Link>
          </div>
        ) : null}
        <ul className="visits-list__items">
          {visits.map((v) => (
            <li key={v.id} className="visits-list__card">
              <div className="visits-list__head">
                <strong>{v.location}</strong>
                {v.sentiment ? (
                  <SentimentBadge sentiment={v.sentiment as Sentiment} />
                ) : null}
              </div>
              <p className="visits-list__meta">
                {v.program_area} · {v.visit_date}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </WorkerLayout>
  );
}
