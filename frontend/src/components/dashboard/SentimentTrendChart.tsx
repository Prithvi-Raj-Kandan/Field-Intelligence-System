import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SentimentTrendItem } from "../../types/api";
import "./Charts.css";

interface SentimentTrendChartProps {
  items: SentimentTrendItem[];
  loading: boolean;
}

function formatPeriod(period: string) {
  const d = new Date(period);
  if (Number.isNaN(d.getTime())) return period;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function SentimentTrendChart({ items, loading }: SentimentTrendChartProps) {
  const chartData = items.map((item) => ({
    ...item,
    label: formatPeriod(item.period),
  }));

  if (loading) {
    return <p className="chart-panel__muted">Loading chart…</p>;
  }

  if (chartData.length === 0) {
    return <p className="chart-panel__muted">No sentiment trend data.</p>;
  }

  return (
    <div className="chart-panel">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis dataKey="label" tick={{ fontSize: 12 }} />
          <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="positive" stroke="var(--color-success)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="neutral" stroke="var(--color-neutral)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="negative" stroke="var(--color-danger)" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
