import type {
  BlockerInsightsResponse,
  InsightQueryParams,
  InsightSummary,
  RecurringBlockersResponse,
  SentimentTrendResponse,
} from "../types/api";
import { apiFetch } from "./client";

function toQueryParams(params: InsightQueryParams & { group_by?: string; interval?: string }): Record<string, string | undefined> {
  const query: Record<string, string | undefined> = {};
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      query[key] = String(value);
    }
  }
  return query;
}

function toQuery(params: Record<string, string | undefined>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) sp.set(key, value);
  }
  const q = sp.toString();
  return q ? `?${q}` : "";
}

export function getInsightSummary(params: InsightQueryParams = {}): Promise<InsightSummary> {
  return apiFetch<InsightSummary>(`/insights/summary${toQuery(toQueryParams(params))}`);
}

export function getBlockerInsights(
  params: InsightQueryParams & { group_by?: "location" | "program_area" | "text" } = {},
): Promise<BlockerInsightsResponse> {
  const { group_by, ...rest } = params;
  return apiFetch<BlockerInsightsResponse>(
    `/insights/blockers${toQuery(toQueryParams({ ...rest, group_by }))}`,
  );
}

export function getRecurringBlockers(params: InsightQueryParams = {}): Promise<RecurringBlockersResponse> {
  return apiFetch<RecurringBlockersResponse>(
    `/insights/recurring-blockers${toQuery(toQueryParams(params))}`,
  );
}

export function getSentimentTrend(
  params: InsightQueryParams & { interval?: "day" | "week" } = {},
): Promise<SentimentTrendResponse> {
  const { interval, ...rest } = params;
  return apiFetch<SentimentTrendResponse>(
    `/insights/sentiment-trend${toQuery(toQueryParams({ ...rest, interval }))}`,
  );
}
