import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { getVisitSession } from "../api/visits";
import { useVisitFlow, type FlowPhase } from "../context/VisitFlowContext";

const PHASE_HOME: Record<FlowPhase, string> = {
  idle: "/app/log",
  notes_review: "/app/log/review",
  generating: "/app/log/debrief/generate",
  debrief_review: "/app/log/debrief",
  completed: "/app/log",
};

interface VisitFlowGuardProps {
  allowed: FlowPhase[];
  children: ReactNode;
}

export function VisitFlowGuard({ allowed, children }: VisitFlowGuardProps) {
  const navigate = useNavigate();
  const { flowPhase, sessionId } = useVisitFlow();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (flowPhase === "completed") {
        navigate("/app/log", { replace: true });
        return;
      }

      if (!allowed.includes(flowPhase)) {
        navigate(PHASE_HOME[flowPhase], { replace: true });
        return;
      }

      if (sessionId) {
        try {
          const session = await getVisitSession(sessionId);
          if (cancelled) return;
          if (session.status === "saved") {
            navigate("/app/log", { replace: true });
            return;
          }
        } catch {
          if (!cancelled) navigate("/app/log", { replace: true });
          return;
        }
      } else if (flowPhase !== "idle" && !allowed.includes("idle")) {
        navigate("/app/log", { replace: true });
        return;
      }

      if (!cancelled) setReady(true);
    })();

    return () => {
      cancelled = true;
    };
  }, [allowed, flowPhase, sessionId, navigate]);

  if (!ready) {
    return (
      <div className="flow-guard-loading">
        <div className="debrief-loading__spinner" aria-hidden />
      </div>
    );
  }

  return <>{children}</>;
}
