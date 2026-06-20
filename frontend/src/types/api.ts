export type UserRole = "field_worker" | "manager";

export interface User {
  id: number;
  email: string;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type Sentiment = "positive" | "neutral" | "negative";

export interface DebriefItem {
  type: "finding" | "blocker" | "follow_up";
  text: string;
  source: "text" | "photo" | "voice";
}

export interface DebriefResult {
  sentiment: Sentiment;
  findings: DebriefItem[];
  blockers: DebriefItem[];
  follow_ups: DebriefItem[];
}

export interface PreprocessResponse {
  session_id: string;
  raw_notes: string;
  needs_review: boolean;
}

export interface DebriefResponse {
  session_id: string;
  debrief: DebriefResult;
}

export interface VisitSummary {
  id: number;
  location: string;
  visit_date: string;
  program_area: string;
  sentiment: Sentiment | null;
  created_at: string;
}

export interface VisitDetail extends VisitSummary {
  stakeholders: string;
  raw_notes: string;
  note_image_paths: string[];
  field_photo_paths: string[];
  voice_memo_paths: string[];
  findings: DebriefItem[];
}

export interface GalleryMediaItem {
  visit_id: number;
  path: string;
  media_type: "note" | "field";
  location: string;
  visit_date: string;
}

export interface VisitFormData {
  location: string;
  visit_date: string;
  program_area: string;
  stakeholders: string;
  raw_notes: string;
  note_images: File[];
  field_photos: File[];
  voice_memos: File[];
}

export interface VisitFlowState {
  sessionId: string | null;
  rawNotes: string;
  needsReview: boolean;
  debrief: DebriefResult | null;
  form: VisitFormData | null;
}

export interface VisitSessionStatus {
  session_id: string;
  status: string;
  raw_notes: string;
  debrief: DebriefResult | null;
}
