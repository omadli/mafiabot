import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

interface PlayerHist {
  user_id: number;
  first_name: string;
  role: string;
  team: string;
  alive: boolean;
  died_at_round?: number | null;
}

interface RoundHist {
  round_num: number;
  night_actions: Array<{
    role: string; actor_id: number; action_type: string; target_id: number | null;
  }>;
  day_votes: Array<{ voter_id: number; target_id: number; weight: number }>;
  night_deaths: number[];
  hanged: number | null;
  last_words?: Record<string, string>;
}

interface History {
  players?: PlayerHist[];
  rounds?: RoundHist[];
}

export function SaGameReplayPage() {
  const { t } = useTranslation();
  const { t: tFlat } = useI18n();
  const { gameId } = useParams();

  const { data, isLoading } = useQuery({
    queryKey: ["sa-game", gameId],
    queryFn: () => saApi.game(gameId!),
    enabled: !!gameId,
  });

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {tFlat("loading")}</div>;
  }
  const hist = (data.history || {}) as History;
  const players = hist.players || [];
  const rounds = hist.rounds || [];
  const nameOf = (id: number) => players.find((p) => p.user_id === id)?.first_name ?? `#${id}`;
  const roleOf = (id: number) => {
    const r = players.find((p) => p.user_id === id)?.role;
    return r ? t(`role-${r}`, { defaultValue: r }) : "?";
  };

  return (
    <>
      <Link to="/webapp/sa/games" style={{ color: "var(--muted)" }}>
        ← {t("sa.games.title")}
      </Link>
      <h2 style={{ margin: "0.5rem 0" }}>
        🎬 {t("sa.game_replay.title")}
      </h2>
      <p style={{ margin: 0, color: "var(--muted)", fontSize: 13 }}>
        <code>{data.id}</code>
      </p>

      <div className="webapp-section" style={{ marginTop: "0.5rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <Stat label={t("sa.games.col_status")} value={data.status} />
          <Stat
            label={t("sa.game_replay.winner")}
            value={
              data.winner_team
                ? t(`sa.games.winner_${data.winner_team}`, { defaultValue: data.winner_team })
                : "—"
            }
          />
          <Stat label={t("sa.game_replay.players")} value={players.length} />
          <Stat label={t("sa.game_replay.rounds")} value={rounds.length} />
        </div>
      </div>

      {players.length > 0 && (
        <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
          <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
            👥 {t("sa.game_replay.section_players")} ({players.length})
          </summary>
          <ul style={{ listStyle: "none", margin: "0.5rem 0 0", padding: 0 }}>
            {players.map((p) => (
              <li
                key={p.user_id}
                style={{
                  padding: "0.35rem 0",
                  borderBottom: "1px solid var(--border, #222)",
                  fontSize: 13,
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <span>
                  <strong>{p.first_name}</strong>{" "}
                  <small style={{ color: "var(--muted)" }}>
                    ({t(`role-${p.role}`, { defaultValue: p.role })})
                  </small>
                </span>
                <span>
                  {p.alive ? (
                    <span style={{ color: "#4ade80" }}>✓</span>
                  ) : (
                    <span style={{ color: "#e74c3c" }}>💀 R{p.died_at_round}</span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}

      {rounds.map((r) => (
        <details key={r.round_num} className="webapp-section" style={{ marginTop: "0.5rem" }}>
          <summary style={{ cursor: "pointer", color: "var(--accent)", fontWeight: 600 }}>
            {t("admin.live.round_label")} #{r.round_num}
            {r.hanged && (
              <span style={{ color: "#f0a020", fontWeight: 400 }}>
                {" "}— ⚖️ {nameOf(r.hanged)}
              </span>
            )}
          </summary>
          <div style={{ marginTop: "0.4rem", fontSize: 13 }}>
            {r.night_actions?.length > 0 && (
              <div>
                <strong>🌙 {t("admin.live.actions")}:</strong>
                <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
                  {r.night_actions.map((a, i) => (
                    <li key={i}>
                      {t(`role-${a.role}`, { defaultValue: a.role })}{" "}
                      ({nameOf(a.actor_id)}) →{" "}
                      {t(`live.action_${a.action_type}`, { defaultValue: a.action_type })}
                      {a.target_id ? ` → ${nameOf(a.target_id)}` : ""}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {r.day_votes?.length > 0 && (
              <div>
                <strong>🗳 {t("admin.live.votes")}:</strong>
                <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
                  {r.day_votes.map((v, i) => (
                    <li key={i}>
                      {nameOf(v.voter_id)} → {v.target_id ? nameOf(v.target_id) : t("admin.live.nobody")}
                      {v.weight > 1 && ` (×${v.weight})`}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {r.night_deaths?.length > 0 && (
              <div style={{ color: "#e74c3c" }}>
                <strong>💀 {t("admin.live.deaths")}:</strong>{" "}
                {r.night_deaths.map((id) => `${nameOf(id)} (${roleOf(id)})`).join(", ")}
              </div>
            )}
            {r.last_words && Object.keys(r.last_words).length > 0 && (
              <div style={{ marginTop: 8 }}>
                <strong>💬 {t("admin.live.last_words")}:</strong>
                {Object.entries(r.last_words).map(([uid, words]) => (
                  <blockquote
                    key={uid}
                    style={{
                      margin: "4px 0",
                      paddingLeft: 8,
                      borderLeft: "2px solid var(--accent)",
                      color: "var(--muted)",
                      fontStyle: "italic",
                    }}
                  >
                    <strong>{nameOf(parseInt(uid))}:</strong> {words}
                  </blockquote>
                ))}
              </div>
            )}
          </div>
        </details>
      ))}
    </>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.03)", padding: "0.5rem", borderRadius: 6 }}>
      <div style={{ fontSize: 11, color: "var(--muted)" }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
