import { useEffect, useRef, useState } from "react";
import type { Sentiment } from "../types/api";
import "./SentimentBadge.css";

const labels: Record<Sentiment, string> = {
  positive: "Positive",
  neutral: "Neutral",
  negative: "Negative",
};

const options: Sentiment[] = ["positive", "neutral", "negative"];

interface SentimentBadgeProps {
  sentiment: Sentiment;
  onChange?: (s: Sentiment) => void;
}

export function SentimentBadge({ sentiment, onChange }: SentimentBadgeProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  if (!onChange) {
    return <span className={`sentiment-badge sentiment-badge--${sentiment}`}>{labels[sentiment]}</span>;
  }

  return (
    <div className="sentiment-select" ref={rootRef}>
      <button
        type="button"
        className={`sentiment-badge sentiment-badge--${sentiment} sentiment-select__trigger`}
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Community sentiment"
      >
        {labels[sentiment]}
        <span className="sentiment-select__chevron" aria-hidden>
          ▾
        </span>
      </button>
      {open ? (
        <ul className="sentiment-select__menu" role="listbox">
          {options.map((option) => (
            <li key={option} role="option" aria-selected={option === sentiment}>
              <button
                type="button"
                className={`sentiment-select__option ${option === sentiment ? "sentiment-select__option--active" : ""}`}
                onClick={() => {
                  onChange(option);
                  setOpen(false);
                }}
              >
                <span className={`sentiment-select__dot sentiment-select__dot--${option}`} aria-hidden />
                {labels[option]}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
