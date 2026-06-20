import type { ReactNode } from "react";
import "./Card.css";

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function Card({ title, children, className = "" }: CardProps) {
  return (
    <section className={`card animate-in ${className}`}>
      {title ? <h3 className="card__title">{title}</h3> : null}
      <div className="card__body">{children}</div>
    </section>
  );
}
