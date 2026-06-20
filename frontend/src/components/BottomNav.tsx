import { NavLink } from "react-router-dom";
import "./BottomNav.css";

const tabs = [
  { to: "/app/log", label: "Log", icon: "✎" },
  { to: "/app/visits", label: "Visits", icon: "☰" },
  { to: "/app/gallery", label: "Photos", icon: "▦" },
  { to: "/app/recordings", label: "Audio", icon: "♫" },
  { to: "/app/settings", label: "Settings", icon: "⚙" },
];

export function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Main navigation">
      {tabs.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          end={tab.to === "/app/log"}
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
