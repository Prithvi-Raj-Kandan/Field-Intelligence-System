import { useState } from "react";
import { ManagerDashboardPanels } from "../components/dashboard/ManagerDashboardPanels";
import { FilterBar, type FilterDraft } from "../components/dashboard/FilterBar";
import { useManagerDashboard } from "../hooks/useManagerDashboard";
import { ManagerLayout } from "../layouts/ManagerLayout";
import "./ManagerPage.css";

const EMPTY_FILTERS: FilterDraft = {};

export function ManagerPage() {
  const [draftFilters, setDraftFilters] = useState<FilterDraft>(EMPTY_FILTERS);
  const {
    setAppliedFilters,
    summary,
    recurringBlockers,
    blockersByRegion,
    sentimentTrend,
    programAreas,
    locations,
    loading,
    error,
  } = useManagerDashboard();

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

      <ManagerDashboardPanels
        summary={summary}
        recurringBlockers={recurringBlockers}
        blockersByRegion={blockersByRegion}
        sentimentTrend={sentimentTrend}
        loading={loading}
      />
    </ManagerLayout>
  );
}
