/**
 * Single finished-game replay for group admins.
 *
 * Reached from `HistoryPage` (each row links here). Shows a summary
 * header plus the full per-round breakdown via the shared
 * `GameHistoryView` — who had which role, who targeted whom each night,
 * deaths, day votes, hangings and last words.
 */

import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { ErrorBanner, Skeleton } from "../components/Ui";
import { GameHistoryView } from "@shared/components/GameHistoryView";
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

export function HistoryDetailPage() {
  const { t, i18n } = useTranslation();
  const { groupId, gameId } = useParams();
  const gid = parseInt(groupId || "0");

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["group-game-detail", gid, gameId],
    queryFn: () => groupApi.gameDetail(gid, gameId!),
    enabled: !!gid && !!gameId,
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

  const players = data?.history?.players ?? [];
  const rounds = data?.history?.rounds ?? [];

  return (
    <main>
      <div style={{ marginBottom: "0.5rem" }}>
        <Link to={`/webapp/history/${groupId}`} style={{ color: "var(--muted)" }}>
          {t("webapp.history.detail.back")}
        </Link>
      </div>

      <h2>{t("webapp.history.title")}</h2>

      {isLoading && <Skeleton rows={4} height={72} />}
      {isError && <ErrorBanner onRetry={() => refetch()} />}

      {!isLoading && !isError && data && (
        <>
          {/* Summary */}
          <div className="webapp-section">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <Stat
                label={t("webapp.history.detail.winner")}
                value={`${WINNER_BADGE[data.winner_team ?? ""] ?? "❔"} ${winnerLabel(
                  data.winner_team,
                  t,
                )}`}
              />
              <Stat
                label={t("webapp.history.detail.duration")}
                value={
                  data.duration_seconds != null
                    ? t("webapp.history.duration_minutes", {
                        m: Math.round(data.duration_seconds / 60),
                      })
                    : "—"
                }
              />
              <Stat
                label={t("webapp.history.detail.players")}
                value={String(players.length)}
              />
              <Stat label={t("webapp.history.detail.rounds")} value={String(rounds.length)} />
            </div>
            <div style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}>
              {t("webapp.history.started_at_label")}: {formatDate(data.started_at)}
              {data.bounty_per_winner != null && data.bounty_per_winner > 0 && (
                <span> · 💎 {data.bounty_per_winner}</span>
              )}
            </div>
          </div>

          {/* Full per-round breakdown */}
          {data.history ? (
            <GameHistoryView history={data.history} />
          ) : (
            <div
              className="webapp-section"
              style={{ textAlign: "center", color: "var(--muted)" }}
            >
              {t("webapp.history.detail.no_rounds")}
            </div>
          )}
        </>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.03)", padding: "0.5rem", borderRadius: 6 }}>
      <div style={{ fontSize: 11, color: "var(--muted)" }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
