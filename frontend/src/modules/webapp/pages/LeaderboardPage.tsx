import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "@shared/api/client";

interface LeaderItem {
  user_id: number;
  first_name: string;
  username: string | null;
  elo: number;
  games_total: number;
  games_won: number;
  winrate: number;
}

export function LeaderboardPage() {
  const { t } = useTranslation();
  const { groupId } = useParams();
  const { data, isLoading } = useQuery({
    queryKey: ["leaderboard", groupId],
    queryFn: async () =>
      (
        await api.get<{ items: LeaderItem[] }>(`/group/${groupId}/leaderboard`, {
          params: { limit: 30 },
        })
      ).data,
    enabled: !!groupId,
  });

  return (
    <main>
      <h2>🏆 {t("webapp.leaderboard.title")}</h2>
      {isLoading ? (
        <div className="webapp-loading">⏳</div>
      ) : (
        <div className="webapp-section" style={{ padding: 0 }}>
          {data?.items.length === 0 ? (
            <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--muted)" }}>
              {t("webapp.leaderboard.empty")}
            </div>
          ) : (
            data?.items.map((p, idx) => (
              <div
                key={p.user_id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  padding: "0.75rem 1rem",
                  borderBottom: "1px solid #2a2a45",
                }}
              >
                <div style={{ minWidth: 32, fontWeight: 600 }}>
                  {idx === 0 ? "🥇" : idx === 1 ? "🥈" : idx === 2 ? "🥉" : `${idx + 1}.`}
                </div>
                <div style={{ flex: 1 }}>
                  <div>{p.first_name}</div>
                  <small style={{ color: "var(--muted)" }}>
                    {t("webapp.leaderboard.games_winrate", {
                      games: p.games_total,
                      pct: (p.winrate * 100).toFixed(0),
                    })}
                  </small>
                </div>
                <div style={{ color: "var(--accent)", fontWeight: 600 }}>{p.elo}</div>
              </div>
            ))
          )}
        </div>
      )}
    </main>
  );
}
