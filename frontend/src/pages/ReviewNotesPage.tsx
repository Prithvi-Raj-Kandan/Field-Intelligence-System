import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { TextAreaField } from "../components/Input";
import { useVisitFlow } from "../context/VisitFlowContext";
import { WorkerLayout } from "../layouts/WorkerLayout";
import "./ReviewNotesPage.css";

export function ReviewNotesPage() {
  const navigate = useNavigate();
  const { sessionId, rawNotes, setRawNotes, setFlowPhase } = useVisitFlow();
  const [notes, setNotes] = useState(rawNotes);
  const [error, setError] = useState("");

  if (!sessionId) {
    navigate("/app/log", { replace: true });
    return null;
  }

  const handleContinue = () => {
    if (!notes.trim()) {
      setError("Notes cannot be empty");
      return;
    }
    setRawNotes(notes);
    setFlowPhase("generating");
    navigate("/app/log/debrief/generate");
  };

  return (
    <WorkerLayout title="Review notes" hideNav>
      <div className="review-notes animate-in">
        <p className="review-notes__hint">
          Review and correct the transcription from your note photos before generating the debrief.
        </p>
        <TextAreaField
          label="Transcribed notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={14}
        />
        {error ? <p className="review-notes__error">{error}</p> : null}
        <div className="review-notes__actions">
          <Button variant="secondary" onClick={() => navigate("/app/log")}>
            Back
          </Button>
          <Button onClick={handleContinue}>Continue to debrief</Button>
        </div>
      </div>
    </WorkerLayout>
  );
}
