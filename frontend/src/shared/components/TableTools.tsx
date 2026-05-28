/**
 * Reusable table tooling: sortable headers + pagination.
 *
 * `SortableHeader` is a clickable `<th>` content wrapper that flips the
 * sort direction on click and renders a ▲ / ▼ indicator. State is owned
 * by the caller — pass `{by, dir}` and `onChange` for the new sort.
 *
 * `Pagination` is a self-contained prev / page-numbers / next control.
 * It renders nothing when there's only one page (avoids visual noise on
 * tiny datasets).
 *
 * `useTableState` is a tiny hook that bundles `{search, page, sort}` so
 * pages don't have to wire up four useState calls each.
 */
import { type ReactNode, useState, useCallback } from "react";

export type SortDir = "asc" | "desc";
export interface SortState {
  by: string;
  dir: SortDir;
}

interface SortableHeaderProps {
  field: string;
  sort: SortState | null;
  onChange: (next: SortState) => void;
  children: ReactNode;
  align?: "left" | "right" | "center";
  /** Default direction when the field is first clicked. Defaults to "desc"
   *  (most useful for numeric columns where you want the biggest first). */
  initialDir?: SortDir;
}

export function SortableHeader({
  field,
  sort,
  onChange,
  children,
  align = "left",
  initialDir = "desc",
}: SortableHeaderProps) {
  const isActive = sort?.by === field;
  const arrow = isActive ? (sort?.dir === "asc" ? "▲" : "▼") : "";
  const onClick = () => {
    if (!isActive) onChange({ by: field, dir: initialDir });
    else onChange({ by: field, dir: sort?.dir === "asc" ? "desc" : "asc" });
  };
  return (
    <th
      onClick={onClick}
      style={{
        cursor: "pointer",
        textAlign: align,
        userSelect: "none",
      }}
      title="Click to sort"
    >
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 4,
          color: isActive ? "var(--accent, #4ade80)" : undefined,
        }}
      >
        {children}
        <span aria-hidden style={{ opacity: 0.7, fontSize: "0.7rem", minWidth: 10 }}>
          {arrow}
        </span>
      </span>
    </th>
  );
}

interface PaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
  /** Total item count — when provided, rendered as "X of N" alongside the controls. */
  total?: number;
  pageSize?: number;
}

export function Pagination({
  page,
  totalPages,
  onChange,
  total,
  pageSize,
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const goto = (p: number) => onChange(Math.max(1, Math.min(totalPages, p)));

  // Compact page-number window: first, last, and the 2 neighbors of current.
  const pages: (number | "…")[] = [];
  const push = (p: number) => {
    if (pages[pages.length - 1] !== p) pages.push(p);
  };
  push(1);
  if (page > 3) pages.push("…");
  for (let p = Math.max(2, page - 1); p <= Math.min(totalPages - 1, page + 1); p++) push(p);
  if (page < totalPages - 2) pages.push("…");
  if (totalPages > 1) push(totalPages);

  const rangeText =
    total != null && pageSize
      ? `${Math.min(total, (page - 1) * pageSize + 1)}–${Math.min(total, page * pageSize)} / ${total}`
      : null;

  return (
    <div
      style={{
        marginTop: "1rem",
        display: "flex",
        gap: "0.4rem",
        alignItems: "center",
        flexWrap: "wrap",
      }}
    >
      <button className="admin-btn" disabled={page <= 1} onClick={() => goto(page - 1)}>
        ←
      </button>
      {pages.map((p, idx) =>
        p === "…" ? (
          <span key={`gap-${idx}`} style={{ color: "var(--muted)", padding: "0 4px" }}>
            …
          </span>
        ) : (
          <button
            key={p}
            className="admin-btn"
            onClick={() => goto(p)}
            style={{
              fontWeight: p === page ? 600 : 400,
              background:
                p === page ? "var(--accent, #4ade80)" : undefined,
              color: p === page ? "#000" : undefined,
              minWidth: 32,
            }}
          >
            {p}
          </button>
        ),
      )}
      <button
        className="admin-btn"
        disabled={page >= totalPages}
        onClick={() => goto(page + 1)}
      >
        →
      </button>
      {rangeText && (
        <span style={{ color: "var(--muted)", marginLeft: 8, fontSize: "0.85rem" }}>
          {rangeText}
        </span>
      )}
    </div>
  );
}

/** Wire `{search, page, sort}` into a single state bundle. `setSearch`
 *  resets to page 1 so the new filter applies from the beginning. */
export function useTableState(opts?: {
  initialSort?: SortState | null;
  initialPage?: number;
}) {
  const [search, _setSearch] = useState("");
  const [page, setPage] = useState(opts?.initialPage ?? 1);
  const [sort, setSortRaw] = useState<SortState | null>(opts?.initialSort ?? null);

  const setSearch = useCallback((q: string) => {
    _setSearch(q);
    setPage(1);
  }, []);

  const setSort = useCallback((next: SortState) => {
    setSortRaw(next);
    setPage(1);
  }, []);

  return { search, setSearch, page, setPage, sort, setSort };
}
