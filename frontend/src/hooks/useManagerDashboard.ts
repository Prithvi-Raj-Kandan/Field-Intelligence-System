import { useCallback, useEffect, useState } from "react";
import {
  getBlockerInsights,
  getInsightSummary,
  getRecurringBlockers,
  getSentimentTrend,
} from "../api/insights";
import { listManagerVisits } from "../api/managerVisits";
import { ApiError } from "../api/client";
import type {
  BlockerInsightItem,
  InsightQueryParams,
  InsightSummary,
  RecurringBlockerItem,
  SentimentTrendItem,
} from "../types/api";
import type { FilterDraft } from "../components/dashboard/FilterBar";

export function useManagerDashboard(workerId?: number) {
  const [appliedFilters, setAppliedFilters] = useState<FilterDraft>({});
  const [summary, setSummary] = useState<InsightSummary | null>(null);
  const [recurringBlockers, setRecurringBlockers] = useState<RecurringBlockerItem[]>([]);
  const [blockersByRegion, setBlockersByRegion] = useState<BlockerInsightItem[]>([]);
  const [sentimentTrend, setSentimentTrend] = useState<SentimentTrendItem[]>([]);
  const [programAreas, setProgramAreas] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const withWorker = useCallback(
    (filters: FilterDraft): InsightQueryParams => ({
      ...filters,
      ...(workerId !== undefined ? { worker_id: workerId } : {}),
    }),
    [workerId],
  );

  const loadFilterOptions = useCallback(async () => {
    const res = await listManagerVisits({
      page: 1,
      page_size: 100,
      ...(workerId !== undefined ? { worker_id: workerId } : {}),
    });
    const areas = [...new Set(res.items.map((v) => v.program_area))].sort();
    const locs = [...new Set(res.items.map((v) => v.location))].sort();
    setProgramAreas(areas);
    setLocations(locs);
  }, [workerId]);

  const loadDashboard = useCallback(
    async (filters: FilterDraft) => {
      setLoading(true);
      setError("");
      const params = withWorker(filters);
      try {
        const [summaryRes, recurringRes, regionRes, trendRes] = await Promise.all([
          getInsightSummary(params),
          getRecurringBlockers(params),
          getBlockerInsights({ ...params, group_by: "location" }),
          getSentimentTrend({ ...params, interval: "week" }),
        ]);
        setSummary(summaryRes);
        setRecurringBlockers(recurringRes.items);
        setBlockersByRegion(regionRes.items);
        setSentimentTrend(trendRes.items);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    },
    [withWorker],
  );

  useEffect(() => {
    loadFilterOptions().catch(() => {
      /* dropdowns stay empty */
    });
  }, [loadFilterOptions]);

  useEffect(() => {
    loadDashboard(appliedFilters);
  }, [appliedFilters, loadDashboard]);

  return {
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
  };
}
