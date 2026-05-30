/**
 * Groups browser — paginated, filterable, with block / unblock actions.
 *
 * Combined from admin/GroupsPage (search box, is_blocked filter, block
 * mutation) and webapp/SaGroupsPage (last-game-at column, colour-coded
 * status). Mounts in both shells via SaProvider.
 *
 * Auth routes through `superAdminApi.groups` → `/api/admin/groups`
 * (JWT) or `/api/sa/groups` (initData); the block / unblock POST pair
 * dispatches the same way.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { superAdminApi } from "@shared/api/superAdmin";

import { useSa, useSaPath } from "../context";

const PAGE_SIZE = 50;

export function GroupsPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const groupDetailBase = useSaPath("/groups");
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [isBlocked, setIsBlocked] = useState<boolean | "">("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["sa-groups", search, isBlocked, page],
    queryFn: () =>
      superAdminApi.groups({
        search: search || undefined,
        is_blocked: isBlocked === "" ? undefined : isBlocked,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  const blockMutation = useMutation({
    mutationFn: ({ groupId, reason }: { groupId: number; reason: string }) =>
      superAdminApi.blockGroup(groupId, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-groups"] }),
  });

  const unblockMutation = useMutation({
    mutationFn: (groupId: number) => superAdminApi.unblockGroup(groupId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-groups"] }),
  });

  const isAdmin = surface === "admin";
  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const tableCls = isAdmin ? "admin-table" : "sa-table";
  const inputCls = isAdmin ? "admin-input" : "webapp-input";
  const btnCls = isAdmin ? "admin-btn" : "sa-chip";

  const titleEl = isAdmin ? (
    <h1 className="admin-page-title">💬 {t("admin.groups.title")}</h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>💬 {t("admin.groups.title")}</h2>
  );

  const totalPages = data
    ? Math.max(1, Math.ceil(data.total / PAGE_SIZE))
    : 1;
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
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <input
          className={inputCls}
          style={{ flex: "1 1 240px", maxWidth: 340 }}
          placeholder={`🔍 ${t("search")}`}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <select
          className={inputCls}
          style={{ width: "auto" }}
          value={isBlocked === "" ? "" : isBlocked ? "y" : "n"}
          onChange={(e) => {
            const v = e.target.value;
            setIsBlocked(v === "" ? "" : v === "y");
            setPage(1);
          }}
        >
          <option value="">{t("admin.groups.filter_all", "All")}</option>
          <option value="y">{t("admin.groups.blocked", "Blocked")}</option>
          <option value="n">
            {t("admin.groups.filter_active", "Not blocked")}
          </option>
        </select>
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
                  <th>{t("admin.groups.col_id")}</th>
                  <th>{t("admin.groups.col_title")}</th>
                  <th style={{ textAlign: "right" }}>
                    {t("admin.groups.col_games")}
                  </th>
                  <th>{t("admin.groups.col_status")}</th>
                  <th>{t("admin.groups_extra.col_last_game", "Last game")}</th>
                  <th>{t("admin.groups.col_actions")}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((g) => (
                  <tr key={g.id}>
                    {/* Telegram group IDs are identifiers — render raw. */}
                    <td
                      style={{ color: "var(--muted)", fontFamily: "monospace" }}
                    >
                      <Link to={`${groupDetailBase}/${g.id}`}>
                        {String(g.id)}
                      </Link>
                    </td>
                    <td>
                      <Link to={`${groupDetailBase}/${g.id}`}>{g.title}</Link>
                    </td>
                    <td style={{ textAlign: "right" }}>{g.games_total}</td>
                    <td>
                      {!g.is_active ? (
                        <span style={{ color: "var(--muted)" }}>—</span>
                      ) : g.is_blocked ? (
                        <span style={{ color: "#e74c3c" }}>
                          🚫 {t("admin.groups.blocked", "Blocked")}
                        </span>
                      ) : !g.onboarding_completed ? (
                        <span style={{ color: "#f0a020" }}>
                          ⏳ {t("admin.groups.not_onboarded", "Not onboarded")}
                        </span>
                      ) : (
                        <span style={{ color: "#4ade80" }}>
                          ✓ {t("admin.groups.active", "Active")}
                        </span>
                      )}
                    </td>
                    <td
                      style={{
                        color: "var(--muted)",
                        whiteSpace: "nowrap",
                        fontSize: "0.85rem",
                      }}
                    >
                      {g.last_game_at
                        ? new Date(g.last_game_at).toLocaleDateString()
                        : "—"}
                    </td>
                    <td
                      style={{
                        display: "flex",
                        gap: "0.4rem",
                        flexWrap: "wrap",
                      }}
                    >
                      <Link
                        className={btnCls}
                        to={`${groupDetailBase}/${g.id}/live`}
                      >
                        🎥 {t("admin.groups.live", "Live")}
                      </Link>
                      {g.is_blocked ? (
                        <button
                          type="button"
                          className={btnCls}
                          onClick={() => unblockMutation.mutate(g.id)}
                          disabled={unblockMutation.isPending}
                        >
                          {t("admin.groups.unblock", "Unblock")}
                        </button>
                      ) : (
                        <button
                          type="button"
                          className={`${btnCls} ${isAdmin ? "admin-btn-danger" : ""}`}
                          style={!isAdmin ? { color: "#e74c3c" } : undefined}
                          onClick={() => {
                            const reason = prompt(
                              t("admin.prompts.block_reason", "Reason:"),
                              t("admin.prompts.default_reason", "—"),
                            );
                            if (reason)
                              blockMutation.mutate({ groupId: g.id, reason });
                          }}
                          disabled={blockMutation.isPending}
                        >
                          {t("admin.groups.block", "Block")}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {data && data.total > PAGE_SIZE && (
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
