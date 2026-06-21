export type UserRole = "field_worker" | "manager";

export interface User {
  id: number;
  email: string;
  name: string;
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

export interface RecordingMediaItem {
  visit_id: number;
  path: string;
  location: string;
  visit_date: string;
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

export interface InsightQueryParams {
  date_from?: string;
  date_to?: string;
  program_area?: string;
  location?: string;
  worker_id?: number;
}

export interface InsightSummary {
  total_visits: number;
  negative_sentiment_pct: number;
  most_common_blocker: string | null;
  most_common_blocker_count: number;
}

export interface BlockerInsightItem {
  group: string;
  blocker_text: string;
  count: number;
}

export interface BlockerInsightsResponse {
  items: BlockerInsightItem[];
}

export interface RecurringBlockerItem {
  blocker_text: string;
  count: number;
  regions: string[];
}

export interface RecurringBlockersResponse {
  items: RecurringBlockerItem[];
}

export interface SentimentTrendItem {
  period: string;
  positive: number;
  neutral: number;
  negative: number;
}

export interface SentimentTrendResponse {
  items: SentimentTrendItem[];
}

export interface VisitListItem extends VisitSummary {
  blocker_count: number;
  worker_name?: string | null;
  worker_email?: string | null;
}

export interface PaginatedVisitsResponse {
  items: VisitListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface FindingDetail extends DebriefItem {
  id: number;
  category: string | null;
}

export interface ManagerVisitDetail extends VisitSummary {
  stakeholders: string;
  raw_notes: string;
  note_image_paths: string[];
  field_photo_paths: string[];
  voice_memo_paths: string[];
  note_image_urls: string[];
  field_photo_urls: string[];
  voice_memo_urls: string[];
  findings: FindingDetail[];
}

export interface WorkerProfile {
  id: number;
  name: string;
  email: string;
  visit_count: number;
  negative_sentiment_pct: number;
  most_common_blocker: string | null;
  most_common_blocker_count: number;
  last_visit_date: string | null;
}

export interface WorkerListResponse {
  items: WorkerProfile[];
}
