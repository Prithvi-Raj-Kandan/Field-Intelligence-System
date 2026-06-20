import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BlockerInsightItem } from "../../types/api";
import "./Charts.css";

interface BlockersByRegionChartProps {
  items: BlockerInsightItem[];
  loading: boolean;
}

export function BlockersByRegionChart({ items, loading }: BlockersByRegionChartProps) {
  const data = items.reduce<
    Record<string, { region: string; count: number }>
  >((acc, item) => {
    const key = item.group;
    if (!acc[key]) acc[key] = { region: key, count: 0 };
    acc[key].count += item.count;
    return acc;
  }, {});

  const chartData = Object.values(data).sort((a, b) => b.count - a.count);

  if (loading) {
    return <p className="chart-panel__muted">Loading chart…</p>;
  }

  if (chartData.length === 0) {
    return <p className="chart-panel__muted">No blocker data for chart.</p>;
  }

  return (
    <div className="chart-panel">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis
            dataKey="region"
            tick={{ fontSize: 11 }}
            angle={-25}
            textAnchor="end"
            interval={0}
            height={60}
          />
          <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey="count" fill="var(--color-secondary)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
