import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { LiveGameState, useSaLiveGame } from "../../hooks/useSaLiveGame";

const ROLE_EMOJI: Record<string, string> = {
  citizen: "👨🏼",
  detective: "🕵🏻‍♂",
  sergeant: "👮🏻‍♂",
  mayor: "🎖",
  doctor: "👨🏻‍⚕",
  hooker: "💃",
  hobo: "🧙‍♂",
  lucky: "🤞🏼",
  suicide: "🤦🏼",
  kamikaze: "💣",
  don: "🤵🏻",
  mafia: "🤵🏼",
  lawyer: "👨‍💼",
  journalist: "👩🏼‍💻",
  killer: "🥷",
  maniac: "🔪",
  werewolf: "🐺",
  mage: "🧙",
  arsonist: "🧟",
  crook: "🤹",
  snitch: "🤓",
};

const PHASE_EMOJI: Record<string, string> = {
  waiting: "📋",
  night: "🌙",
  day: "☀️",
  voting: "🗳",
  hanging_confirm: "⚖️",
  last_words: "💬",
  finished: "🏁",
  cancelled: "🚫",
};

function useCountdown(deadline: number | null): number {
  const [now, setNow] = useState(() => Math.floor(Date.now() / 1000));
  useEffect(() => {
    if (!deadline) return;
    const t = setInterval(() => setNow(Math.floor(Date.now() / 1000)), 1000);
    return () => clearInterval(t);
  }, [deadline]);
  return deadline ? Math.max(0, deadline - now) : 0;
}

function nameOf(data: LiveGameState, id: number): string {
  const p = data.players.find((x) => x.user_id === id);
  if (!p) return `#${id}`;
  return `${ROLE_EMOJI[p.role] || ""} ${p.first_name}`;
}

export function SaLiveGamePage() {
  const { t } = useTranslation();
  const { groupId: raw } = useParams();
  const gid = parseInt(raw || "0");
  const { data, isLoading, error, wsConnected, ended } = useSaLiveGame(gid);
  const remaining = useCountdown(data?.phase_ends_at ?? null);

  if (isLoading)
    return <div className="webapp-section">⏳ {t("loading")}</div>;

  if (error || !data)
    return (
      <>
        <Link to={`/webapp/sa/groups/${gid}`} style={{ color: "var(--muted)" }}>
          ← {t("admin.live.back_to_groups")}
        </Link>
        <div className="webapp-section">
          <h3>{t("admin.live.no_active_game")}</h3>
          <p style={{ color: "var(--muted)" }}>{t("admin.live.no_active_hint")}</p>
        </div>
      </>
    );

  return (
    <>
      <Link to={`/webapp/sa/groups/${gid}`} style={{ color: "var(--muted)" }}>
        ← {t("admin.live.back_to_groups")}
      </Link>
      <h2 style={{ margin: "0.5rem 0" }}>
        🎥 {t("admin.live.title")} #{data.group_id}
      </h2>
      <p
        style={{
          margin: 0,
          fontSize: "0.75rem",
          color: wsConnected ? "#4ade80" : "var(--muted)",
        }}
      >
        {wsConnected ? "🟢" : "⚪"} {t("admin.live.ws_status")}
        {ended && <span style={{ color: "#e74c3c" }}> • {t("admin.live.game_ended")}</span>}
      </p>

      <div className="webapp-section" style={{ marginTop: "0.5rem" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "0.5rem",
            fontSize: "0.9rem",
          }}
        >
          <div>
            <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>
              {t("admin.live.phase")}
            </div>
            <div style={{ fontWeight: 600 }}>
              {PHASE_EMOJI[data.phase] || ""} {data.phase}
            </div>
          </div>
          <div>
            <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>
              {t("admin.live.round")}
            </div>
            <div style={{ fontWeight: 600 }}>#{data.round_num}</div>
          </div>
          <div>
            <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>
              {t("admin.live.timer")}
            </div>
            <div style={{ fontWeight: 600 }}>
              {data.phase_ends_at
                ? `${Math.floor(remaining / 60).toString().padStart(2, "0")}:${(remaining % 60).toString().padStart(2, "0")}`
                : "—"}
            </div>
          </div>
          <div>
            <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>
              {t("admin.live.alive")}
            </div>
            <div style={{ fontWeight: 600 }}>
              {data.players.filter((p) => p.alive).length} / {data.players.length}
            </div>
          </div>
        </div>
      </div>

      <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
        <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
          {t("admin.live.section_players")} ({data.players.length})
        </summary>
        <ul style={{ margin: "0.5rem 0 0 0", padding: 0, listStyle: "none" }}>
          {data.players
            .slice()
            .sort((a, b) => a.join_order - b.join_order)
            .map((p) => (
              <li
                key={p.user_id}
                style={{
                  padding: "0.4rem 0",
                  borderBottom: "1px solid var(--border, #222)",
                  fontSize: "0.9rem",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <span>
                  {p.join_order}. {ROLE_EMOJI[p.role] || ""} <strong>{p.first_name}</strong>{" "}
                  <small style={{ color: "var(--muted)" }}>({t(`role-${p.role}`)})</small>
                </span>
                <span style={{ fontSize: "0.75rem" }}>
                  {p.alive ? (
                    <span style={{ color: "#4ade80" }}>✓ {t("admin.live.alive_yes")}</span>
                  ) : (
                    <span style={{ color: "#e74c3c" }}>💀 {t("admin.live.round_short")}{p.died_at_round}</span>
                  )}
                </span>
              </li>
            ))}
        </ul>
      </details>

      {Object.keys(data.current_actions).length > 0 && (
        <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
          <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
            🌙 {t("admin.live.section_current_actions")} (
            {Object.keys(data.current_actions).length})
          </summary>
          <ul style={{ margin: "0.5rem 0 0 1.2rem", fontSize: "0.85rem" }}>
            {Object.entries(data.current_actions).map(([uid, a]) => {
              const actor = data.players.find((p) => p.user_id === parseInt(uid));
              return (
                <li key={uid}>
                  <strong>{actor?.first_name}</strong> ({actor?.role}) → {a.action_type}{" "}
                  {a.target_id !== null && a.target_id !== 0
                    ? `→ ${nameOf(data, a.target_id)}`
                    : ""}
                </li>
              );
            })}
          </ul>
        </details>
      )}

      {Object.keys(data.current_votes).length > 0 && (
        <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
          <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
            🗳 {t("admin.live.section_current_votes")} ({Object.keys(data.current_votes).length})
          </summary>
          <VotingTally data={data} />
        </details>
      )}

      {data.rounds.length > 0 && (
        <HangingConfirmPanel data={data} />
      )}

      <details className="webapp-section" style={{ marginTop: "0.5rem" }}>
        <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
          {t("admin.live.section_rounds_history")} ({data.rounds.length})
        </summary>
        {data.rounds.map((r) => (
          <details key={r.round_num} style={{ margin: "0.5rem 0", paddingLeft: "0.5rem" }}>
            <summary style={{ cursor: "pointer", fontSize: "0.9rem" }}>
              {t("admin.live.round_label")} #{r.round_num}
              {r.hanged && (
                <span style={{ color: "#f0a020" }}>
                  {" "}— {t("admin.live.hanged")}: {nameOf(data, r.hanged)}
                </span>
              )}
            </summary>
            <div style={{ fontSize: "0.8rem", marginTop: "0.4rem" }}>
              {r.night_actions.length > 0 && (
                <div>
                  <strong>{t("admin.live.actions")}:</strong>
                  <ul style={{ marginLeft: "1.2rem" }}>
                    {r.night_actions.map((a, i) => (
                      <li key={i}>
                        {a.role} ({nameOf(data, a.actor_id)}) → {a.action_type}{" "}
                        {a.target_id !== null && a.target_id !== 0
                          ? `→ ${nameOf(data, a.target_id)}`
                          : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {r.day_votes.length > 0 && (
                <div>
                  <strong>{t("admin.live.votes")}:</strong>
                  <ul style={{ marginLeft: "1.2rem" }}>
                    {r.day_votes.map((v, i) => (
                      <li key={i}>
                        {nameOf(data, v.voter_id)} →{" "}
                        {v.target_id === 0
                          ? t("admin.live.nobody")
                          : nameOf(data, v.target_id)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {r.night_deaths.length > 0 && (
                <div style={{ color: "#e74c3c" }}>
                  <strong>{t("admin.live.deaths")}:</strong>{" "}
                  {r.night_deaths.map((id) => nameOf(data, id)).join(", ")}
                </div>
              )}
              {Object.keys(r.last_words || {}).length > 0 && (
                <div>
                  <strong>{t("admin.live.last_words")}:</strong>
                  {Object.entries(r.last_words).map(([uid, words]) => (
                    <blockquote
                      key={uid}
                      style={{
                        margin: "0.3rem 0",
                        paddingLeft: "0.5rem",
                        borderLeft: "2px solid var(--accent)",
                        color: "var(--muted)",
                        fontStyle: "italic",
                      }}
                    >
                      <strong>{nameOf(data, parseInt(uid))}:</strong> {words}
                    </blockquote>
                  ))}
                </div>
              )}
            </div>
          </details>
        ))}
      </details>
    </>
  );
}

function VotingTally({ data }: { data: LiveGameState }) {
  const { t } = useTranslation();
  const entries = Object.values(data.current_votes);
  const tally = new Map<number, number>();
  for (const v of entries) {
    tally.set(v.target_id, (tally.get(v.target_id) || 0) + v.weight);
  }
  const sortedTally = [...tally.entries()].sort((a, b) => b[1] - a[1]);

  return (
    <>
      <ul style={{ margin: "0.5rem 0 0 1.2rem", fontSize: "0.85rem" }}>
        {sortedTally.map(([tid, count]) => (
          <li key={tid}>
            <strong>{tid === 0 ? t("admin.live.nobody") : nameOf(data, tid)}</strong>: {count}
          </li>
        ))}
      </ul>
      <details style={{ marginTop: "0.5rem" }}>
        <summary style={{ cursor: "pointer", color: "var(--muted)", fontSize: "0.8rem" }}>
          {t("admin.live.individual_votes")}
        </summary>
        <ul style={{ margin: "0.3rem 0 0 1.2rem", fontSize: "0.8rem" }}>
          {entries.map((v, i) => (
            <li key={i}>
              {nameOf(data, v.voter_id)} →{" "}
              {v.target_id === 0 ? t("admin.live.nobody") : nameOf(data, v.target_id)}{" "}
              {v.weight > 1 && `(×${v.weight})`}
            </li>
          ))}
        </ul>
      </details>
    </>
  );
}

function HangingConfirmPanel({ data }: { data: LiveGameState }) {
  const { t } = useTranslation();
  const current = data.rounds[data.rounds.length - 1];
  if (!current) return null;
  const hc = current.extra?.hanging_confirm;
  const target = current.extra?.pending_hang_target;
  if (!target && !hc) return null;

  const yesSum = Object.values(hc?.yes || {}).reduce((s, w) => s + w, 0);
  const noSum = Object.values(hc?.no || {}).reduce((s, w) => s + w, 0);

  return (
    <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
      <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
        ⚖️ {t("admin.live.section_hanging_confirm")}
      </summary>
      <div style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
        {target && (
          <p style={{ margin: 0 }}>
            <strong>{t("admin.live.hang_target")}:</strong>{" "}
            {nameOf(data, target as number)}
          </p>
        )}
        <p style={{ margin: "0.5rem 0 0 0" }}>
          👍 <strong style={{ color: "#4ade80" }}>{yesSum}</strong> &nbsp; 👎{" "}
          <strong style={{ color: "#e74c3c" }}>{noSum}</strong>
        </p>
      </div>
    </details>
  );
}
