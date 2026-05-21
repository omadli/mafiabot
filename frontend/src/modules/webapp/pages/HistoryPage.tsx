/**
 * Group game history — paginated list of finished games for this group.
 *
 * Entry point: bot `/settings` menu's "Tarix" button deeplinks to
 * `?start=history_<group_id>`; `WebAppHome` parses that and routes here.
 */

import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { ErrorBanner, Pagination, Skeleton } from "../components/Ui";
import type { GroupHistoryItem } from "@shared/api/group";
import { groupApi } from "@shared/api/group";

const WINNER_BADGE: Record<string, string> = {
  citizens: "👨‍👨‍👧‍👦",
  mafia: "🤵🏼",
  singleton: "🎯",
};

function winnerLabel(team: string | null, t: (k: string) => string): string {
  if (team === "citizens") return t("webapp.history.winner_civilians");
  if (team === "mafia") return t("webapp.history.winner_mafia");
  if (team === "singleton") return t("webapp.history.winner_singleton");
  return t("webapp.history.winner_unknown");
}

export function HistoryPage() {
  const { t, i18n } = useTranslation();
  const { groupId } = useParams();
  const gid = parseInt(groupId || "0");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["group-history", gid, page],
    queryFn: () => groupApi.history(gid, page, pageSize),
    enabled: !!gid,
  });

  const formatDate = (iso: string | null): string => {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString(i18n.language || "uz", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  const formatDuration = (sec: number | null): string => {
    if (sec == null) return "—";
    const minutes = Math.round(sec / 60);
    return t("webapp.history.duration_minutes", { m: minutes });
  };

  return (
    <main>
      <h2>{t("webapp.history.title")}</h2>

      {isLoading && <Skeleton rows={4} height={72} />}

      {isError && <ErrorBanner onRetry={() => refetch()} />}

      {!isLoading && !isError && data?.items.length === 0 && (
        <div className="webapp-section" style={{ textAlign: "center", color: "var(--muted)" }}>
          {t("webapp.history.empty")}
        </div>
      )}

      {!isLoading && !isError && data && data.items.length > 0 && (
        <>
          <div className="webapp-section" style={{ padding: 0 }}>
            {data.items.map((g: GroupHistoryItem) => (
              <div key={g.id} className="webapp-history-row">
                <div className="webapp-history-row-main">
                  <span className="webapp-history-badge">
                    {WINNER_BADGE[g.winner_team ?? ""] ?? "❔"} {winnerLabel(g.winner_team, t)}
                  </span>
                  <span className="webapp-history-meta">
                    {formatDate(g.started_at)} · {formatDuration(g.duration_seconds)}
                  </span>
                </div>
                <div className="webapp-history-row-aux">
                  <span>{t("webapp.history.players_count", { n: g.player_count })}</span>
                  <span>·</span>
                  <span>{t("webapp.history.alive_count", { n: g.alive_at_end })}</span>
                  {g.bounty_per_winner != null && g.bounty_per_winner > 0 && (
                    <span className="webapp-history-bounty">💎 {g.bounty_per_winner}</span>
                  )}
                </div>
              </div>
            ))}
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
