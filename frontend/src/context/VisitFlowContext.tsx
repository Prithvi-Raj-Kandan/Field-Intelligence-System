import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { DebriefResult, VisitFlowState, VisitFormData } from "../types/api";

const SESSION_STORAGE_KEY = "field_intel_visit_session_id";
const FLOW_PHASE_KEY = "field_intel_flow_phase";

export type FlowPhase = "idle" | "notes_review" | "generating" | "debrief_review" | "completed";

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

function readFlowPhase(): FlowPhase {
  const value = sessionStorage.getItem(FLOW_PHASE_KEY);
  if (
    value === "notes_review" ||
    value === "generating" ||
    value === "debrief_review" ||
    value === "completed"
  ) {
    return value;
  }
  return "idle";
}

interface VisitFlowContextValue extends VisitFlowState {
  flowPhase: FlowPhase;
  setSessionId: (id: string) => void;
  setRawNotes: (notes: string) => void;
  setNeedsReview: (v: boolean) => void;
  setDebrief: (d: DebriefResult) => void;
  setForm: (form: VisitFormData) => void;
  setFlowPhase: (phase: FlowPhase) => void;
  completeFlow: () => void;
  resetFlow: () => void;
}

const VisitFlowContext = createContext<VisitFlowContextValue | null>(null);

export function VisitFlowProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionIdState] = useState<string | null>(() =>
    readFlowPhase() === "completed" ? null : sessionStorage.getItem(SESSION_STORAGE_KEY),
  );
  const [flowPhase, setFlowPhaseState] = useState<FlowPhase>(readFlowPhase);
  const [rawNotes, setRawNotes] = useState("");
  const [needsReview, setNeedsReview] = useState(false);
  const [debrief, setDebrief] = useState<DebriefResult | null>(null);
  const [form, setForm] = useState<VisitFormData | null>(null);

  const setFlowPhase = (phase: FlowPhase) => {
    sessionStorage.setItem(FLOW_PHASE_KEY, phase);
    setFlowPhaseState(phase);
  };

  const setSessionId = (id: string) => {
    sessionStorage.setItem(SESSION_STORAGE_KEY, id);
    setSessionIdState(id);
  };

  const completeFlow = () => {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    sessionStorage.setItem(FLOW_PHASE_KEY, "completed");
    setSessionIdState(null);
    setFlowPhaseState("completed");
    setRawNotes("");
    setNeedsReview(false);
    setDebrief(null);
    setForm(null);
  };

  const resetFlow = () => {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    sessionStorage.setItem(FLOW_PHASE_KEY, "idle");
    setSessionIdState(null);
    setFlowPhaseState("idle");
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
      flowPhase,
      setSessionId,
      setRawNotes,
      setNeedsReview,
      setDebrief,
      setForm,
      setFlowPhase,
      completeFlow,
      resetFlow,
    }),
    [sessionId, rawNotes, needsReview, debrief, form, flowPhase],
  );

  return <VisitFlowContext.Provider value={value}>{children}</VisitFlowContext.Provider>;
}

export function useVisitFlow() {
  const ctx = useContext(VisitFlowContext);
  if (!ctx) throw new Error("useVisitFlow must be used within VisitFlowProvider");
  return ctx;
}

export { emptyForm };
