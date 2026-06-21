import { useState } from "react";
import { exportVisitsCsv } from "../api/managerVisits";
import { ApiError } from "../api/client";
import { ManagerDashboardPanels } from "../components/dashboard/ManagerDashboardPanels";
import { FilterBar, type FilterDraft } from "../components/dashboard/FilterBar";
import { Button } from "../components/Button";
import { useManagerDashboard } from "../hooks/useManagerDashboard";
import { ManagerLayout } from "../layouts/ManagerLayout";
import "./ManagerPage.css";

const EMPTY_FILTERS: FilterDraft = {};

export function ManagerPage() {
  const [draftFilters, setDraftFilters] = useState<FilterDraft>(EMPTY_FILTERS);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");
  const {
    appliedFilters,
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

  async function handleExport() {
    setExportError("");
    setExporting(true);
    try {
      await exportVisitsCsv(appliedFilters);
    } catch (err) {
      setExportError(err instanceof ApiError ? err.message : "Export failed");
    } finally {
      setExporting(false);
    }
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

      <div className="manager-panel__header-row">
        <span />
        <Button variant="secondary" onClick={handleExport} loading={exporting}>
          Export visits CSV
        </Button>
      </div>

      {error ? <p className="manager-dashboard__error">{error}</p> : null}
      {exportError ? <p className="manager-dashboard__error">{exportError}</p> : null}

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
