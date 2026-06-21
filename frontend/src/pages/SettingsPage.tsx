import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { useAuth } from "../context/AuthContext";
import { WorkerLayout } from "../layouts/WorkerLayout";
import "./SettingsPage.css";

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <WorkerLayout title="Settings">
      <div className="settings animate-in">
        <Card title="Account">
          <dl className="settings__dl">
            <div>
              <dt>Name</dt>
              <dd>{user?.name}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user?.email}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>Field worker</dd>
            </div>
          </dl>
        </Card>
        <Card title="About">
          <p className="settings__about">
            Field Intelligence is built by{" "}
            <a href="https://www.thenudge.org/" target="_blank" rel="noreferrer">
              The/Nudge Institute
            </a>{" "}
            to capture structured field visit intelligence for livelihood programs.
          </p>
        </Card>
        <Button variant="danger" fullWidth onClick={handleLogout}>
          Sign out
        </Button>
      </div>
    </WorkerLayout>
  );
}
