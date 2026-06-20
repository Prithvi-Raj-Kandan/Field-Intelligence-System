import { Link } from "react-router-dom";
import { Button } from "../components/Button";
import { useAuth } from "../context/AuthContext";
import "./ManagerPage.css";

export function ManagerPage() {
  const { logout } = useAuth();

  return (
    <div className="manager-page">
      <div className="manager-page__card animate-in">
        <p className="manager-page__brand">The/Nudge Institute</p>
        <h1>Manager dashboard</h1>
        <p>
          Pattern analytics, recurring blockers, and sentiment trends are coming in Stage 2 of the
          build. Your account is ready — check back soon.
        </p>
        <div className="manager-page__actions">
          <Link to="/">
            <Button variant="secondary">Back to home</Button>
          </Link>
          <Button variant="ghost" onClick={logout}>
            Sign out
          </Button>
        </div>
      </div>
    </div>
  );
}
