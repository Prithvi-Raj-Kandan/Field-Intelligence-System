import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listMyVisits } from "../api/visits";
import { ApiError } from "../api/client";
import { SelectField } from "../components/Input";
import { SentimentBadge } from "../components/SentimentBadge";
import { WorkerLayout } from "../layouts/WorkerLayout";
import type { Sentiment, VisitSummary } from "../types/api";
import "./PreviousVisitsPage.css";

type SortOption = "date_desc" | "date_asc" | "location_asc";

const PROGRAM_AREAS = [
  "All programs",
  "Water Access",
  "Rural Housing",
  "Agriculture",
  "Livelihoods",
  "Education",
  "Health",
  "Other",
];

export function PreviousVisitsPage() {
  const [visits, setVisits] = useState<VisitSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sort, setSort] = useState<SortOption>("date_desc");
  const [programFilter, setProgramFilter] = useState("All programs");
  const [sentimentFilter, setSentimentFilter] = useState("all");

  useEffect(() => {
    listMyVisits()
      .then(setVisits)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load visits"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let list = [...visits];
    if (programFilter !== "All programs") {
      list = list.filter((v) => v.program_area === programFilter);
    }
    if (sentimentFilter !== "all") {
      list = list.filter((v) => v.sentiment === sentimentFilter);
    }
    list.sort((a, b) => {
      if (sort === "location_asc") return a.location.localeCompare(b.location);
      const da = a.visit_date.localeCompare(b.visit_date);
      return sort === "date_asc" ? da : -da;
    });
    return list;
  }, [visits, sort, programFilter, sentimentFilter]);

  return (
    <WorkerLayout title="Previous visits">
      <div className="visits-list animate-in">
        <div className="visits-list__filters">
          <SelectField label="Sort by" value={sort} onChange={(e) => setSort(e.target.value as SortOption)}>
            <option value="date_desc">Newest first</option>
            <option value="date_asc">Oldest first</option>
            <option value="location_asc">Location A–Z</option>
          </SelectField>
          <SelectField
            label="Program"
            value={programFilter}
            onChange={(e) => setProgramFilter(e.target.value)}
          >
            {PROGRAM_AREAS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </SelectField>
          <SelectField
            label="Sentiment"
            value={sentimentFilter}
            onChange={(e) => setSentimentFilter(e.target.value)}
          >
            <option value="all">All sentiments</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
          </SelectField>
        </div>

        {loading ? <p className="visits-list__muted">Loading visits…</p> : null}
        {error ? <p className="visits-list__error">{error}</p> : null}
        {!loading && !error && visits.length === 0 ? (
          <div className="visits-list__empty">
            <p>No visits saved yet.</p>
            <Link to="/app/log">Log your first visit</Link>
          </div>
        ) : null}
        {!loading && !error && visits.length > 0 && filtered.length === 0 ? (
          <p className="visits-list__muted">No visits match your filters.</p>
        ) : null}
        <ul className="visits-list__items">
          {filtered.map((v) => (
            <li key={v.id}>
              <Link to={`/app/visits/${v.id}`} className="visits-list__card">
                <div className="visits-list__head">
                  <strong>{v.location}</strong>
                  {v.sentiment ? (
                    <SentimentBadge sentiment={v.sentiment as Sentiment} />
                  ) : null}
                </div>
                <p className="visits-list__meta">
                  {v.program_area} · {v.visit_date}
                </p>
                <span className="visits-list__cta">View summary →</span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </WorkerLayout>
  );
}
