import { Link } from "react-router-dom";
import { Button } from "../components/Button";
import "./LandingPage.css";

export function LandingPage() {
  return (
    <div className="landing">
      <header className="landing__hero animate-in">
        <div className="landing__hero-inner">
          <p className="landing__eyebrow">The/Nudge Institute</p>
          <h1 className="landing__title">
            Field Intelligence Tool
            <span className="landing__subtitle">Track every field visit</span>
          </h1>
          <div className="landing__actions">
            <Link to="/signup">
              <Button size="lg">Get started</Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary" size="lg">
                Sign in
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <div className="landing__content">
        <section className="landing__intro container animate-in">
          <p className="landing__desc">
            Capture field visits, transcribe notes, and produce structured debriefs — so managers can
            see patterns across programs without reading every report.
          </p>
        </section>

        <section className="landing__stats container animate-in">
        <div className="landing__stat">
          <strong>Structured</strong>
          <span>Visit metadata + free-form notes</span>
        </div>
        <div className="landing__stat">
          <strong>AI-powered</strong>
          <span>Transcription &amp; debrief summaries</span>
        </div>
        <div className="landing__stat">
          <strong>Actionable</strong>
          <span>Findings, blockers &amp; follow-ups</span>
        </div>
        </section>
      </div>

      <footer className="landing__footer">
        <p>
          An extension of{" "}
          <a href="https://www.thenudge.org/" target="_blank" rel="noreferrer">
            The/Nudge Institute
          </a>
        </p>
      </footer>
    </div>
  );
}
