import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listRecordings } from "../api/visits";
import { ApiError } from "../api/client";
import { AuthenticatedAudio } from "../components/AuthenticatedMedia";
import { WorkerLayout } from "../layouts/WorkerLayout";
import type { RecordingMediaItem } from "../types/api";
import "./RecordingsPage.css";

export function RecordingsPage() {
  const [items, setItems] = useState<RecordingMediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listRecordings()
      .then(setItems)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load recordings"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <WorkerLayout title="Recordings">
      <div className="recordings animate-in">
        <p className="recordings__hint">Voice memos from your saved field visits</p>
        {loading ? <p className="recordings__muted">Loading…</p> : null}
        {error ? <p className="recordings__error">{error}</p> : null}
        {!loading && items.length === 0 ? (
          <p className="recordings__muted">No recordings yet. Save a visit with voice memos.</p>
        ) : null}
        <ul className="recordings__list">
          {items.map((item) => (
            <li key={`${item.visit_id}-${item.path}`} className="recordings__item">
              <Link to={`/app/visits/${item.visit_id}`} className="recordings__header">
                <strong>{item.location}</strong>
                <span>{item.visit_date}</span>
                <span className="recordings__cta">View summary →</span>
              </Link>
              <AuthenticatedAudio path={item.path} className="recordings__player" />
            </li>
          ))}
        </ul>
      </div>
    </WorkerLayout>
  );
}
