import type { InsightQueryParams, ManagerVisitDetail, PaginatedVisitsResponse } from "../types/api";
import { apiFetch, downloadCsv } from "./client";

function toQuery(
  params: InsightQueryParams & { page?: number; page_size?: number },
): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") sp.set(key, String(value));
  }
  const q = sp.toString();
  return q ? `?${q}` : "";
}

export function listManagerVisits(
  params: InsightQueryParams & { page?: number; page_size?: number } = {},
): Promise<PaginatedVisitsResponse> {
  return apiFetch<PaginatedVisitsResponse>(`/visits${toQuery(params)}`);
}

export function getManagerVisit(id: number): Promise<ManagerVisitDetail> {
  return apiFetch<ManagerVisitDetail>(`/visits/${id}`);
}

export function exportVisitsCsv(params: InsightQueryParams = {}): Promise<void> {
  const query = toQuery(params);
  return downloadCsv(`/visits/export.csv${query}`, "visits-export.csv");
}
