/**
 * Presentational replay of one finished game's `Game.history` JSON.
 *
 * Renders the player roster (role, alive/dead, death reason) and a
 * collapsible per-round breakdown — night actions (who targeted whom),
 * deaths, day votes, who was hanged, and last words. Surface-agnostic:
 * styled with the `webapp-section` shell so it drops into the Telegram
 * Mini App. Data shape matches both `/api/group/{id}/history/{game_id}`
 * and the SA `/api/sa/games/{id}` replay endpoint.
 */

import { useTranslation } from "react-i18next";

import type {
  GameHistory,
  GameHistoryPlayer,
  GameHistoryRound,
} from "@shared/api/group";
import { ROLE_EMOJI } from "@shared/constants/roles";

export function GameHistoryView({ history }: { history: GameHistory }) {
  const { t } = useTranslation();

  const players = history.players ?? [];
  const rounds = history.rounds ?? [];

  const byId = new Map<number, GameHistoryPlayer>();
  players.forEach((p) => byId.set(p.user_id, p));

  const nameOf = (id: number): string => byId.get(id)?.first_name ?? `#${id}`;
  const emojiOf = (id: number): string => ROLE_EMOJI[byId.get(id)?.role ?? ""] ?? "";
  const labelOf = (id: number): string => `${emojiOf(id)} ${nameOf(id)}`.trim();
  const roleNameOf = (id: number): string => {
    const r = byId.get(id)?.role;
    return r ? t(`role-${r}`, { defaultValue: r }) : "?";
  };

  return (
    <>
      {/* === Player roster === */}
      {players.length > 0 && (
        <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
          <summary style={{ cursor: "pointer", color: "var(--accent)", fontWeight: 600 }}>
            👥 {t("webapp.history.detail.section_players")} ({players.length})
          </summary>
          <ul style={{ listStyle: "none", margin: "0.5rem 0 0", padding: 0 }}>
            {players
              .slice()
              .sort((a, b) => (a.join_order ?? 0) - (b.join_order ?? 0))
              .map((p) => (
                <li
                  key={p.user_id}
                  style={{
                    padding: "0.4rem 0",
                    borderBottom: "1px solid var(--border, #222)",
                    fontSize: 13,
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 8,
                  }}
                >
                  <span>
                    {ROLE_EMOJI[p.role] || ""} <strong>{p.first_name}</strong>{" "}
                    <small style={{ color: "var(--muted)" }}>
                      ({t(`role-${p.role}`, { defaultValue: p.role })})
                    </small>
                  </span>
                  <span style={{ whiteSpace: "nowrap", textAlign: "right" }}>
                    {p.alive ? (
                      <span style={{ color: "#4ade80" }}>
                        ✓ {t("webapp.history.detail.alive")}
                      </span>
                    ) : (
                      <span style={{ color: "#e74c3c" }}>
                        💀 {t("webapp.history.detail.round_short")}
                        {p.died_at_round ?? ""}
                        {p.died_reason ? (
                          <small style={{ color: "var(--muted)", display: "block" }}>
                            {t(`webapp.history.detail.death_reason.${p.died_reason}`, {
                              defaultValue: p.died_reason,
                            })}
                          </small>
                        ) : null}
                      </span>
                    )}
                  </span>
                </li>
              ))}
          </ul>
        </details>
      )}

      {/* === Per-round breakdown === */}
      {rounds.length === 0 && (
        <div
          className="webapp-section"
          style={{ marginTop: "0.5rem", textAlign: "center", color: "var(--muted)" }}
        >
          {t("webapp.history.detail.no_rounds")}
        </div>
      )}
      {rounds.map((r) => (
        <RoundCard
          key={r.round_num}
          round={r}
          nameOf={nameOf}
          labelOf={labelOf}
          roleNameOf={roleNameOf}
        />
      ))}
    </>
  );
}

interface RoundCardProps {
  round: GameHistoryRound;
  nameOf: (id: number) => string;
  labelOf: (id: number) => string;
  roleNameOf: (id: number) => string;
}

function RoundCard({ round, nameOf, labelOf, roleNameOf }: RoundCardProps) {
  const { t } = useTranslation();

  const actions = round.night_actions ?? [];
  const votes = round.day_votes ?? [];
  const deaths = round.night_deaths ?? [];
  const lastWords = round.last_words ?? {};
  const hasLastWords = Object.keys(lastWords).length > 0;

  const hc = round.extra?.hanging_confirm;
  const yesVoters = Object.entries(hc?.yes ?? {});
  const noVoters = Object.entries(hc?.no ?? {});
  const hasConfirm = yesVoters.length > 0 || noVoters.length > 0;

  return (
    <details className="webapp-section" style={{ marginTop: "0.5rem" }}>
      <summary style={{ cursor: "pointer", color: "var(--accent)", fontWeight: 600 }}>
        {t("webapp.history.detail.round_label")} #{round.round_num}
        {round.hanged ? (
          <span style={{ color: "#f0a020", fontWeight: 400 }}>
            {" "}
            — ⚖️ {nameOf(round.hanged)}
          </span>
        ) : null}
      </summary>

      <div style={{ marginTop: "0.4rem", fontSize: 13 }}>
        {/* Night actions — who targeted whom */}
        {actions.length > 0 && (
          <div>
            <strong>🌙 {t("webapp.history.detail.actions")}:</strong>
            <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
              {actions.map((a, i) => (
                <li key={i}>
                  {labelOf(a.actor_id)} →{" "}
                  {t(`live.action_${a.action_type}`, { defaultValue: a.action_type })}
                  {a.target_id ? ` → ${labelOf(a.target_id)}` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Day votes */}
        {votes.length > 0 && (
          <div>
            <strong>🗳 {t("webapp.history.detail.votes")}:</strong>
            <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
              {votes.map((v, i) => (
                <li key={i}>
                  {nameOf(v.voter_id)} →{" "}
                  {v.target_id
                    ? nameOf(v.target_id)
                    : t("webapp.history.detail.nobody")}
                  {v.weight > 1 ? ` (×${v.weight})` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Hanging confirmation — who pressed 👍 / 👎 */}
        {hasConfirm && (
          <div style={{ marginTop: 4 }}>
            <strong>⚖️ {t("admin.live.section_hanging_confirm")}:</strong>
            {hc?.target_id ? (
              <span style={{ color: "var(--muted)" }}> → {nameOf(hc.target_id)}</span>
            ) : null}
            <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
              {yesVoters.map(([uid, w]) => (
                <li key={`y-${uid}`} style={{ color: "#4ade80" }}>
                  👍 {nameOf(parseInt(uid, 10))}
                  {w > 1 ? ` (×${w})` : ""}
                </li>
              ))}
              {noVoters.map(([uid, w]) => (
                <li key={`n-${uid}`} style={{ color: "#e74c3c" }}>
                  👎 {nameOf(parseInt(uid, 10))}
                  {w > 1 ? ` (×${w})` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Night deaths */}
        {deaths.length > 0 && (
          <div style={{ color: "#e74c3c" }}>
            <strong>💀 {t("webapp.history.detail.deaths")}:</strong>{" "}
            {deaths.map((id) => `${nameOf(id)} (${roleNameOf(id)})`).join(", ")}
          </div>
        )}

        {/* Hanged */}
        {round.hanged ? (
          <div style={{ color: "#f0a020", marginTop: 4 }}>
            <strong>⚖️ {t("webapp.history.detail.hanged")}:</strong>{" "}
            {labelOf(round.hanged)}
          </div>
        ) : null}

        {/* Last words */}
        {hasLastWords && (
          <div style={{ marginTop: 8 }}>
            <strong>💬 {t("webapp.history.detail.last_words")}:</strong>
            {Object.entries(lastWords).map(([uid, words]) => (
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
                <strong>{nameOf(parseInt(uid, 10))}:</strong> {words}
              </blockquote>
            ))}
          </div>
        )}

        {actions.length === 0 &&
          votes.length === 0 &&
          deaths.length === 0 &&
          !hasConfirm &&
          !round.hanged &&
          !hasLastWords && (
            <div style={{ color: "var(--muted)" }}>
              {t("webapp.history.detail.round_empty")}
            </div>
          )}
      </div>
    </details>
  );
}
