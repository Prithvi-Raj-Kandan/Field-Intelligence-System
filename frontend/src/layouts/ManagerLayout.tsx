import type { ReactNode } from "react";
import { Button } from "../components/Button";
import { useAuth } from "../context/AuthContext";
import "./ManagerLayout.css";

interface ManagerLayoutProps {
  children: ReactNode;
}

export function ManagerLayout({ children }: ManagerLayoutProps) {
  const { logout, user } = useAuth();

  return (
    <div className="manager-layout">
      <header className="manager-layout__header">
        <div className="manager-layout__brand">
          <p className="manager-layout__org">The/Nudge Institute</p>
          <h1 className="manager-layout__title">Field Intelligence</h1>
        </div>
        <nav className="manager-layout__nav">
          <span className="manager-layout__nav-active">Dashboard</span>
          <span className="manager-layout__user">{user?.email}</span>
          <Button variant="ghost" onClick={logout}>
            Sign out
          </Button>
        </nav>
      </header>
      <main className="manager-layout__main">{children}</main>
    </div>
  );
}
