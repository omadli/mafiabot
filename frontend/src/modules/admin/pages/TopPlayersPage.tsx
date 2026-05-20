import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { adminApi } from "@shared/api/admin";
import type { TopPlayersSort } from "@shared/api/sa";

const SORTS: TopPlayersSort[] = ["elo", "games_won", "games_total", "longest_win_streak", "level"];

export function TopPlayersPage() {
  const { t } = useTranslation();
  const [sort, setSort] = useState<TopPlayersSort>("elo");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-top-players", sort],
    queryFn: () => adminApi.topPlayers(sort, 100),
  });

  return (
    <>
      <h1 className="admin-page-title">🏆 {t("admin.top_players.title")}</h1>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: "1rem" }}>
        {SORTS.map((s) => (
          <button
            key={s}
            className={`admin-btn ${sort === s ? "primary" : ""}`}
            onClick={() => setSort(s)}
          >
            {t(`admin.top_players.sort_${s}`)}
          </button>
        ))}
      </div>

      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading || !data ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>{t("admin.top_players.col_rank")}</th>
                <th>{t("admin.top_players.col_name")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.top_players.col_level")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.top_players.col_elo")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.top_players.col_games")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.top_players.col_wins")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.top_players.col_winrate")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.top_players.col_streak")}</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((p) => (
                <tr key={p.user_id}>
                  <td style={{ color: "var(--muted)" }}>#{p.rank}</td>
                  <td>
                    <Link to={`/admin/users/${p.user_id}`} style={{ color: "inherit" }}>
                      {p.is_premium && "👑 "}{p.first_name}
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
                  <td style={{ textAlign: "right" }}>{p.winrate_pct}%</td>
                  <td style={{ textAlign: "right" }}>🔥 {p.longest_win_streak}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
