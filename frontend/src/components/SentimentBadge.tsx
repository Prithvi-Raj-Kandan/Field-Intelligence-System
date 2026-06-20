import type { Sentiment } from "../types/api";
import "./SentimentBadge.css";

const labels: Record<Sentiment, string> = {
  positive: "Positive",
  neutral: "Neutral",
  negative: "Negative",
};

interface SentimentBadgeProps {
  sentiment: Sentiment;
  onChange?: (s: Sentiment) => void;
}

export function SentimentBadge({ sentiment, onChange }: SentimentBadgeProps) {
  if (onChange) {
    return (
      <select
        className={`sentiment-badge sentiment-badge--${sentiment} sentiment-badge--select`}
        value={sentiment}
        onChange={(e) => onChange(e.target.value as Sentiment)}
        aria-label="Community sentiment"
      >
        <option value="positive">Positive</option>
        <option value="neutral">Neutral</option>
        <option value="negative">Negative</option>
      </select>
    );
  }
  return <span className={`sentiment-badge sentiment-badge--${sentiment}`}>{labels[sentiment]}</span>;
}
