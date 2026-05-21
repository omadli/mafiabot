import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { ErrorBanner, Pagination, Skeleton } from "../components/Ui";
import { groupApi } from "@shared/api/group";

export function LeaderboardPage() {
  const { t } = useTranslation();
  const { groupId } = useParams();
  const gid = parseInt(groupId || "0");
  const [page, setPage] = useState(1);
  const pageSize = 30;

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["leaderboard", gid, page],
    queryFn: () => groupApi.leaderboard(gid, page, pageSize),
    enabled: !!gid,
  });

  return (
    <main>
      <h2>🏆 {t("webapp.leaderboard.title")}</h2>

      {isLoading && <Skeleton rows={6} height={56} />}

      {isError && <ErrorBanner onRetry={() => refetch()} />}

      {!isLoading && !isError && data?.items.length === 0 && (
        <div className="webapp-section" style={{ textAlign: "center", color: "var(--muted)" }}>
          {t("webapp.leaderboard.empty")}
        </div>
      )}

      {!isLoading && !isError && data && data.items.length > 0 && (
        <>
          <div className="webapp-section" style={{ padding: 0 }}>
            {data.items.map((p) => {
              // Medal podium only when on page 1
              let badge: string | number = p.rank;
              if (page === 1) {
                if (p.rank === 1) badge = "🥇";
                else if (p.rank === 2) badge = "🥈";
                else if (p.rank === 3) badge = "🥉";
                else badge = `${p.rank}.`;
              } else {
                badge = `${p.rank}.`;
              }
              return (
                <div key={p.user_id} className="webapp-leaderboard-row">
                  <div className="webapp-leaderboard-rank">{badge}</div>
                  <div className="webapp-leaderboard-name">
                    <div>{p.first_name}</div>
                    <small style={{ color: "var(--muted)" }}>
                      {t("webapp.leaderboard.games_winrate", {
                        games: p.games_total,
                        pct: (p.winrate * 100).toFixed(0),
                      })}
                    </small>
                  </div>
                  <div className="webapp-leaderboard-elo">{p.elo}</div>
                </div>
              );
            })}
          </div>

          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onChange={setPage}
          />
        </>
      )}
    </main>
  );
}
