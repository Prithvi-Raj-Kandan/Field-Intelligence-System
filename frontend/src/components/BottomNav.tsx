import { NavLink } from "react-router-dom";
import "./BottomNav.css";

const tabs = [
  { to: "/app/log", label: "Log Visit", icon: "✎" },
  { to: "/app/visits", label: "Visits", icon: "☰" },
  { to: "/app/gallery", label: "Gallery", icon: "▦" },
  { to: "/app/settings", label: "Settings", icon: "⚙" },
];

export function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Main navigation">
      {tabs.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          className={({ isActive }) => `bottom-nav__item ${isActive ? "bottom-nav__item--active" : ""}`}
        >
          <span className="bottom-nav__icon" aria-hidden>
            {tab.icon}
          </span>
          <span className="bottom-nav__label">{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
