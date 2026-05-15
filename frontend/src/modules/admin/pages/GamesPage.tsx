import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "@shared/api/client";

interface GameItem {
  id: string;
  group_id: number;
  status: string;
  winner_team: string | null;
  started_at: string;
  finished_at: string | null;
  bounty_per_winner: number | null;
}

export function GamesPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["games"],
    queryFn: async () =>
      (await api.get<{ items: GameItem[]; total: number }>("/admin/games")).data,
  });

  return (
    <>
      <h1 className="admin-page-title">🎲 {t("admin.games.title")}</h1>
      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : (
          <table className="admin-table">
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
              {data?.items.map((g) => (
                <tr key={g.id}>
                  <td style={{ color: "var(--muted)", fontFamily: "monospace" }}>
                    <Link to={`/admin/games/${g.id}`}>{g.id.slice(0, 8)}…</Link>
                  </td>
                  <td>{g.group_id}</td>
                  <td>
                    {g.status === "finished" ? (
                      <span className="badge green">{t(`admin.games.status_${g.status}`)}</span>
                    ) : g.status === "running" ? (
                      <span className="badge yellow">{t(`admin.games.status_${g.status}`)}</span>
                    ) : (
                      <span className="badge">{t(`admin.games.status_${g.status}`, g.status)}</span>
                    )}
                  </td>
                  <td>
                    {g.winner_team ? t(`admin.games.team_${g.winner_team}`, g.winner_team) : "—"}
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {new Date(g.started_at).toLocaleString()}
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {g.finished_at ? new Date(g.finished_at).toLocaleString() : "—"}
                  </td>
                  <td>{g.bounty_per_winner ? `💎 ${g.bounty_per_winner}` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
