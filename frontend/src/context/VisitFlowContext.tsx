import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { DebriefResult, VisitFlowState, VisitFormData } from "../types/api";

const SESSION_STORAGE_KEY = "field_intel_visit_session_id";

const emptyForm = (): VisitFormData => ({
  location: "",
  visit_date: new Date().toISOString().slice(0, 10),
  program_area: "",
  stakeholders: "",
  raw_notes: "",
  note_images: [],
  field_photos: [],
  voice_memos: [],
});

interface VisitFlowContextValue extends VisitFlowState {
  setSessionId: (id: string) => void;
  setRawNotes: (notes: string) => void;
  setNeedsReview: (v: boolean) => void;
  setDebrief: (d: DebriefResult) => void;
  setForm: (form: VisitFormData) => void;
  resetFlow: () => void;
}

const VisitFlowContext = createContext<VisitFlowContextValue | null>(null);

export function VisitFlowProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionIdState] = useState<string | null>(() =>
    sessionStorage.getItem(SESSION_STORAGE_KEY),
  );

  const setSessionId = (id: string) => {
    sessionStorage.setItem(SESSION_STORAGE_KEY, id);
    setSessionIdState(id);
  };
  const [rawNotes, setRawNotes] = useState("");
  const [needsReview, setNeedsReview] = useState(false);
  const [debrief, setDebrief] = useState<DebriefResult | null>(null);
  const [form, setForm] = useState<VisitFormData | null>(null);

  const resetFlow = () => {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    setSessionIdState(null);
    setRawNotes("");
    setNeedsReview(false);
    setDebrief(null);
    setForm(null);
  };

  const value = useMemo(
    () => ({
      sessionId,
      rawNotes,
      needsReview,
      debrief,
      form,
      setSessionId,
      setRawNotes,
      setNeedsReview,
      setDebrief,
      setForm,
      resetFlow,
    }),
    [sessionId, rawNotes, needsReview, debrief, form],
  );

  return <VisitFlowContext.Provider value={value}>{children}</VisitFlowContext.Provider>;
}

export function useVisitFlow() {
  const ctx = useContext(VisitFlowContext);
  if (!ctx) throw new Error("useVisitFlow must be used within VisitFlowProvider");
  return ctx;
}

export { emptyForm };
