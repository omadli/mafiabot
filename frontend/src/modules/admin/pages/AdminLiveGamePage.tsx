import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { LiveGameState, useLiveGame } from "../hooks/useLiveGame";

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

export function AdminLiveGamePage() {
  const { t } = useTranslation();
  const { groupId } = useParams();
  const gid = parseInt(groupId || "0");
  const { data, isLoading, error, wsConnected, ended } = useLiveGame(gid);
  const remaining = useCountdown(data?.phase_ends_at ?? null);

  if (isLoading) return <div className="admin-card">⏳</div>;
  if (error || !data)
    return (
      <div className="admin-card">
        <Link to="/admin/groups" style={{ color: "var(--muted)" }}>
          ← {t("admin.live.back_to_groups")}
        </Link>
        <h2 style={{ marginTop: "1rem" }}>{t("admin.live.no_active_game")}</h2>
        <p style={{ color: "var(--muted)" }}>{t("admin.live.no_active_hint")}</p>
      </div>
    );

  return (
    <>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/admin/groups" style={{ color: "var(--muted)" }}>
          ← {t("admin.live.back_to_groups")}
        </Link>
      </div>
      <h1 className="admin-page-title">
        🎥 {t("admin.live.title")} — {t("admin.live.group_label")} #{data.group_id}
      </h1>
      <div
        style={{
          marginBottom: "1.5rem",
          fontSize: "0.85rem",
          color: wsConnected ? "#27ae60" : "var(--muted)",
        }}
      >
        {wsConnected ? "🟢" : "⚪"} {t("admin.live.ws_status")}{" "}
        {ended && <span style={{ color: "#e74c3c" }}>• {t("admin.live.game_ended")}</span>}
      </div>

      <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
        <KPI
          label={t("admin.live.phase")}
          value={`${PHASE_EMOJI[data.phase] || ""} ${data.phase}`}
        />
        <KPI label={t("admin.live.round")} value={`#${data.round_num}`} />
        <KPI
          label={t("admin.live.timer")}
          value={
            data.phase_ends_at
              ? `${Math.floor(remaining / 60)
                  .toString()
                  .padStart(2, "0")}:${(remaining % 60).toString().padStart(2, "0")}`
              : "—"
          }
        />
        <KPI
          label={t("admin.live.alive")}
          value={`${data.players.filter((p) => p.alive).length} / ${data.players.length}`}
        />
      </div>

      <PlayersPanel data={data} />
      <CurrentActionsPanel data={data} />
      <CurrentVotesPanel data={data} />
      <HangingConfirmPanel data={data} />
      <RoundsHistoryPanel data={data} />
    </>
  );
}

function PlayersPanel({ data }: { data: LiveGameState }) {
  const { t } = useTranslation();
  return (
    <>
      <h3 style={{ color: "var(--muted)" }}>
        {t("admin.live.section_players")} ({data.players.length})
      </h3>
      <div
        className="admin-card"
        style={{ padding: 0, overflow: "hidden", marginBottom: "1.5rem" }}
      >
        <table className="admin-table">
          <thead>
            <tr>
              <th>#</th>
              <th>{t("admin.live.col_player")}</th>
              <th>{t("admin.live.col_role")}</th>
              <th>{t("admin.live.col_team")}</th>
              <th>{t("admin.live.col_alive")}</th>
              <th>{t("admin.live.col_items")}</th>
            </tr>
          </thead>
          <tbody>
            {data.players
              .slice()
              .sort((a, b) => a.join_order - b.join_order)
              .map((p) => (
                <tr key={p.user_id}>
                  <td>{p.join_order}</td>
                  <td>
                    <Link to={`/admin/users/${p.user_id}`}>{p.first_name}</Link>
                  </td>
                  <td>
                    {ROLE_EMOJI[p.role]} {p.role}
                  </td>
                  <td>{p.team}</td>
                  <td>
                    {p.alive ? (
                      <span className="badge green">{t("admin.live.alive_yes")}</span>
                    ) : (
                      <span className="badge red">💀 {t("admin.live.round_short")}{p.died_at_round}</span>
                    )}
                  </td>
                  <td style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                    {p.items_active.length > 0 ? p.items_active.join(", ") : "—"}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function nameOf(data: LiveGameState, id: number): string {
  const p = data.players.find((x) => x.user_id === id);
  if (!p) return `#${id}`;
  return `${ROLE_EMOJI[p.role] || ""} ${p.first_name}`;
}

function CurrentActionsPanel({ data }: { data: LiveGameState }) {
  const { t } = useTranslation();
  const entries = Object.entries(data.current_actions);
  if (data.phase !== "night" && entries.length === 0) return null;
  return (
    <>
      <h3 style={{ color: "var(--muted)" }}>
        🌙 {t("admin.live.section_current_actions")} ({entries.length})
      </h3>
      <div className="admin-card" style={{ marginBottom: "1.5rem" }}>
        {entries.length === 0 ? (
          <p style={{ color: "var(--muted)", margin: 0 }}>
            {t("admin.live.no_actions_yet")}
          </p>
        ) : (
          <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.92rem" }}>
            {entries.map(([uid, a]) => {
              const actor = data.players.find((p) => p.user_id === parseInt(uid));
              return (
                <li key={uid}>
                  <code style={{ color: "var(--accent)" }}>{actor?.role}</code>{" "}
                  ({actor?.first_name}) <code>{a.action_type}</code>{" "}
                  {a.target_id !== null && a.target_id !== 0
                    ? `→ ${nameOf(data, a.target_id)}`
                    : ""}
                  {a.used_item && (
                    <span style={{ color: "var(--muted)" }}> [item: {a.used_item}]</span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </>
  );
}

function CurrentVotesPanel({ data }: { data: LiveGameState }) {
  const { t } = useTranslation();
  const entries = Object.values(data.current_votes);
  if (data.phase !== "voting" && entries.length === 0) return null;

  // Tally
  const tally = new Map<number, number>();
  for (const v of entries) {
    tally.set(v.target_id, (tally.get(v.target_id) || 0) + v.weight);
  }
  const sortedTally = [...tally.entries()].sort((a, b) => b[1] - a[1]);

  return (
    <>
      <h3 style={{ color: "var(--muted)" }}>
        🗳 {t("admin.live.section_current_votes")} ({entries.length})
      </h3>
      <div className="admin-card" style={{ marginBottom: "1.5rem" }}>
        {entries.length === 0 ? (
          <p style={{ color: "var(--muted)", margin: 0 }}>
            {t("admin.live.no_votes_yet")}
          </p>
        ) : (
          <>
            <h4 style={{ margin: "0 0 0.5rem 0", color: "var(--muted)" }}>
              {t("admin.live.tally")}
            </h4>
            <ul style={{ margin: "0 0 1rem 0", paddingLeft: "1.5rem", fontSize: "0.92rem" }}>
              {sortedTally.map(([tid, count]) => (
                <li key={tid}>
                  <strong>
                    {tid === 0 ? t("admin.live.nobody") : nameOf(data, tid)}:
                  </strong>{" "}
                  {count}
                </li>
              ))}
            </ul>
            <h4 style={{ margin: "0 0 0.5rem 0", color: "var(--muted)" }}>
              {t("admin.live.individual_votes")}
            </h4>
            <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
              {entries.map((v, i) => (
                <li key={i}>
                  {nameOf(data, v.voter_id)} →{" "}
                  {v.target_id === 0
                    ? t("admin.live.nobody")
                    : nameOf(data, v.target_id)}{" "}
                  {v.weight > 1 && `(×${v.weight})`}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </>
  );
}

function HangingConfirmPanel({ data }: { data: LiveGameState }) {
  const { t } = useTranslation();
  if (data.phase !== "hanging_confirm" && data.rounds.length === 0) return null;
  const current = data.rounds[data.rounds.length - 1];
  if (!current) return null;
  const hc = current.extra?.hanging_confirm;
  const target = current.extra?.pending_hang_target;
  if (!target && !hc) return null;

  const yesSum = Object.values(hc?.yes || {}).reduce((s, w) => s + w, 0);
  const noSum = Object.values(hc?.no || {}).reduce((s, w) => s + w, 0);

  return (
    <>
      <h3 style={{ color: "var(--muted)" }}>
        ⚖️ {t("admin.live.section_hanging_confirm")}
      </h3>
      <div className="admin-card" style={{ marginBottom: "1.5rem" }}>
        {target && (
          <p style={{ margin: 0 }}>
            <strong>{t("admin.live.hang_target")}:</strong>{" "}
            {nameOf(data, target as number)}
          </p>
        )}
        <p style={{ margin: "0.5rem 0 0 0" }}>
          👍 <strong style={{ color: "#27ae60" }}>{yesSum}</strong> &nbsp;&nbsp; 👎{" "}
          <strong style={{ color: "#e74c3c" }}>{noSum}</strong>
        </p>
        {(yesSum > 0 || noSum > 0) && (
          <details style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
            <summary style={{ cursor: "pointer", color: "var(--muted)" }}>
              {t("admin.live.individual_hang_votes")}
            </summary>
            <ul style={{ paddingLeft: "1.5rem", marginTop: "0.5rem" }}>
              {Object.entries(hc?.yes || {}).map(([uid, w]) => (
                <li key={`y-${uid}`}>
                  👍 {nameOf(data, parseInt(uid))} {w > 1 && `(×${w})`}
                </li>
              ))}
              {Object.entries(hc?.no || {}).map(([uid, w]) => (
                <li key={`n-${uid}`}>
                  👎 {nameOf(data, parseInt(uid))} {w > 1 && `(×${w})`}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </>
  );
}

function RoundsHistoryPanel({ data }: { data: LiveGameState }) {
  const { t } = useTranslation();
  if (data.rounds.length === 0) return null;
  return (
    <>
      <h3 style={{ color: "var(--muted)" }}>
        {t("admin.live.section_rounds_history")} ({data.rounds.length})
      </h3>
      {data.rounds.map((r) => (
        <details
          key={r.round_num}
          className="admin-card"
          style={{ marginBottom: "0.75rem" }}
          open={r.round_num === data.round_num}
        >
          <summary style={{ cursor: "pointer", color: "var(--accent)", fontSize: "1.05rem" }}>
            {t("admin.live.round_label")} #{r.round_num}
            {r.hanged && (
              <span style={{ color: "#f0a020", marginLeft: "0.5rem" }}>
                — {t("admin.live.hanged")}: {nameOf(data, r.hanged)}
              </span>
            )}
            {r.night_deaths.length > 0 && (
              <span style={{ color: "#e74c3c", marginLeft: "0.5rem" }}>
                — 💀 {r.night_deaths.length}
              </span>
            )}
          </summary>

          {r.night_actions.length > 0 && (
            <>
              <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>
                {t("admin.live.actions")}
              </h4>
              <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
                {r.night_actions.map((a, i) => (
                  <li key={i}>
                    <code>{a.role}</code> ({nameOf(data, a.actor_id)}){" "}
                    <code>{a.action_type}</code>{" "}
                    {a.target_id !== null && a.target_id !== 0
                      ? `→ ${nameOf(data, a.target_id)}`
                      : ""}
                  </li>
                ))}
              </ul>
            </>
          )}

          {r.night_deaths.length > 0 && (
            <>
              <h4 style={{ color: "#e74c3c", margin: "0.5rem 0" }}>
                {t("admin.live.deaths")}
              </h4>
              <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
                {r.night_deaths.map((id) => (
                  <li key={id}>{nameOf(data, id)}</li>
                ))}
              </ul>
            </>
          )}

          {r.day_votes.length > 0 && (
            <>
              <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>
                {t("admin.live.votes")}
              </h4>
              <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
                {r.day_votes.map((v, i) => (
                  <li key={i}>
                    {nameOf(data, v.voter_id)} →{" "}
                    {v.target_id === 0
                      ? t("admin.live.nobody")
                      : nameOf(data, v.target_id)}{" "}
                    {v.weight > 1 && `(×${v.weight})`}
                  </li>
                ))}
              </ul>
            </>
          )}

          {Object.keys(r.last_words || {}).length > 0 && (
            <>
              <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>
                {t("admin.live.last_words")}
              </h4>
              {Object.entries(r.last_words).map(([uid, words]) => (
                <blockquote
                  key={uid}
                  style={{
                    margin: "0.3rem 0",
                    paddingLeft: "0.75rem",
                    borderLeft: "3px solid var(--accent)",
                    color: "var(--muted)",
                    fontStyle: "italic",
                  }}
                >
                  <strong>{nameOf(data, parseInt(uid))}:</strong> {words}
                </blockquote>
              ))}
            </>
          )}
        </details>
      ))}
    </>
  );
}

function KPI({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="admin-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" style={{ fontSize: "1.5rem" }}>
        {value}
      </div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

// Re-export for AdminApp routing
export default AdminLiveGamePage;
