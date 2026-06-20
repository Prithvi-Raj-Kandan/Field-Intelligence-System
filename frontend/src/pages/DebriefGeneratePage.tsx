import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { generateDebrief } from "../api/visits";
import { ApiError } from "../api/client";
import { Button } from "../components/Button";
import { useVisitFlow } from "../context/VisitFlowContext";
import { WorkerLayout } from "../layouts/WorkerLayout";
import "./DebriefReviewPage.css";

export function DebriefGeneratePage() {
  const navigate = useNavigate();
  const { sessionId, rawNotes, form, setDebrief, debrief } = useVisitFlow();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId || !form) {
      navigate("/app/log", { replace: true });
      return;
    }
    if (debrief) {
      navigate("/app/log/debrief", { replace: true });
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const res = await generateDebrief(
          sessionId,
          rawNotes,
          form.field_photos,
          form.voice_memos,
        );
        if (!cancelled) {
          setDebrief(res.debrief);
          navigate("/app/log/debrief", { replace: true });
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Debrief generation failed");
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [sessionId, rawNotes, form, debrief, setDebrief, navigate]);

  return (
    <WorkerLayout title="Generating debrief" hideNav>
      <div className="debrief-loading animate-in">
        {loading && !error ? (
          <>
            <div className="debrief-loading__spinner" aria-hidden />
            <p>Analyzing your visit notes and context media…</p>
            <p className="debrief-loading__sub">This may take 10–20 seconds</p>
          </>
        ) : null}
        {error ? (
          <>
            <p className="debrief-loading__error">{error}</p>
            <Button onClick={() => navigate("/app/log")}>Start over</Button>
          </>
        ) : null}
      </div>
    </WorkerLayout>
  );
}
