import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { useAuth } from "../context/AuthContext";
import { ManagerLayout } from "../layouts/ManagerLayout";
import "./ManagerProfilePage.css";

export function ManagerProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <ManagerLayout>
      <div className="manager-profile">
        <Card title="Account">
          <dl className="manager-profile__dl">
            <div>
              <dt>Email</dt>
              <dd>{user?.email}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>Manager</dd>
            </div>
          </dl>
        </Card>
        <Card title="About">
          <p className="manager-profile__about">
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
    </ManagerLayout>
  );
}
