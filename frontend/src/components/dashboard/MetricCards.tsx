import type { InsightSummary } from "../../types/api";
import "./MetricCards.css";

interface MetricCardsProps {
  summary: InsightSummary | null;
  loading: boolean;
}

export function MetricCards({ summary, loading }: MetricCardsProps) {
  if (loading) {
    return (
      <div className="metric-cards">
        {[1, 2, 3].map((n) => (
          <div key={n} className="metric-card metric-card--loading">
            <span className="metric-card__label">Loading…</span>
          </div>
        ))}
      </div>
    );
  }

  if (!summary || summary.total_visits === 0) {
    return (
      <div className="metric-cards metric-cards--empty">
        <p>No visits match the current filters.</p>
      </div>
    );
  }

  return (
    <div className="metric-cards">
      <article className="metric-card">
        <p className="metric-card__label">Total visits</p>
        <p className="metric-card__value">{summary.total_visits}</p>
      </article>
      <article className="metric-card metric-card--warning">
        <p className="metric-card__label">Negative sentiment</p>
        <p className="metric-card__value">{summary.negative_sentiment_pct}%</p>
      </article>
      <article className="metric-card metric-card--accent">
        <p className="metric-card__label">Top blocker</p>
        <p className="metric-card__value metric-card__value--small">
          {summary.most_common_blocker ?? "—"}
        </p>
        {summary.most_common_blocker ? (
          <p className="metric-card__sub">{summary.most_common_blocker_count} mentions</p>
        ) : null}
      </article>
    </div>
  );
}
