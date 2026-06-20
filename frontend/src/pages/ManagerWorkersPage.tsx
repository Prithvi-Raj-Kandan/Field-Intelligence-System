import { useEffect, useState } from "react";
import { listManagerVisits } from "../api/managerVisits";
import { listWorkers } from "../api/workers";
import { ApiError } from "../api/client";
import { FilterBar, type FilterDraft } from "../components/dashboard/FilterBar";
import { MetricCards } from "../components/dashboard/MetricCards";
import { RecurringBlockersTable } from "../components/dashboard/RecurringBlockersTable";
import { VisitDetailDrawer } from "../components/dashboard/VisitDetailDrawer";
import { SentimentBadge } from "../components/SentimentBadge";
import { useManagerDashboard } from "../hooks/useManagerDashboard";
import { ManagerLayout } from "../layouts/ManagerLayout";
import type { VisitListItem, WorkerProfile } from "../types/api";
import "./ManagerPage.css";
import "./ManagerWorkersPage.css";

const EMPTY_FILTERS: FilterDraft = {};

export function ManagerWorkersPage() {
  const [workers, setWorkers] = useState<WorkerProfile[]>([]);
  const [workersLoading, setWorkersLoading] = useState(true);
  const [workersError, setWorkersError] = useState("");
  const [selectedWorkerId, setSelectedWorkerId] = useState<number | null>(null);
  const [draftFilters, setDraftFilters] = useState<FilterDraft>(EMPTY_FILTERS);
  const [visits, setVisits] = useState<VisitListItem[]>([]);
  const [visitsLoading, setVisitsLoading] = useState(false);
  const [selectedVisitId, setSelectedVisitId] = useState<number | null>(null);

  const {
    appliedFilters,
    setAppliedFilters,
    summary,
    recurringBlockers,
    programAreas,
    locations,
    loading: dashboardLoading,
    error: dashboardError,
  } = useManagerDashboard(selectedWorkerId ?? undefined);

  useEffect(() => {
    listWorkers()
      .then((res) => {
        setWorkers(res.items);
        setSelectedWorkerId((current) => current ?? res.items[0]?.id ?? null);
      })
      .catch((err) =>
        setWorkersError(err instanceof ApiError ? err.message : "Failed to load workers"),
      )
      .finally(() => setWorkersLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedWorkerId) {
      setVisits([]);
      return;
    }
    setVisitsLoading(true);
    listManagerVisits({
      ...appliedFilters,
      worker_id: selectedWorkerId,
      page: 1,
      page_size: 100,
    })
      .then((res) => setVisits(res.items))
      .catch(() => setVisits([]))
      .finally(() => setVisitsLoading(false));
  }, [selectedWorkerId, appliedFilters]);

  const selectedWorker = workers.find((w) => w.id === selectedWorkerId) ?? null;
  const loading = dashboardLoading || visitsLoading;

  function applyFilters() {
    setAppliedFilters({ ...draftFilters });
  }

  function clearFilters() {
    setDraftFilters(EMPTY_FILTERS);
    setAppliedFilters(EMPTY_FILTERS);
  }

  return (
    <ManagerLayout>
      <div className="workers-page">
        <aside className="workers-page__list">
          <h2>Field workers</h2>
          {workersLoading ? (
            <p className="workers-page__muted">Loading workers…</p>
          ) : workersError ? (
            <p className="workers-page__error">{workersError}</p>
          ) : workers.length === 0 ? (
            <p className="workers-page__muted">No field workers found.</p>
          ) : (
            <ul className="workers-page__cards">
              {workers.map((worker) => (
                <li key={worker.id}>
                  <button
                    type="button"
                    className={`worker-card${selectedWorkerId === worker.id ? " worker-card--active" : ""}`}
                    onClick={() => {
                      setSelectedWorkerId(worker.id);
                      setDraftFilters(EMPTY_FILTERS);
                      setAppliedFilters(EMPTY_FILTERS);
                    }}
                  >
                    <span className="worker-card__email">{worker.email}</span>
                    <span className="worker-card__stat">{worker.visit_count} visits</span>
                    <span className="worker-card__stat">
                      {worker.negative_sentiment_pct}% negative
                    </span>
                    {worker.last_visit_date ? (
                      <span className="worker-card__meta">
                        Last visit: {worker.last_visit_date}
                      </span>
                    ) : null}
                    {worker.most_common_blocker ? (
                      <span className="worker-card__blocker">
                        Top blocker: {worker.most_common_blocker}
                      </span>
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="workers-page__analytics">
          {selectedWorker ? (
            <>
              <header className="workers-page__header">
                <h2>{selectedWorker.email}</h2>
                <p>
                  {selectedWorker.visit_count} visits logged
                  {selectedWorker.last_visit_date
                    ? ` · Last visit ${selectedWorker.last_visit_date}`
                    : ""}
                </p>
              </header>

              <FilterBar
                draft={draftFilters}
                onChange={setDraftFilters}
                onApply={applyFilters}
                onClear={clearFilters}
                programAreas={programAreas}
                locations={locations}
              />

              {dashboardError ? (
                <p className="manager-dashboard__error">{dashboardError}</p>
              ) : null}

              <MetricCards summary={summary} loading={loading} />

              <section className="manager-dashboard__panel">
                <h3>Visits</h3>
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

              <section className="manager-dashboard__panel">
                <h3>Recurring blockers</h3>
                <p className="manager-dashboard__panel-desc">
                  Blockers linked across regions — same issue appearing in multiple locations.
                </p>
                <RecurringBlockersTable items={recurringBlockers} loading={loading} />
              </section>
            </>
          ) : (
            <p className="workers-page__muted">Select a worker to view analytics.</p>
          )}
        </div>
      </div>

      <VisitDetailDrawer visitId={selectedVisitId} onClose={() => setSelectedVisitId(null)} />
    </ManagerLayout>
  );
}
