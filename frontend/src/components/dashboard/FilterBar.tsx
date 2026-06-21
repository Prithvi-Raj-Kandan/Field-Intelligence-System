import { Button } from "../Button";
import { SelectField, TextField } from "../Input";
import type { InsightQueryParams } from "../../types/api";
import "./FilterBar.css";

export interface FilterDraft extends InsightQueryParams {}

interface FilterBarProps {
  draft: FilterDraft;
  onChange: (next: FilterDraft) => void;
  onApply: () => void;
  onClear: () => void;
  programAreas: string[];
  locations: string[];
}

export function FilterBar({
  draft,
  onChange,
  onApply,
  onClear,
  programAreas,
  locations,
}: FilterBarProps) {
  return (
    <section className="filter-bar">
      <h2 className="filter-bar__heading">Filters</h2>
      <div className="filter-bar__fields">
        <TextField
          label="From date"
          type="date"
          value={draft.date_from ?? ""}
          onChange={(e) => onChange({ ...draft, date_from: e.target.value || undefined })}
        />
        <TextField
          label="To date"
          type="date"
          value={draft.date_to ?? ""}
          onChange={(e) => onChange({ ...draft, date_to: e.target.value || undefined })}
        />
        <SelectField
          label="Program area"
          value={draft.program_area ?? ""}
          onChange={(e) =>
            onChange({ ...draft, program_area: e.target.value || undefined })
          }
        >
          <option value="">All programs</option>
          {programAreas.map((area) => (
            <option key={area} value={area}>
              {area}
            </option>
          ))}
        </SelectField>
        <SelectField
          label="Location"
          value={draft.location ?? ""}
          onChange={(e) => onChange({ ...draft, location: e.target.value || undefined })}
        >
          <option value="">All locations</option>
          {locations.map((loc) => (
            <option key={loc} value={loc}>
              {loc}
            </option>
          ))}
        </SelectField>
      </div>
      <div className="filter-bar__actions">
        <Button onClick={onApply}>Apply filters</Button>
        <Button variant="secondary" onClick={onClear}>
          Clear
        </Button>
      </div>
    </section>
  );
}
