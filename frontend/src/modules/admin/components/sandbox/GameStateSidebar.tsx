/**
 * Right-side panel: condensed live game state.
 */

import { useTranslation } from "react-i18next";

import type {
  LiveGameState,
  LiveNightAction,
  LivePlayer,
  LiveVote,
} from "@shared/api/sandbox";

import { ROLE_EMOJI } from "../../constants/roles";

interface GameStateSidebarProps {
  state: LiveGameState;
  activeUserId: number | null;
}

function nameOf(state: LiveGameState, uid: number | null | undefined): string {
  if (!uid) return "—";
  const p = state.players.find((x) => x.user_id === uid);
  return p ? p.first_name : `#${uid}`;
}

interface PlayerRowProps {
  p: LivePlayer;
  active: boolean;
  lastAction?: string;
}

function PlayerRow({ p, active, lastAction }: PlayerRowProps) {
  const className = ["", active && "active", !p.alive && "dead"].filter(Boolean).join(" ");
  return (
    <li className={className}>
      <span className="sb-player-order">{p.join_order}</span>
      {ROLE_EMOJI[p.role] || "❓"} <strong>{p.first_name}</strong>{" "}
      <code className="sb-player-meta">
        {p.role}
        {!p.alive && p.died_at_round ? ` · R${p.died_at_round}` : ""}
      </code>
      {lastAction && <div className="sb-player-last-action">↳ {lastAction}</div>}
    </li>
  );
}

export function GameStateSidebar({ state, activeUserId }: GameStateSidebarProps) {
  const { t } = useTranslation();
  const actionByActor = state.current_actions || {};
  const voteByVoter = state.current_votes || {};
  const currentRound = state.rounds[state.rounds.length - 1];
  const confirm = currentRound?.extra?.hanging_confirm;
  const yesTotal = currentRound?.extra?.hang_yes_total ?? 0;
  const noTotal = currentRound?.extra?.hang_no_total ?? 0;
  const pendingHang = currentRound?.extra?.pending_hang_target;

  const actionSummary: Record<number, string> = {};
  Object.values(actionByActor).forEach((a) => {
    const act = a as LiveNightAction;
    actionSummary[act.actor_id] = act.target_id
      ? `${act.action_type} → ${nameOf(state, act.target_id)}`
      : `${act.action_type}`;
  });

  const aliveCount = state.players.filter((p) => p.alive).length;

  return (
    <div className="sb-sidebar-scroll">
      <div className="admin-card sb-sidebar-section">
        <div className="sb-stat-row">
          <strong>{t("admin.sandbox.sidebar.phase")}</strong>
          <code>{state.phase}</code>
        </div>
        <div className="sb-stat-row">
          <strong>{t("admin.sandbox.sidebar.round")}</strong>
          <span>{state.round_num}</span>
        </div>
        <div className="sb-stat-row">
          <strong>{t("admin.sandbox.sidebar.alive")}</strong>
          <span>
            {aliveCount}/{state.players.length}
          </span>
        </div>
      </div>

      <div className="admin-card sb-sidebar-section">
        <strong>
          {t("admin.sandbox.sidebar.players")} ({state.players.length})
        </strong>
        <ul className="sb-player-list">
          {[...state.players]
            .sort((a, b) => a.join_order - b.join_order)
            .map((p) => (
              <PlayerRow
                key={p.user_id}
                p={p}
                active={p.user_id === activeUserId}
                lastAction={actionSummary[p.user_id]}
              />
            ))}
        </ul>
      </div>

      {Object.keys(actionByActor).length > 0 && (
        <details className="admin-card sb-sidebar-section" open>
          <summary>
            <strong>
              {t("admin.sandbox.sidebar.current_actions")} ({Object.keys(actionByActor).length})
            </strong>
          </summary>
          <ul style={{ margin: "0.4rem 0 0", padding: "0 0 0 1rem" }}>
            {Object.values(actionByActor).map((a) => {
              const act = a as LiveNightAction;
              return (
                <li key={act.actor_id} style={{ fontSize: "0.85rem" }}>
                  {nameOf(state, act.actor_id)} <code>{act.action_type}</code> →{" "}
                  <strong>{nameOf(state, act.target_id)}</strong>
                </li>
              );
            })}
          </ul>
        </details>
      )}

      {Object.keys(voteByVoter).length > 0 && (
        <details className="admin-card sb-sidebar-section" open>
          <summary>
            <strong>
              {t("admin.sandbox.sidebar.current_votes")} ({Object.keys(voteByVoter).length})
            </strong>
          </summary>
          <ul style={{ margin: "0.4rem 0 0", padding: "0 0 0 1rem" }}>
            {Object.values(voteByVoter).map((v) => {
              const vote = v as LiveVote;
              return (
                <li key={vote.voter_id} style={{ fontSize: "0.85rem" }}>
                  {nameOf(state, vote.voter_id)} →{" "}
                  <strong>{nameOf(state, vote.target_id)}</strong>
                  {vote.weight > 1 && (
                    <span style={{ color: "var(--muted)" }}> ×{vote.weight}</span>
                  )}
                </li>
              );
            })}
          </ul>
        </details>
      )}

      {confirm && pendingHang && (
        <div className="admin-card sb-sidebar-section">
          <strong>{t("admin.sandbox.sidebar.hanging_confirm")}</strong>
          <div style={{ marginTop: "0.25rem", fontSize: "0.9rem" }}>
            {t("admin.sandbox.sidebar.target")}:{" "}
            <strong>{nameOf(state, pendingHang)}</strong>
          </div>
          <div style={{ marginTop: "0.4rem", display: "flex", gap: "0.75rem" }}>
            <span>👍 {yesTotal}</span>
            <span>👎 {noTotal}</span>
          </div>
        </div>
      )}

      {state.winner_team && (
        <div className="admin-card sb-sidebar-section sb-winner-card">
          <strong>
            🏁 {t("admin.sandbox.sidebar.winner")}:{" "}
            {t(`admin.sandbox.team_${state.winner_team}`, { defaultValue: state.winner_team })}
          </strong>
          <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: "0.25rem" }}>
            {state.winner_user_ids.map((uid) => nameOf(state, uid)).join(", ")}
          </div>
        </div>
      )}
    </div>
  );
}
