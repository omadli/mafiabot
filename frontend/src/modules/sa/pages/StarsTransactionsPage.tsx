/**
 * Telegram Stars revenue feed — paginated, with headline aggregates.
 *
 * Shared between `/admin/stars-transactions` (website JWT) and
 * `/webapp/sa/stars` (Telegram WebApp initData). The component is
 * route-agnostic; it picks up `basePath` + `surface` from `useSa()`
 * so the same JSX renders in either shell.
 *
 * Backend endpoints are mirrored:
 *   GET /api/admin/stars-transactions
 *   GET /api/sa/stars-transactions
 *
 * `superAdminApi.starsTransactions` dispatches between them based on
 * the JWT-vs-initData auth that's actually present.
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { superAdminApi } from "@shared/api/superAdmin";

import { useSa, useSaPath } from "../context";

const PAGE_SIZE = 50;

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function fmtTxn(value: number | null): string {
  if (value == null) return "—";
  return value.toLocaleString();
}

export function StarsTransactionsPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const userDetailHrefBase = useSaPath("/users");
  const [page, setPage] = useState(1);
  const [userFilter, setUserFilter] = useState<string>("");

  const userId = userFilter.trim() ? parseInt(userFilter.trim()) || undefined : undefined;

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["sa-stars-transactions", page, userId],
    queryFn: () => superAdminApi.starsTransactions(page, PAGE_SIZE, userId),
  });

  const isAdmin = surface === "admin";
  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const tableCls = isAdmin ? "admin-table" : "sa-table";
  const inputCls = isAdmin ? "admin-input" : "webapp-input";
  const titleEl = isAdmin ? (
    <h1 className="admin-page-title">⭐ {t("sa.stars_tx.title")}</h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>⭐ {t("sa.stars_tx.title")}</h2>
  );

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const canPrev = page > 1;
  const canNext = data ? page < totalPages : false;

  return (
    <>
      {titleEl}

      {/* Headline aggregates — total across the active filter. */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.6rem",
          marginBottom: "0.75rem",
        }}
      >
        <div className={cardCls} style={{ padding: "0.75rem 1rem" }}>
          <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>
            {t("sa.stars_tx.total_tx")}
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 600 }}>{data?.total ?? "—"}</div>
        </div>
        <div className={cardCls} style={{ padding: "0.75rem 1rem" }}>
          <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>
            ⭐ {t("sa.stars_tx.total_stars")}
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 600 }}>
            {data?.agg_total_stars?.toLocaleString() ?? "—"}
          </div>
        </div>
        <div className={cardCls} style={{ padding: "0.75rem 1rem" }}>
          <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>
            💎 {t("sa.stars_tx.total_diamonds")}
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 600 }}>
            {data?.agg_total_diamonds?.toLocaleString() ?? "—"}
          </div>
        </div>
      </div>

      {/* Filter row */}
      <div
        style={{
          display: "flex",
          gap: "0.5rem",
          marginBottom: "0.75rem",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <input
          className={inputCls}
          placeholder={t("sa.stars_tx.filter_user_placeholder")}
          value={userFilter}
          onChange={(e) => {
            setUserFilter(e.target.value);
            setPage(1);
          }}
          style={{ width: 220 }}
          inputMode="numeric"
        />
        {userFilter && (
          <button
            type="button"
            className={isAdmin ? "admin-btn" : "sa-chip"}
            onClick={() => {
              setUserFilter("");
              setPage(1);
            }}
            style={{ padding: "0.35rem 0.7rem" }}
          >
            ✕ {t("sa.stars_tx.clear_filter")}
          </button>
        )}
      </div>

      <div className={cardCls} style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : isError ? (
          <div style={{ padding: "1rem" }}>
            ⚠️ {t("sa.stars_tx.load_failed")}{" "}
            <button onClick={() => refetch()} className={isAdmin ? "admin-btn" : "sa-chip"}>
              {t("sa.stars_tx.retry")}
            </button>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--muted)" }}>
            {userFilter
              ? t("sa.stars_tx.empty_user", { user: userFilter })
              : t("sa.stars_tx.empty")}
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className={tableCls}>
              <thead>
                <tr>
                  <th>{t("sa.stars_tx.col_time")}</th>
                  <th>{t("sa.stars_tx.col_user")}</th>
                  <th style={{ textAlign: "right" }}>⭐</th>
                  <th style={{ textAlign: "right" }}>💎</th>
                  <th>{t("sa.stars_tx.col_charge_id")}</th>
                  <th>{t("sa.stars_tx.col_note")}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((tx) => (
                  <tr key={tx.id}>
                    <td style={{ color: "var(--muted)", whiteSpace: "nowrap" }}>
                      {fmtDate(tx.created_at)}
                    </td>
                    <td>
                      {tx.user_id != null ? (
                        <Link to={`${userDetailHrefBase}/${tx.user_id}`}>
                          {tx.first_name || `#${tx.user_id}`}
                          {tx.username && (
                            <small style={{ color: "var(--muted)", marginLeft: 4 }}>
                              @{tx.username}
                            </small>
                          )}
                        </Link>
                      ) : (
                        <span style={{ color: "var(--muted)" }}>—</span>
                      )}
                    </td>
                    <td style={{ textAlign: "right", fontWeight: 600 }}>
                      {fmtTxn(tx.stars_amount)}
                    </td>
                    <td style={{ textAlign: "right", color: "#4ade80" }}>
                      +{fmtTxn(tx.diamonds_amount)}
                    </td>
                    <td>
                      {tx.telegram_payment_charge_id ? (
                        <code
                          title={tx.telegram_payment_charge_id}
                          style={{
                            fontSize: "0.75rem",
                            color: "var(--muted)",
                          }}
                        >
                          {tx.telegram_payment_charge_id.slice(0, 16)}…
                        </code>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                      {tx.note || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
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
            className={isAdmin ? "admin-btn" : "sa-chip"}
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
            className={isAdmin ? "admin-btn" : "sa-chip"}
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
