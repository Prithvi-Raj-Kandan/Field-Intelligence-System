import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import "./ManagerLayout.css";

interface ManagerLayoutProps {
  children: ReactNode;
}

const navItems = [
  { to: "/manager", label: "Dashboard", end: true },
  { to: "/manager/visits", label: "Visits", end: false },
  { to: "/manager/workers", label: "Workers", end: false },
  { to: "/manager/profile", label: "Profile", end: false },
];

export function ManagerLayout({ children }: ManagerLayoutProps) {
  return (
    <div className="manager-layout">
      <header className="manager-layout__header">
        <div className="manager-layout__brand">
          <p className="manager-layout__org">The/Nudge Institute</p>
          <h1 className="manager-layout__title">Field Intelligence</h1>
        </div>
        <nav className="manager-layout__nav">
          <div className="manager-layout__tabs">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `manager-layout__tab${isActive ? " manager-layout__tab--active" : ""}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>
      </header>
      <main className="manager-layout__main">{children}</main>
    </div>
  );
}
