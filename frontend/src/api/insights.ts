import type {
  BlockerInsightsResponse,
  InsightQueryParams,
  InsightSummary,
  SentimentTrendResponse,
} from "../types/api";
import { apiFetch } from "./client";

function toQuery(params: Record<string, string | undefined>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) sp.set(key, value);
  }
  const q = sp.toString();
  return q ? `?${q}` : "";
}

export function getInsightSummary(params: InsightQueryParams = {}): Promise<InsightSummary> {
  return apiFetch<InsightSummary>(`/insights/summary${toQuery(params as Record<string, string | undefined>)}`);
}

export function getBlockerInsights(
  params: InsightQueryParams & { group_by?: "location" | "program_area" | "text" } = {},
): Promise<BlockerInsightsResponse> {
  const { group_by, ...rest } = params;
  return apiFetch<BlockerInsightsResponse>(
    `/insights/blockers${toQuery({ ...rest, group_by } as Record<string, string | undefined>)}`,
  );
}

export function getSentimentTrend(
  params: InsightQueryParams & { interval?: "day" | "week" } = {},
): Promise<SentimentTrendResponse> {
  const { interval, ...rest } = params;
  return apiFetch<SentimentTrendResponse>(
    `/insights/sentiment-trend${toQuery({ ...rest, interval } as Record<string, string | undefined>)}`,
  );
}
