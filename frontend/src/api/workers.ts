import type { WorkerListResponse } from "../types/api";
import { apiFetch } from "./client";

export function listWorkers(): Promise<WorkerListResponse> {
  return apiFetch<WorkerListResponse>("/workers");
}
