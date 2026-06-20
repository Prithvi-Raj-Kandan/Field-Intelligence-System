import { apiFetch } from "./client";
import type {
  DebriefResponse,
  DebriefResult,
  GalleryMediaItem,
  PreprocessResponse,
  VisitDetail,
  VisitFormData,
  VisitSessionStatus,
  VisitSummary,
} from "../types/api";

export async function preprocessVisit(form: VisitFormData): Promise<PreprocessResponse> {
  const body = new FormData();
  body.append("location", form.location);
  body.append("visit_date", form.visit_date);
  body.append("program_area", form.program_area);
  body.append("stakeholders", form.stakeholders);
  if (form.raw_notes.trim()) body.append("raw_notes", form.raw_notes.trim());
  form.note_images.forEach((f) => body.append("note_images", f));

  return apiFetch<PreprocessResponse>("/visits/preprocess", { method: "POST", body });
}

export async function generateDebrief(
  sessionId: string,
  rawNotes: string | null,
  fieldPhotos: File[],
  voiceMemos: File[],
): Promise<DebriefResponse> {
  const body = new FormData();
  body.append("session_id", sessionId);
  if (rawNotes !== null) body.append("raw_notes", rawNotes);
  fieldPhotos.forEach((f) => body.append("field_photos", f));
  voiceMemos.forEach((f) => body.append("voice_memos", f));

  return apiFetch<DebriefResponse>("/visits/debrief", { method: "POST", body });
}

export async function saveVisit(
  sessionId: string,
  debrief: DebriefResult,
  rawNotes?: string,
): Promise<{ visit_id: number; message: string }> {
  return apiFetch("/visits/save", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      debrief,
      ...(rawNotes ? { raw_notes: rawNotes } : {}),
    }),
  });
}

export async function getVisitSession(sessionId: string): Promise<VisitSessionStatus> {
  return apiFetch<VisitSessionStatus>(`/visits/sessions/${sessionId}`);
}

export async function listMyVisits(): Promise<VisitSummary[]> {
  return apiFetch<VisitSummary[]>("/visits/mine");
}

export async function getVisit(id: number): Promise<VisitDetail> {
  return apiFetch<VisitDetail>(`/visits/mine/${id}`);
}

export async function listGallery(): Promise<GalleryMediaItem[]> {
  return apiFetch<GalleryMediaItem[]>("/visits/mine/gallery");
}
