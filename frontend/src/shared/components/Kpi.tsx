/**
 * KPI card — small labeled metric tile used across admin pages.
 *
 * Extracted from `AdminLiveGamePage` + `Dashboard` (both had their own
 * inline copies). The two had slightly different visual emphasis on
 * the value font-size, so we expose `compact` to opt-in to the smaller
 * 1.5rem variant the spectator panel uses.
 */

import React from "react";

interface KpiProps {
  label: string;
  value: string | number;
  sub?: string;
  /** Smaller value font (1.5rem) — for dense dashboards. Default false → uses the
   *  CSS-defined `.kpi-value` size. */
  compact?: boolean;
  /** When true, render `value` verbatim — no thousand separators. Use
   *  for IDs (Telegram user_id, group_id, charge_id) where digit grouping
   *  is wrong; leave off for amounts (diamonds, dollars, elo) where the
   *  locale formatter helps readability. */
  raw?: boolean;
}

export function Kpi({
  label,
  value,
  sub,
  compact = false,
  raw = false,
}: KpiProps): React.ReactElement {
  const formatted =
    raw || typeof value !== "number" ? String(value) : value.toLocaleString();
  return (
    <div className="admin-card">
      <div className="kpi-label">{label}</div>
      <div
        className="kpi-value"
        style={compact ? { fontSize: "1.5rem" } : undefined}
      >
        {formatted}
      </div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}
