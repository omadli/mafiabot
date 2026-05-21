/**
 * Shared WebApp UI primitives — small, dependency-free.
 *
 * Kept in one file because each piece is ~10 LOC and they always travel
 * together: a page that needs `<Pagination/>` almost always wants
 * `<ErrorBanner/>` and `<Skeleton/>` too. Splitting would cost more in
 * imports than it saves in cohesion.
 */

import { useTranslation } from "react-i18next";

export function Skeleton({
  rows = 3,
  height = 56,
}: {
  rows?: number;
  height?: number;
}) {
  return (
    <div className="webapp-skeleton-list" aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="webapp-skeleton-row" style={{ height }} />
      ))}
    </div>
  );
}

export function ErrorBanner({
  message,
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="webapp-error-banner" role="alert">
      <span>{message ?? t("webapp.ux.error_load_failed")}</span>
      {onRetry && (
        <button className="webapp-btn webapp-btn-ghost" onClick={onRetry}>
          {t("webapp.ux.retry")}
        </button>
      )}
    </div>
  );
}

export function Pagination({
  page,
  pageSize,
  total,
  onChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onChange: (p: number) => void;
}) {
  const { t } = useTranslation();
  const lastPage = Math.max(1, Math.ceil(total / pageSize));
  if (lastPage <= 1) return null;
  return (
    <div className="webapp-pagination">
      <button
        className="webapp-btn webapp-btn-ghost"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
      >
        {t("webapp.leaderboard.prev")}
      </button>
      <span className="webapp-pagination-label">
        {t("webapp.leaderboard.page_label", { current: page, total: lastPage })}
      </span>
      <button
        className="webapp-btn webapp-btn-ghost"
        disabled={page >= lastPage}
        onClick={() => onChange(page + 1)}
      >
        {t("webapp.leaderboard.next")}
      </button>
    </div>
  );
}
