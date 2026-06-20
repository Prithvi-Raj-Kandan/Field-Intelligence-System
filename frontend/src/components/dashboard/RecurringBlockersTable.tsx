import { useMemo, useState } from "react";
import type { RecurringBlockerItem } from "../../types/api";
import "./RecurringBlockersTable.css";

type SortKey = "blocker_text" | "count" | "regions";

interface RecurringBlockersTableProps {
  items: RecurringBlockerItem[];
  loading: boolean;
}

export function RecurringBlockersTable({ items, loading }: RecurringBlockersTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("count");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = useMemo(() => {
    const list = [...items];
    list.sort((a, b) => {
      if (sortKey === "count") {
        return sortAsc ? a.count - b.count : b.count - a.count;
      }
      if (sortKey === "regions") {
        const av = a.regions.join(", ");
        const bv = b.regions.join(", ");
        return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sortAsc
        ? a.blocker_text.localeCompare(b.blocker_text)
        : b.blocker_text.localeCompare(a.blocker_text);
    });
    return list;
  }, [items, sortKey, sortAsc]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === "blocker_text");
    }
  }

  function sortIndicator(key: SortKey) {
    if (sortKey !== key) return "";
    return sortAsc ? " ↑" : " ↓";
  }

  if (loading) {
    return <p className="recurring-blockers__muted">Loading blockers…</p>;
  }

  if (items.length === 0) {
    return <p className="recurring-blockers__muted">No blockers match the current filters.</p>;
  }

  return (
    <div className="recurring-blockers-wrap">
      <table className="recurring-blockers">
        <thead>
          <tr>
            <th>
              <button type="button" onClick={() => toggleSort("blocker_text")}>
                Blocker{sortIndicator("blocker_text")}
              </button>
            </th>
            <th>
              <button type="button" onClick={() => toggleSort("count")}>
                Count{sortIndicator("count")}
              </button>
            </th>
            <th>
              <button type="button" onClick={() => toggleSort("regions")}>
                Regions{sortIndicator("regions")}
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={row.blocker_text}>
              <td>{row.blocker_text}</td>
              <td className="recurring-blockers__count">{row.count}</td>
              <td className="recurring-blockers__regions">{row.regions.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
