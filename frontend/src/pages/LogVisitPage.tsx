import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { preprocessVisit } from "../api/visits";
import { ApiError } from "../api/client";
import { Button } from "../components/Button";
import { FileUpload } from "../components/FileUpload";
import { SelectField, TextAreaField, TextField } from "../components/Input";
import { emptyForm, useVisitFlow } from "../context/VisitFlowContext";
import { WorkerLayout } from "../layouts/WorkerLayout";
import type { VisitFormData } from "../types/api";
import "./LogVisitPage.css";

const PROGRAM_AREAS = [
  "Water Access",
  "Rural Housing",
  "Agriculture",
  "Livelihoods",
  "Education",
  "Health",
  "Other",
];

export function LogVisitPage() {
  const navigate = useNavigate();
  const { setSessionId, setRawNotes, setNeedsReview, setForm: saveFormToFlow, resetFlow } = useVisitFlow();
  const [form, setForm] = useState<VisitFormData>(emptyForm());
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = <K extends keyof VisitFormData>(key: K, value: VisitFormData[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const validate = (): string | null => {
    if (!form.location.trim()) return "Location is required";
    if (!form.visit_date) return "Visit date is required";
    if (!form.program_area) return "Program area is required";
    if (!form.raw_notes.trim() && form.note_images.length === 0) {
      return "Add typed notes or a photo of your notes";
    }
    return null;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError("");
    setLoading(true);
    resetFlow();
    try {
      const res = await preprocessVisit(form);
      setSessionId(res.session_id);
      setRawNotes(res.raw_notes);
      setNeedsReview(res.needs_review);
      saveFormToFlow(form);
      if (res.needs_review) {
        navigate("/app/log/review");
      } else {
        navigate("/app/log/debrief/generate");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to process visit");
    } finally {
      setLoading(false);
    }
  };

  return (
    <WorkerLayout title="Log a visit">
      <form className="log-visit animate-in" onSubmit={handleSubmit}>
        <p className="log-visit__intro">
          Record structured visit data and free-form notes. Context photos and voice memos are added
          at the debrief step.
        </p>

        <TextField
          label="Location"
          required
          placeholder="e.g. Jayanagar, Ward 12"
          value={form.location}
          onChange={(e) => update("location", e.target.value)}
        />
        <TextField
          label="Visit date"
          type="date"
          required
          value={form.visit_date}
          onChange={(e) => update("visit_date", e.target.value)}
        />
        <SelectField
          label="Program area"
          required
          value={form.program_area}
          onChange={(e) => update("program_area", e.target.value)}
        >
          <option value="">Select program</option>
          {PROGRAM_AREAS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </SelectField>
        <TextField
          label="Stakeholders met"
          placeholder="e.g. BDA, village council"
          value={form.stakeholders}
          onChange={(e) => update("stakeholders", e.target.value)}
        />

        <TextAreaField
          label="Free-form notes (typed)"
          placeholder="Observations, conversations, key points..."
          value={form.raw_notes}
          onChange={(e) => update("raw_notes", e.target.value)}
          hint="Or upload a photo of handwritten notes below"
        />

        <FileUpload
          label="Note photos"
          hint="Handwritten or printed notes — will be transcribed"
          accept="image/*"
          multiple
          files={form.note_images}
          onChange={(files) => update("note_images", files)}
        />

        <FileUpload
          label="Field context photos"
          hint="Location, people, proof of work — sent to AI at debrief (not transcribed)"
          accept="image/*"
          multiple
          files={form.field_photos}
          onChange={(files) => update("field_photos", files)}
        />

        <FileUpload
          label="Voice memos"
          hint="Recorded on site — interpreted directly at debrief"
          accept="audio/*"
          multiple
          files={form.voice_memos}
          onChange={(files) => update("voice_memos", files)}
          previews={false}
        />

        {error ? <p className="log-visit__error">{error}</p> : null}

        <div className="log-visit__footer">
          <Button type="submit" fullWidth size="lg" loading={loading}>
            Continue
          </Button>
        </div>
      </form>
    </WorkerLayout>
  );
}
