import { useCallback, useEffect, useMemo, useState } from "react";
import { listManagerVisits } from "../api/managerVisits";
import { ApiError } from "../api/client";
import { FilterBar, type FilterDraft } from "../components/dashboard/FilterBar";
import { VisitDetailDrawer } from "../components/dashboard/VisitDetailDrawer";
import { SelectField } from "../components/Input";
import { SentimentBadge } from "../components/SentimentBadge";
import { ManagerLayout } from "../layouts/ManagerLayout";
import type { VisitListItem } from "../types/api";
import "./ManagerPage.css";

const EMPTY_FILTERS: FilterDraft = {};

type VisitSort =
  | "date_desc"
  | "date_asc"
  | "location_asc"
  | "blockers_desc"
  | "blockers_asc";

export function ManagerVisitsPage() {
  const [draftFilters, setDraftFilters] = useState<FilterDraft>(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<FilterDraft>(EMPTY_FILTERS);
  const [visits, setVisits] = useState<VisitListItem[]>([]);
  const [programAreas, setProgramAreas] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedVisitId, setSelectedVisitId] = useState<number | null>(null);
  const [sentimentFilter, setSentimentFilter] = useState("all");
  const [sort, setSort] = useState<VisitSort>("date_desc");

  const loadFilterOptions = useCallback(async () => {
    const res = await listManagerVisits({ page: 1, page_size: 100 });
    setProgramAreas([...new Set(res.items.map((v) => v.program_area))].sort());
    setLocations([...new Set(res.items.map((v) => v.location))].sort());
  }, []);

  const loadVisits = useCallback(async (filters: FilterDraft) => {
    setLoading(true);
    setError("");
    try {
      const res = await listManagerVisits({ ...filters, page: 1, page_size: 100 });
      setVisits(res.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load visits");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFilterOptions().catch(() => {});
  }, [loadFilterOptions]);

  useEffect(() => {
    loadVisits(appliedFilters);
  }, [appliedFilters, loadVisits]);

  const displayedVisits = useMemo(() => {
    let list = [...visits];
    if (sentimentFilter !== "all") {
      list = list.filter((v) => v.sentiment === sentimentFilter);
    }
    list.sort((a, b) => {
      if (sort === "blockers_desc") return b.blocker_count - a.blocker_count;
      if (sort === "blockers_asc") return a.blocker_count - b.blocker_count;
      if (sort === "location_asc") return a.location.localeCompare(b.location);
      const dateCmp = a.visit_date.localeCompare(b.visit_date);
      return sort === "date_asc" ? dateCmp : -dateCmp;
    });
    return list;
  }, [visits, sentimentFilter, sort]);

  function applyFilters() {
    setAppliedFilters({ ...draftFilters });
  }

  function clearFilters() {
    setDraftFilters(EMPTY_FILTERS);
    setAppliedFilters(EMPTY_FILTERS);
  }

  return (
    <ManagerLayout>
      <FilterBar
        draft={draftFilters}
        onChange={setDraftFilters}
        onApply={applyFilters}
        onClear={clearFilters}
        programAreas={programAreas}
        locations={locations}
      />

      <div className="manager-visits-toolbar">
        <SelectField label="Sort by" value={sort} onChange={(e) => setSort(e.target.value as VisitSort)}>
          <option value="date_desc">Newest first</option>
          <option value="date_asc">Oldest first</option>
          <option value="location_asc">Location A–Z</option>
          <option value="blockers_desc">Most blockers</option>
          <option value="blockers_asc">Fewest blockers</option>
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

      {error ? <p className="manager-dashboard__error">{error}</p> : null}

      <section className="manager-dashboard__panel">
        <h3>All visits</h3>
        {loading ? (
          <p className="manager-dashboard__muted">Loading visits…</p>
        ) : displayedVisits.length === 0 ? (
          <p className="manager-dashboard__muted">No visits match filters.</p>
        ) : (
          <div className="manager-visits-table-wrap">
            <table className="manager-visits-table">
              <thead>
                <tr>
                  <th>Location</th>
                  <th>Program</th>
                  <th>Date</th>
                  <th>Worker</th>
                  <th>Sentiment</th>
                  <th>Blockers</th>
                </tr>
              </thead>
              <tbody>
                {displayedVisits.map((visit) => (
                  <tr
                    key={visit.id}
                    className="manager-visits-table__row--clickable"
                    onClick={() => setSelectedVisitId(visit.id)}
                  >
                    <td>{visit.location}</td>
                    <td>{visit.program_area}</td>
                    <td>{visit.visit_date}</td>
                    <td>{visit.worker_email ?? "—"}</td>
                    <td>
                      {visit.sentiment ? (
                        <SentimentBadge sentiment={visit.sentiment} />
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>{visit.blocker_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <VisitDetailDrawer visitId={selectedVisitId} onClose={() => setSelectedVisitId(null)} />
    </ManagerLayout>
  );
}
