/**
 * Users browser + moderation — paginated, filterable, with ban /
 * unban / quick-grant inline actions.
 *
 * Combined from admin/UsersPage (desktop table layout with sortable
 * headers, ban / unban / grant action buttons, three-state filter
 * dropdowns) and webapp/SaUsersPage (mobile-friendly card list,
 * filter chips). Picks the layout based on `surface`:
 *
 *   /admin/users               table + action column
 *   /webapp/sa/users           list cards (mod actions live on the
 *                              detail page on mobile — no room
 *                              for them in the row chip)
 *
 * Auth routes through superAdminApi.users / banUser / unbanUser /
 * grantDiamonds → /api/{admin|sa}/users(/...).
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { superAdminApi } from "@shared/api/superAdmin";

import { useSa, useSaPath } from "../context";

const PAGE_SIZE = 50;

export function UsersPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const userDetailBase = useSaPath("/users");
  const qc = useQueryClient();
  const isAdmin = surface === "admin";

  const [search, setSearch] = useState("");
  const [isBanned, setIsBanned] = useState<boolean | "">("");
  const [isPremium, setIsPremium] = useState<boolean | "">("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["sa-users", search, isBanned, isPremium, page],
    queryFn: () =>
      superAdminApi.users({
        search: search || undefined,
        is_banned: isBanned === "" ? undefined : isBanned,
        is_premium: isPremium === "" ? undefined : isPremium,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  const banMutation = useMutation({
    mutationFn: ({ userId, reason }: { userId: number; reason: string }) =>
      superAdminApi.banUser(userId, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-users"] }),
  });

  const unbanMutation = useMutation({
    mutationFn: (userId: number) => superAdminApi.unbanUser(userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-users"] }),
  });

  const grantMutation = useMutation({
    mutationFn: ({ userId, amount }: { userId: number; amount: number }) =>
      superAdminApi.grantDiamonds(userId, amount, "admin manual grant"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-users"] }),
  });

  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const tableCls = isAdmin ? "admin-table" : "sa-table";
  const inputCls = isAdmin ? "admin-input" : "webapp-input sa-input";
  const btnCls = isAdmin ? "admin-btn" : "sa-chip";

  const titleEl = isAdmin ? (
    <h1 className="admin-page-title">👥 {t("admin.users.title")}</h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>👥 {t("sa.users.title")}</h2>
  );

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const canPrev = page > 1;
  const canNext = data ? page < totalPages : false;

  return (
    <>
      {titleEl}

      {/* Filter row */}
      <div
        className={!isAdmin ? "webapp-section" : undefined}
        style={
          isAdmin
            ? {
                display: "flex",
                gap: "0.6rem",
                marginBottom: "1rem",
                flexWrap: "wrap",
                alignItems: "center",
              }
            : { display: "grid", gap: "0.5rem" }
        }
      >
        <input
          className={inputCls}
          style={
            isAdmin
              ? { flex: "1 1 260px", maxWidth: 360 }
              : { width: "100%" }
          }
          placeholder={`🔍 ${t("admin.users.search_placeholder", "Search users")}`}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />

        {isAdmin ? (
          <>
            <select
              className={inputCls}
              style={{ width: "auto" }}
              value={isBanned === "" ? "" : isBanned ? "y" : "n"}
              onChange={(e) => {
                const v = e.target.value;
                setIsBanned(v === "" ? "" : v === "y");
                setPage(1);
              }}
            >
              <option value="">{t("admin.users.filter_ban_all", "All")}</option>
              <option value="y">{t("admin.users.banned", "Banned")}</option>
              <option value="n">
                {t("admin.users.filter_not_banned", "Not banned")}
              </option>
            </select>
            <select
              className={inputCls}
              style={{ width: "auto" }}
              value={isPremium === "" ? "" : isPremium ? "y" : "n"}
              onChange={(e) => {
                const v = e.target.value;
                setIsPremium(v === "" ? "" : v === "y");
                setPage(1);
              }}
            >
              <option value="">
                {t("admin.users.filter_premium_all", "All")}
              </option>
              <option value="y">{t("admin.users.premium", "Premium")}</option>
              <option value="n">
                {t("admin.users.filter_not_premium", "Not premium")}
              </option>
            </select>
          </>
        ) : (
          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
            <FilterChip
              label={`👑 ${t("sa.users.filter_premium", "Premium")}`}
              active={isPremium === true}
              onClick={() => {
                setIsPremium(isPremium === true ? "" : true);
                setPage(1);
              }}
            />
            <FilterChip
              label={`🚫 ${t("sa.users.filter_banned", "Banned")}`}
              active={isBanned === true}
              onClick={() => {
                setIsBanned(isBanned === true ? "" : true);
                setPage(1);
              }}
            />
          </div>
        )}
      </div>

      {/* Desktop table layout */}
      {isAdmin ? (
        <>
          <div className={cardCls} style={{ padding: 0, overflow: "hidden" }}>
            {isLoading ? (
              <div style={{ padding: "2rem", textAlign: "center" }}>
                ⏳ {t("loading")}
              </div>
            ) : !data || data.items.length === 0 ? (
              <div
                style={{
                  padding: "2rem",
                  textAlign: "center",
                  color: "var(--muted)",
                }}
              >
                {t("sa.users.empty", "—")}
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table className={tableCls}>
                  <thead>
                    <tr>
                      <th>{t("admin.users.col_id")}</th>
                      <th>{t("admin.users.col_name")}</th>
                      <th style={{ textAlign: "right" }}>
                        {t("admin.users_extra.col_diamonds")}
                      </th>
                      <th style={{ textAlign: "right" }}>
                        {t("admin.users_extra.col_dollars")}
                      </th>
                      <th style={{ textAlign: "right" }}>
                        {t("admin.users_extra.col_lvl")}
                      </th>
                      <th style={{ textAlign: "right" }}>
                        {t("admin.users_extra.col_elo")}
                      </th>
                      <th style={{ textAlign: "right" }}>
                        {t("admin.users.col_balance")}
                      </th>
                      <th>{t("admin.users.col_status")}</th>
                      <th>{t("admin.users.col_actions")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((u) => (
                      <tr key={u.id}>
                        {/* User IDs are identifiers — render raw so they
                            don't get thousand-separator formatting. */}
                        <td style={{ color: "var(--muted)" }}>
                          <Link to={`${userDetailBase}/${u.id}`}>
                            {String(u.id)}
                          </Link>
                        </td>
                        <td>
                          <Link
                            to={`${userDetailBase}/${u.id}`}
                            style={{ color: "inherit" }}
                          >
                            {u.first_name || `#${u.id}`}
                            {u.username && (
                              <small
                                style={{
                                  color: "var(--muted)",
                                  marginLeft: 6,
                                }}
                              >
                                @{u.username}
                              </small>
                            )}
                          </Link>
                        </td>
                        <td style={{ textAlign: "right" }}>{u.diamonds}</td>
                        <td style={{ textAlign: "right" }}>{u.dollars}</td>
                        <td style={{ textAlign: "right" }}>{u.level}</td>
                        <td style={{ textAlign: "right" }}>{u.elo}</td>
                        <td style={{ textAlign: "right" }}>{u.games_total}</td>
                        <td>
                          {u.is_premium && (
                            <span className="badge yellow">
                              {t("admin.users.premium", "Premium")}
                            </span>
                          )}{" "}
                          {u.is_banned && (
                            <span className="badge red">
                              {t("admin.users.banned", "Banned")}
                            </span>
                          )}
                        </td>
                        <td style={{ display: "flex", gap: "0.4rem" }}>
                          {u.is_banned ? (
                            <button
                              type="button"
                              className={btnCls}
                              onClick={() => unbanMutation.mutate(u.id)}
                              disabled={unbanMutation.isPending}
                            >
                              {t("admin.users.unban", "Unban")}
                            </button>
                          ) : (
                            <button
                              type="button"
                              className={`${btnCls} admin-btn-danger`}
                              onClick={() => {
                                const reason = prompt(
                                  t("admin.prompts.ban_reason", "Ban reason"),
                                  t("admin.prompts.default_reason", "—"),
                                );
                                if (reason)
                                  banMutation.mutate({
                                    userId: u.id,
                                    reason,
                                  });
                              }}
                              disabled={banMutation.isPending}
                            >
                              {t("admin.users.ban", "Ban")}
                            </button>
                          )}
                          <button
                            type="button"
                            className={btnCls}
                            onClick={() => {
                              const amt = prompt(
                                t(
                                  "admin.users.grant_diamonds",
                                  "Grant diamonds:",
                                ),
                                "100",
                              );
                              if (amt)
                                grantMutation.mutate({
                                  userId: u.id,
                                  amount: parseInt(amt) || 0,
                                });
                            }}
                            disabled={grantMutation.isPending}
                          >
                            💎+
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      ) : (
        // WebApp mobile card list
        <>
          {isLoading || !data ? (
            <div className={cardCls}>⏳ {t("loading")}</div>
          ) : data.items.length === 0 ? (
            <div
              className={cardCls}
              style={{ padding: "1rem", textAlign: "center", color: "var(--muted)" }}
            >
              {t("sa.users.empty", "—")}
            </div>
          ) : (
            <div className={cardCls} style={{ padding: 0 }}>
              <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
                {data.items.map((u) => (
                  <li
                    key={u.id}
                    style={{
                      borderBottom: "1px solid #2a2a45",
                      padding: "0.6rem 0.9rem",
                    }}
                  >
                    <Link
                      to={`${userDetailBase}/${u.id}`}
                      style={{ color: "inherit", textDecoration: "none" }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          gap: "0.4rem",
                        }}
                      >
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div
                            style={{
                              display: "flex",
                              gap: 6,
                              alignItems: "baseline",
                            }}
                          >
                            <strong>
                              {u.first_name || `#${u.id}`}
                            </strong>
                            {u.username && (
                              <small style={{ color: "var(--muted)" }}>
                                @{u.username}
                              </small>
                            )}
                            {u.is_premium && <span title="premium">👑</span>}
                            {u.is_banned && <span title="banned">🚫</span>}
                          </div>
                          <div
                            style={{
                              fontSize: 12,
                              color: "var(--muted)",
                              marginTop: 2,
                            }}
                          >
                            💎 {u.diamonds} · 💵 {u.dollars} · 🎮{" "}
                            {u.games_total} · ELO {u.elo}
                          </div>
                        </div>
                        <span style={{ color: "var(--muted)" }}>›</span>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

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

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`sa-chip ${active ? "active" : ""}`}
      onClick={onClick}
      style={{ padding: "0.3rem 0.7rem" }}
    >
      {label}
    </button>
  );
}
