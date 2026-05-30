/**
 * Audit log feed — paginated, filterable by `action` substring.
 *
 * Combines the strengths of the two previous variants:
 *   - admin/AuditPage  → table layout with payload-JSON + IP columns
 *   - webapp/SaAuditPage → action filter, pagination, refetch interval
 *
 * Lives in modules/sa/pages so both shells (admin sidebar, WebApp SA
 * nav) mount the same component. Auth and URL prefix are decided by
 * `superAdminApi.audit` based on which credential the user actually
 * presented.
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { superAdminApi } from "@shared/api/superAdmin";

import { useSa } from "../context";

const PAGE_SIZE = 50;

function fmtPayload(payload: Record<string, unknown> | null): string {
  if (!payload || Object.keys(payload).length === 0) return "—";
  try {
    return JSON.stringify(payload);
  } catch {
    return "[unserialisable]";
  }
}

function fmtActor(row: {
  actor_admin_id: string | null;
  actor_id: number | null;
}): string {
  if (row.actor_admin_id) return `admin:${row.actor_admin_id.slice(0, 8)}…`;
  if (row.actor_id) return `tg:${row.actor_id}`;
  return "system";
}

export function AuditPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const [actionFilter, setActionFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["sa-audit", actionFilter, page],
    queryFn: () =>
      superAdminApi.audit({
        action: actionFilter || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
    // 10 s refetch matches the original admin behaviour so the feed
    // stays live without a manual click.
    refetchInterval: 10_000,
  });

  const isAdmin = surface === "admin";
  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const tableCls = isAdmin ? "admin-table" : "sa-table";
  const inputCls = isAdmin ? "admin-input" : "webapp-input";
  const btnCls = isAdmin ? "admin-btn" : "sa-chip";

  const titleEl = isAdmin ? (
    <h1 className="admin-page-title">📝 {t("admin.audit.title")}</h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>📝 {t("admin.audit.title")}</h2>
  );

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const canPrev = page > 1;
  const canNext = data ? page < totalPages : false;

  return (
    <>
      {titleEl}

      <div
        style={{
          display: "flex",
          gap: "0.5rem",
          marginBottom: "0.75rem",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <input
          className={inputCls}
          placeholder={`🔍 ${t("sa.audit.filter_action")}`}
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(1);
          }}
          style={{ width: 260 }}
        />
        {actionFilter && (
          <button
            type="button"
            className={btnCls}
            onClick={() => {
              setActionFilter("");
              setPage(1);
            }}
            style={{ padding: "0.35rem 0.7rem" }}
          >
            ✕ {t("sa.stars_tx.clear_filter")}
          </button>
        )}
        {data && (
          <span style={{ color: "var(--muted)", fontSize: "0.85rem", marginLeft: "auto" }}>
            {t("sa.audit.row_count", { total: data.total })}
          </span>
        )}
      </div>

      <div className={cardCls} style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : isError ? (
          <div style={{ padding: "1rem" }}>
            ⚠️ {t("sa.stars_tx.load_failed")}{" "}
            <button onClick={() => refetch()} className={btnCls}>
              {t("sa.stars_tx.retry")}
            </button>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--muted)" }}>
            —
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className={tableCls}>
              <thead>
                <tr>
                  <th>{t("admin.audit.col_time")}</th>
                  <th>{t("admin.audit.col_actor")}</th>
                  <th>{t("admin.audit.col_action")}</th>
                  <th>{t("admin.audit.col_target")}</th>
                  <th>{t("admin.audit.col_payload")}</th>
                  <th>{t("admin.audit.col_ip")}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((row) => (
                  <tr key={row.id}>
                    <td style={{ color: "var(--muted)", whiteSpace: "nowrap" }}>
                      {new Date(row.created_at).toLocaleString()}
                    </td>
                    <td>{fmtActor(row)}</td>
                    <td
                      style={{
                        fontFamily: "monospace",
                        fontSize: "0.85rem",
                        color: "var(--accent)",
                      }}
                    >
                      {row.action}
                    </td>
                    <td>
                      {row.target_type ? (
                        <span>
                          {row.target_type}
                          {row.target_id ? `:${row.target_id}` : ""}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td
                      style={{
                        fontFamily: "monospace",
                        fontSize: "0.75rem",
                        color: "var(--muted)",
                        maxWidth: 320,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                      title={fmtPayload(row.payload)}
                    >
                      {fmtPayload(row.payload)}
                    </td>
                    <td style={{ color: "var(--muted)" }}>{row.ip_address || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {data && data.total > data.page_size && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "0.75rem",
            gap: "0.5rem",
          }}
        >
          <button
            type="button"
            className={btnCls}
            onClick={() => canPrev && setPage((p) => p - 1)}
            disabled={!canPrev}
          >
            ← {t("sa.stars_tx.prev")}
          </button>
          <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
            {t("sa.stars_tx.page_x_of_y", { page, total: totalPages })}
          </span>
          <button
            type="button"
            className={btnCls}
            onClick={() => canNext && setPage((p) => p + 1)}
            disabled={!canNext}
          >
            {t("sa.stars_tx.next")} →
          </button>
        </div>
      )}
    </>
  );
}
