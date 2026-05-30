/**
 * Games browser — paginated, filterable by status + group_id.
 *
 * Combined from admin/GamesPage (table layout, sort headers, group
 * jump-to-live) and webapp/SaGamesPage (status chip filter, colored
 * badges). Mounts in both shells via SaProvider.
 *
 * Auth routes through `superAdminApi.games` → `/api/admin/games`
 * (JWT) or `/api/sa/games` (initData).
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { superAdminApi } from "@shared/api/superAdmin";

import { useSa, useSaPath } from "../context";

const PAGE_SIZE = 50;

const STATUSES = ["", "running", "finished", "cancelled", "waiting"] as const;

const STATUS_COLORS: Record<string, string> = {
  finished: "#4ade80",
  running: "#f0a020",
  waiting: "#8a90a0",
  cancelled: "#e74c3c",
};

export function GamesPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const gameDetailBase = useSaPath("/games");
  const groupLiveBase = useSaPath("/groups");
  const [status, setStatus] = useState<string>("");
  const [groupId, setGroupId] = useState<string>("");
  const [page, setPage] = useState(1);

  const groupIdNum = groupId.trim() ? parseInt(groupId.trim()) || undefined : undefined;

  const { data, isLoading } = useQuery({
    queryKey: ["sa-games", status, groupIdNum, page],
    queryFn: () =>
      superAdminApi.games({
        status: status || undefined,
        group_id: groupIdNum,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  const isAdmin = surface === "admin";
  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const tableCls = isAdmin ? "admin-table" : "sa-table";
  const inputCls = isAdmin ? "admin-input" : "webapp-input";
  const btnCls = isAdmin ? "admin-btn" : "sa-chip";

  const titleEl = isAdmin ? (
    <h1 className="admin-page-title">🎲 {t("admin.games.title")}</h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>🎲 {t("admin.games.title")}</h2>
  );

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const canPrev = page > 1;
  const canNext = data ? page < totalPages : false;

  return (
    <>
      {titleEl}

      {/* Status chip filter */}
      <div
        style={{
          display: "flex",
          gap: 6,
          flexWrap: "wrap",
          marginBottom: "0.5rem",
        }}
      >
        {STATUSES.map((s) => (
          <button
            key={s || "all"}
            type="button"
            className={`${btnCls} ${
              status === s ? (isAdmin ? "primary" : "active") : ""
            }`}
            onClick={() => {
              setStatus(s);
              setPage(1);
            }}
            style={{ padding: "0.3rem 0.7rem", fontSize: 13 }}
          >
            {s === ""
              ? t("admin.games.filter_all", "All")
              : t(`admin.games.status_${s}`, s)}
          </button>
        ))}
      </div>

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
          style={{ width: 160 }}
          placeholder={t("admin.games.filter_group", "Group ID")}
          value={groupId}
          onChange={(e) => {
            setGroupId(e.target.value.replace(/[^0-9-]/g, ""));
            setPage(1);
          }}
          inputMode="numeric"
        />
        {groupId && (
          <button
            type="button"
            className={btnCls}
            onClick={() => {
              setGroupId("");
              setPage(1);
            }}
            style={{ padding: "0.35rem 0.7rem" }}
          >
            ✕ {t("sa.stars_tx.clear_filter")}
          </button>
        )}
        {data && (
          <span
            style={{
              color: "var(--muted)",
              fontSize: "0.85rem",
              marginLeft: "auto",
            }}
          >
            {t("sa.audit.row_count", { total: data.total })}
          </span>
        )}
      </div>

      <div className={cardCls} style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : !data || data.items.length === 0 ? (
          <div
            style={{ padding: "2rem", textAlign: "center", color: "var(--muted)" }}
          >
            —
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className={tableCls}>
              <thead>
                <tr>
                  <th>{t("admin.games.col_id")}</th>
                  <th>{t("admin.games.col_group")}</th>
                  <th>{t("admin.games.col_status")}</th>
                  <th>{t("admin.games.col_winner")}</th>
                  <th>{t("admin.games.col_started")}</th>
                  <th>{t("admin.games.col_duration")}</th>
                  <th>{t("admin.games_extra.col_bounty")}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((g) => (
                  <tr key={g.id}>
                    <td
                      style={{ color: "var(--muted)", fontFamily: "monospace" }}
                    >
                      <Link to={`${gameDetailBase}/${g.id}`}>
                        {g.id.slice(0, 8)}…
                      </Link>
                    </td>
                    <td>
                      {/* Group ID as identifier — no thousand separators
                          via toString(). The /:gid/live target lives at
                          a different prefix in admin (just /groups/{id})
                          vs webapp (groups/{id}/live) but the shared
                          context resolves both. */}
                      <Link to={`${groupLiveBase}/${g.group_id}/live`}>
                        {String(g.group_id)}
                      </Link>
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: 12,
                          padding: "2px 8px",
                          borderRadius: 999,
                          background: "rgba(255,255,255,0.06)",
                          color: STATUS_COLORS[g.status] || "var(--muted)",
                        }}
                      >
                        {t(`admin.games.status_${g.status}`, g.status)}
                      </span>
                    </td>
                    <td>
                      {g.winner_team
                        ? t(`admin.games.team_${g.winner_team}`, g.winner_team)
                        : "—"}
                    </td>
                    <td style={{ color: "var(--muted)", whiteSpace: "nowrap" }}>
                      {g.started_at ? new Date(g.started_at).toLocaleString() : "—"}
                    </td>
                    <td style={{ color: "var(--muted)", whiteSpace: "nowrap" }}>
                      {g.finished_at
                        ? new Date(g.finished_at).toLocaleString()
                        : "—"}
                    </td>
                    <td>{g.bounty_per_winner ? `💎 ${g.bounty_per_winner}` : "—"}</td>
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
