import { useMemo, useState } from "react";
import type { BlockerInsightItem } from "../../types/api";
import "./BlockersTable.css";

type SortKey = "blocker_text" | "group" | "count";

interface BlockersTableProps {
  items: BlockerInsightItem[];
  loading: boolean;
  onRowClick?: (item: BlockerInsightItem) => void;
}

export function BlockersTable({ items, loading, onRowClick }: BlockersTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("count");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = useMemo(() => {
    const list = [...items];
    list.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "number" && typeof bv === "number") {
        return sortAsc ? av - bv : bv - av;
      }
      return sortAsc
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return list;
  }, [items, sortKey, sortAsc]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key !== "count");
    }
  }

  function sortIndicator(key: SortKey) {
    if (sortKey !== key) return "";
    return sortAsc ? " ↑" : " ↓";
  }

  if (loading) {
    return <p className="blockers-table__muted">Loading blockers…</p>;
  }

  if (items.length === 0) {
    return <p className="blockers-table__muted">No blockers match the current filters.</p>;
  }

  return (
    <div className="blockers-table-wrap">
      <table className="blockers-table">
        <thead>
          <tr>
            <th>
              <button type="button" onClick={() => toggleSort("blocker_text")}>
                Blocker{sortIndicator("blocker_text")}
              </button>
            </th>
            <th>
              <button type="button" onClick={() => toggleSort("group")}>
                Region / group{sortIndicator("group")}
              </button>
            </th>
            <th>
              <button type="button" onClick={() => toggleSort("count")}>
                Count{sortIndicator("count")}
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, idx) => (
            <tr
              key={`${row.group}-${row.blocker_text}-${idx}`}
              className={onRowClick ? "blockers-table__row--clickable" : undefined}
              onClick={() => onRowClick?.(row)}
            >
              <td>{row.blocker_text}</td>
              <td>{row.group}</td>
              <td className="blockers-table__count">{row.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
