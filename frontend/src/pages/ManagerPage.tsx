import { useCallback, useEffect, useMemo, useState } from "react";
import { getBlockerInsights, getInsightSummary, getSentimentTrend } from "../api/insights";
import { listManagerVisits } from "../api/managerVisits";
import { ApiError } from "../api/client";
import { BlockersByRegionChart } from "../components/dashboard/BlockersByRegionChart";
import { BlockersTable } from "../components/dashboard/BlockersTable";
import "../components/dashboard/Charts.css";
import { FilterBar, type FilterDraft } from "../components/dashboard/FilterBar";
import { MetricCards } from "../components/dashboard/MetricCards";
import { SentimentTrendChart } from "../components/dashboard/SentimentTrendChart";
import { VisitDetailDrawer } from "../components/dashboard/VisitDetailDrawer";
import { SentimentBadge } from "../components/SentimentBadge";
import { ManagerLayout } from "../layouts/ManagerLayout";
import type {
  BlockerInsightItem,
  InsightSummary,
  SentimentTrendItem,
  VisitListItem,
} from "../types/api";
import "./ManagerPage.css";

const EMPTY_FILTERS: FilterDraft = {};

export function ManagerPage() {
  const [draftFilters, setDraftFilters] = useState<FilterDraft>(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<FilterDraft>(EMPTY_FILTERS);
  const [summary, setSummary] = useState<InsightSummary | null>(null);
  const [blockers, setBlockers] = useState<BlockerInsightItem[]>([]);
  const [blockersByRegion, setBlockersByRegion] = useState<BlockerInsightItem[]>([]);
  const [sentimentTrend, setSentimentTrend] = useState<SentimentTrendItem[]>([]);
  const [visits, setVisits] = useState<VisitListItem[]>([]);
  const [programAreas, setProgramAreas] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedVisitId, setSelectedVisitId] = useState<number | null>(null);

  const loadFilterOptions = useCallback(async () => {
    const res = await listManagerVisits({ page: 1, page_size: 100 });
    const areas = [...new Set(res.items.map((v) => v.program_area))].sort();
    const locs = [...new Set(res.items.map((v) => v.location))].sort();
    setProgramAreas(areas);
    setLocations(locs);
  }, []);

  const loadDashboard = useCallback(async (filters: FilterDraft) => {
    setLoading(true);
    setError("");
    try {
      const [summaryRes, blockersRes, regionRes, trendRes, visitsRes] = await Promise.all([
        getInsightSummary(filters),
        getBlockerInsights({ ...filters, group_by: "location" }),
        getBlockerInsights({ ...filters, group_by: "location" }),
        getSentimentTrend({ ...filters, interval: "week" }),
        listManagerVisits({ ...filters, page: 1, page_size: 50 }),
      ]);
      setSummary(summaryRes);
      setBlockers(blockersRes.items);
      setBlockersByRegion(regionRes.items);
      setSentimentTrend(trendRes.items);
      setVisits(visitsRes.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFilterOptions().catch(() => {
      /* filter dropdowns stay empty until visits load */
    });
  }, [loadFilterOptions]);

  useEffect(() => {
    loadDashboard(appliedFilters);
  }, [appliedFilters, loadDashboard]);

  const hasData = useMemo(
    () => (summary?.total_visits ?? 0) > 0 || visits.length > 0,
    [summary, visits.length],
  );

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

      {error ? <p className="manager-dashboard__error">{error}</p> : null}

      <MetricCards summary={summary} loading={loading} />

      {hasData || loading ? (
        <>
          <div className="dashboard-charts">
            <section className="dashboard-chart-card">
              <h3>Blockers by region</h3>
              <BlockersByRegionChart items={blockersByRegion} loading={loading} />
            </section>
            <section className="dashboard-chart-card">
              <h3>Sentiment over time</h3>
              <SentimentTrendChart items={sentimentTrend} loading={loading} />
            </section>
          </div>

          <section className="manager-dashboard__panel">
            <h3>Recurring blockers</h3>
            <BlockersTable items={blockers} loading={loading} />
          </section>

          <section className="manager-dashboard__panel">
            <h3>All visits</h3>
            {loading ? (
              <p className="manager-dashboard__muted">Loading visits…</p>
            ) : visits.length === 0 ? (
              <p className="manager-dashboard__muted">No visits match filters.</p>
            ) : (
              <div className="manager-visits-table-wrap">
                <table className="manager-visits-table">
                  <thead>
                    <tr>
                      <th>Location</th>
                      <th>Program</th>
                      <th>Date</th>
                      <th>Sentiment</th>
                      <th>Blockers</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visits.map((visit) => (
                      <tr
                        key={visit.id}
                        className="manager-visits-table__row--clickable"
                        onClick={() => setSelectedVisitId(visit.id)}
                      >
                        <td>{visit.location}</td>
                        <td>{visit.program_area}</td>
                        <td>{visit.visit_date}</td>
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
        </>
      ) : null}

      <VisitDetailDrawer visitId={selectedVisitId} onClose={() => setSelectedVisitId(null)} />
    </ManagerLayout>
  );
}
