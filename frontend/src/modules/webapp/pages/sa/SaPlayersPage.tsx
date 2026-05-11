import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { saApi, type TopPlayersSort } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

const SORT_OPTIONS: { value: TopPlayersSort; labelKey: string }[] = [
  { value: "elo", labelKey: "players-sort-elo" },
  { value: "games_won", labelKey: "players-sort-games-won" },
  { value: "games_total", labelKey: "players-sort-games-total" },
  { value: "longest_win_streak", labelKey: "players-sort-streak" },
  { value: "level", labelKey: "players-sort-level" },
];

export function SaPlayersPage() {
  const { t } = useI18n();
  const [sort, setSort] = useState<TopPlayersSort>("elo");
  const { data, isLoading } = useQuery({
    queryKey: ["sa-top-players", sort],
    queryFn: () => saApi.topPlayers(sort, 100),
  });

  return (
    <div className="webapp-section">
      <h3>🏆 {t("players-title")}</h3>

      <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        {SORT_OPTIONS.map((o) => (
          <button
            key={o.value}
            onClick={() => setSort(o.value)}
            className={`sa-chip ${sort === o.value ? "active" : ""}`}
          >
            {t(o.labelKey)}
          </button>
        ))}
      </div>

      {isLoading || !data ? (
        <div>⏳ {t("loading")}</div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table className="sa-table">
            <thead>
              <tr>
                <th>{t("players-col-rank")}</th>
                <th>{t("players-col-name")}</th>
                <th style={{ textAlign: "right" }}>{t("players-col-level")}</th>
                <th style={{ textAlign: "right" }}>{t("players-col-elo")}</th>
                <th style={{ textAlign: "right" }}>{t("players-col-games")}</th>
                <th style={{ textAlign: "right" }}>{t("players-col-wins")}</th>
                <th style={{ textAlign: "right" }}>{t("players-col-winrate")}</th>
                <th style={{ textAlign: "right" }}>{t("players-col-streak")}</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((p) => (
                <tr key={p.user_id}>
                  <td>{p.rank}</td>
                  <td>
                    {p.is_premium && "👑 "}
                    {p.first_name}
                    {p.username ? (
                      <small style={{ color: "var(--muted)" }}> @{p.username}</small>
                    ) : null}
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
  );
}
