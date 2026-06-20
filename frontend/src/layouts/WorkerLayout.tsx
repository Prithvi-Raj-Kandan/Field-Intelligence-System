import type { ReactNode } from "react";
import { BottomNav } from "../components/BottomNav";
import "./WorkerLayout.css";

interface WorkerLayoutProps {
  title: string;
  children: ReactNode;
  hideNav?: boolean;
}

export function WorkerLayout({ title, children, hideNav = false }: WorkerLayoutProps) {
  return (
    <div className={`worker-layout ${hideNav ? "worker-layout--no-nav" : ""}`}>
      <header className="worker-header">
        <div className="container worker-header__inner">
          <p className="worker-header__brand">The/Nudge</p>
          <h1 className="worker-header__title">{title}</h1>
        </div>
      </header>
      <main className="worker-main container">{children}</main>
      {!hideNav ? <BottomNav /> : null}
    </div>
  );
}
