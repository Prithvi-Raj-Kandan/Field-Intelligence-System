import "./Charts.css";
import { BlockersByRegionChart } from "./BlockersByRegionChart";
import { MetricCards } from "./MetricCards";
import { RecurringBlockersTable } from "./RecurringBlockersTable";
import { SentimentTrendChart } from "./SentimentTrendChart";
import type {
  BlockerInsightItem,
  InsightSummary,
  RecurringBlockerItem,
  SentimentTrendItem,
} from "../../types/api";

interface ManagerDashboardPanelsProps {
  summary: InsightSummary | null;
  recurringBlockers: RecurringBlockerItem[];
  blockersByRegion: BlockerInsightItem[];
  sentimentTrend: SentimentTrendItem[];
  loading: boolean;
}

export function ManagerDashboardPanels({
  summary,
  recurringBlockers,
  blockersByRegion,
  sentimentTrend,
  loading,
}: ManagerDashboardPanelsProps) {
  const hasData = (summary?.total_visits ?? 0) > 0;

  return (
    <>
      <MetricCards summary={summary} loading={loading} />

      {hasData || loading ? (
        <>
          <div className="dashboard-charts">
            <section className="dashboard-chart-card">
              <h3>Blockers by region</h3>
              <BlockersByRegionChart items={blockersByRegion} loading={loading} />
            </section>
            <section className="dashboard-chart-card">
              <h3>Sentiment over time</h3>
              <SentimentTrendChart items={sentimentTrend} loading={loading} />
            </section>
          </div>

          <section className="manager-dashboard__panel">
            <h3>Recurring blockers</h3>
            <p className="manager-dashboard__panel-desc">
              Blockers linked across regions — same issue appearing in multiple locations.
            </p>
            <RecurringBlockersTable items={recurringBlockers} loading={loading} />
          </section>
        </>
      ) : null}
    </>
  );
}
