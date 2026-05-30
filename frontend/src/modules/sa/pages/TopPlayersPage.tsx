/**
 * Global leaderboard — top players by ELO / wins / streak / level.
 *
 * Combined from `admin/TopPlayersPage` (Link to user detail) and
 * `webapp/SaPlayersPage` (colour-coded winrate). Mounts in both
 * shells via the SaProvider context.
 *
 * Auth-aware: `superAdminApi.topPlayers` dispatches between
 * `/api/admin/top-players` (JWT) and `/api/sa/top-players` (initData).
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { superAdminApi, type TopPlayersSort } from "@shared/api/superAdmin";

import { useSa, useSaPath } from "../context";

const SORTS: TopPlayersSort[] = [
  "elo",
  "games_won",
  "games_total",
  "longest_win_streak",
  "level",
];

export function TopPlayersPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const userDetailBase = useSaPath("/users");
  const [sort, setSort] = useState<TopPlayersSort>("elo");

  const { data, isLoading } = useQuery({
    queryKey: ["sa-top-players", sort],
    queryFn: () => superAdminApi.topPlayers(sort, 100),
  });

  const isAdmin = surface === "admin";
  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const tableCls = isAdmin ? "admin-table" : "sa-table";
  const btnCls = isAdmin ? "admin-btn" : "sa-chip";

  const titleEl = isAdmin ? (
    <h1 className="admin-page-title">🏆 {t("admin.top_players.title")}</h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>🏆 {t("admin.top_players.title")}</h2>
  );

  return (
    <>
      {titleEl}

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: "1rem" }}>
        {SORTS.map((s) => (
          <button
            key={s}
            className={`${btnCls} ${
              sort === s ? (isAdmin ? "primary" : "active") : ""
            }`}
            onClick={() => setSort(s)}
          >
            {t(`admin.top_players.sort_${s}`)}
          </button>
        ))}
      </div>

      <div className={cardCls} style={{ padding: 0, overflow: "hidden" }}>
        {isLoading || !data ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className={tableCls}>
              <thead>
                <tr>
                  <th>{t("admin.top_players.col_rank")}</th>
                  <th>{t("admin.top_players.col_name")}</th>
                  <th style={{ textAlign: "right" }}>
                    {t("admin.top_players.col_level")}
                  </th>
                  <th style={{ textAlign: "right" }}>
                    {t("admin.top_players.col_elo")}
                  </th>
                  <th style={{ textAlign: "right" }}>
                    {t("admin.top_players.col_games")}
                  </th>
                  <th style={{ textAlign: "right" }}>
                    {t("admin.top_players.col_wins")}
                  </th>
                  <th style={{ textAlign: "right" }}>
                    {t("admin.top_players.col_winrate")}
                  </th>
                  <th style={{ textAlign: "right" }}>
                    {t("admin.top_players.col_streak")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((p) => (
                  <tr key={p.user_id}>
                    <td style={{ color: "var(--muted)" }}>#{p.rank}</td>
                    <td>
                      <Link
                        to={`${userDetailBase}/${p.user_id}`}
                        style={{ color: "inherit" }}
                      >
                        {p.is_premium && "👑 "}
                        {p.first_name}
                        {p.username && (
                          <small style={{ color: "var(--muted)", marginLeft: 6 }}>
                            @{p.username}
                          </small>
                        )}
                      </Link>
                    </td>
                    <td style={{ textAlign: "right" }}>{p.level}</td>
                    <td style={{ textAlign: "right", fontWeight: 600 }}>{p.elo}</td>
                    <td style={{ textAlign: "right" }}>{p.games_total}</td>
                    <td style={{ textAlign: "right" }}>{p.games_won}</td>
                    <td
                      style={{
                        textAlign: "right",
                        color: p.winrate_pct >= 50 ? "#4ade80" : "#e74c3c",
                      }}
                    >
                      {p.winrate_pct}%
                    </td>
                    <td style={{ textAlign: "right" }}>🔥 {p.longest_win_streak}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
