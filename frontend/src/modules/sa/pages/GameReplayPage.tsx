/**
 * Unified game replay page.
 *
 * Combined from admin/GameReplayPage (wide tables with full round
 * breakdowns) and webapp/SaGameReplayPage (compact `<details>`
 * stack with role-emoji role names). Both shells dehydrate the
 * same Redis-derived `Game.history` JSON.
 *
 * Surface picks visual chrome — `admin-card` + `admin-table` on the
 * desktop, `webapp-section` + collapsible `<details>` panels on the
 * Mini App. Round display is shared; only the player roster
 * differs (table vs list).
 */

import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { superAdminApi } from "@shared/api/superAdmin";

import { useSa, useSaPath } from "../context";

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

interface Player {
  user_id: number;
  username?: string | null;
  first_name: string;
  role: string;
  team: string;
  alive: boolean;
  join_order?: number;
  died_at_round?: number | null;
  died_at_phase?: string | null;
  died_reason?: string | null;
}

interface Round {
  round_num: number;
  night_actions?: Array<{
    role: string;
    actor_id: number;
    action_type: string;
    target_id: number | null;
  }>;
  night_deaths?: number[];
  day_votes?: Array<{ voter_id: number; target_id: number; weight: number }>;
  hanged?: number | null;
  last_words?: Record<string, string>;
}

interface History {
  players?: Player[];
  rounds?: Round[];
  winner_team?: string;
  winner_user_ids?: number[];
  final_alive?: number[];
}

export function GameReplayPage() {
  const { t } = useTranslation();
  const { gameId } = useParams();
  const { surface } = useSa();
  const isAdmin = surface === "admin";
  const gamesBase = useSaPath("/games");
  const userBase = useSaPath("/users");

  const { data: game, isLoading } = useQuery({
    queryKey: ["sa-game", gameId],
    queryFn: () => superAdminApi.game(gameId!),
    enabled: !!gameId,
  });

  const cardCls = isAdmin ? "admin-card" : "webapp-section";

  if (isLoading) {
    return <div className={cardCls}>⏳</div>;
  }
  if (!game) {
    return (
      <div className={cardCls}>
        {t("admin.common.game_not_found", "Game not found")}
      </div>
    );
  }

  const hist = (game.history || {}) as History;
  const players = hist.players || [];
  const rounds = hist.rounds || [];

  const playerById = new Map<number, Player>();
  players.forEach((p) => playerById.set(p.user_id, p));

  const nameOf = (id: number) =>
    playerById.get(id)?.first_name ?? `#${String(id)}`;
  const playerName = (id: number) => {
    const p = playerById.get(id);
    return p ? `${ROLE_EMOJI[p.role] || ""} ${p.first_name}` : `#${String(id)}`;
  };
  const roleOf = (id: number) => {
    const r = playerById.get(id)?.role;
    return r ? t(`role-${r}`, { defaultValue: r }) : "?";
  };

  const duration =
    game.started_at && game.finished_at
      ? Math.round(
          (new Date(game.finished_at).getTime() -
            new Date(game.started_at).getTime()) /
            60000,
        )
      : null;

  return (
    <>
      <div style={{ marginBottom: "0.5rem" }}>
        <Link to={gamesBase} style={{ color: "var(--muted)" }}>
          ← {t("sa.games.title", "Games")}
        </Link>
      </div>

      {isAdmin ? (
        <h1 className="admin-page-title">
          🎬 {t("admin.game_replay_extra.title", "Game replay")}
        </h1>
      ) : (
        <>
          <h2 style={{ margin: "0.5rem 0" }}>
            🎬 {t("sa.game_replay.title", "Game replay")}
          </h2>
          <p style={{ margin: 0, color: "var(--muted)", fontSize: 13 }}>
            <code>{game.id}</code>
          </p>
        </>
      )}

      {/* === Summary panel === */}
      {isAdmin ? (
        <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
          <KPI
            label={t("admin.game_replay_extra.status", "Status")}
            value={game.status}
          />
          <KPI
            label={t("admin.game_replay_extra.winner", "Winner")}
            value={game.winner_team || "—"}
          />
          {/* Telegram group IDs are identifiers — no thousand separators */}
          <KPI
            label={t("admin.game_replay_extra.group", "Group")}
            value={String(game.group_id)}
          />
          <KPI
            label={t("admin.game_replay_extra.duration", "Duration")}
            value={
              duration
                ? `${duration} ${t("admin.game_replay_extra.duration_unit", "min")}`
                : "—"
            }
          />
          {game.bounty_per_winner != null && (
            <KPI
              label={t("admin.game_replay_extra.bounty", "Bounty")}
              value={`💎 ${game.bounty_per_winner}`}
              sub={`${t("admin.game_replay_extra.pool", "Pool")} ${game.bounty_pool ?? "—"}`}
            />
          )}
        </div>
      ) : (
        <div className="webapp-section" style={{ marginTop: "0.5rem" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 8,
            }}
          >
            <Stat
              label={t("sa.games.col_status", "Status")}
              value={game.status}
            />
            <Stat
              label={t("sa.game_replay.winner", "Winner")}
              value={
                game.winner_team
                  ? t(`sa.games.winner_${game.winner_team}`, {
                      defaultValue: game.winner_team,
                    })
                  : "—"
              }
            />
            <Stat
              label={t("sa.game_replay.players", "Players")}
              value={players.length}
            />
            <Stat
              label={t("sa.game_replay.rounds", "Rounds")}
              value={rounds.length}
            />
          </div>
        </div>
      )}

      {/* === Player roster === */}
      {players.length > 0 && (
        <>
          {isAdmin ? (
            <>
              <h3 style={{ color: "var(--muted)" }}>
                {t("admin.game_replay_extra.players_count", "Players")} (
                {players.length})
              </h3>
              <div
                className="admin-card"
                style={{
                  padding: 0,
                  overflow: "hidden",
                  marginBottom: "1.5rem",
                }}
              >
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>{t("admin.game_replay.col_order", "#")}</th>
                      <th>{t("admin.game_replay.col_player", "Player")}</th>
                      <th>{t("admin.game_replay.col_role", "Role")}</th>
                      <th>{t("admin.game_replay.col_team", "Team")}</th>
                      <th>{t("admin.game_replay.col_state", "State")}</th>
                      <th>
                        {t(
                          "admin.game_replay.col_death_reason",
                          "Death reason",
                        )}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {players
                      .slice()
                      .sort(
                        (a, b) =>
                          (a.join_order ?? 0) - (b.join_order ?? 0),
                      )
                      .map((p) => (
                        <tr key={p.user_id}>
                          <td>{p.join_order ?? "—"}</td>
                          <td>
                            <Link to={`${userBase}/${p.user_id}`}>
                              {p.first_name}
                            </Link>
                          </td>
                          <td>
                            {ROLE_EMOJI[p.role]} {p.role}
                          </td>
                          <td>{p.team}</td>
                          <td>
                            {p.alive ? (
                              <span className="badge green">
                                {t("admin.game_replay.alive", "Alive")}
                              </span>
                            ) : (
                              <span className="badge red">
                                💀 {t("admin.live.round_short", "R")}
                                {p.died_at_round ?? ""}
                              </span>
                            )}
                          </td>
                          <td
                            style={{
                              color: "var(--muted)",
                              fontSize: "0.85rem",
                            }}
                          >
                            {p.died_reason || "—"}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <details
              open
              className="webapp-section"
              style={{ marginTop: "0.5rem" }}
            >
              <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
                👥 {t("sa.game_replay.section_players", "Players")} (
                {players.length})
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
                        <span style={{ color: "#e74c3c" }}>
                          💀 R{p.died_at_round ?? ""}
                        </span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}

      {/* === Per-round breakdown === */}
      {isAdmin ? (
        <h3 style={{ color: "var(--muted)" }}>
          {t("admin.game_replay_extra.rounds_count", "Rounds")} ({rounds.length})
        </h3>
      ) : null}
      {rounds.map((r) => (
        <RoundCard
          key={r.round_num}
          round={r}
          isAdmin={isAdmin}
          nameOf={nameOf}
          playerName={playerName}
          roleOf={roleOf}
        />
      ))}
    </>
  );
}

// === Round card (per-round breakdown, surface-aware) ===

interface RoundCardProps {
  round: Round;
  isAdmin: boolean;
  nameOf: (id: number) => string;
  playerName: (id: number) => string;
  roleOf: (id: number) => string;
}

function RoundCard({ round, isAdmin, nameOf, playerName, roleOf }: RoundCardProps) {
  const { t } = useTranslation();

  if (isAdmin) {
    return (
      <div className="admin-card" style={{ marginBottom: "1rem" }}>
        <h3 style={{ marginTop: 0, color: "var(--accent)" }}>
          {t("admin.game_replay_extra.round_label", "Round")} #{round.round_num}
        </h3>

        {round.night_actions && round.night_actions.length > 0 && (
          <>
            <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>
              {t("admin.game_replay_extra.actions", "Actions")}
            </h4>
            <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
              {round.night_actions.map((a, idx) => (
                <li key={idx}>
                  <code style={{ color: "var(--accent)" }}>{a.role}</code> (
                  {playerName(a.actor_id)}) <code>{a.action_type}</code>{" "}
                  {a.target_id !== null && a.target_id !== 0
                    ? `→ ${playerName(a.target_id)}`
                    : ""}
                </li>
              ))}
            </ul>
          </>
        )}

        {round.night_deaths && round.night_deaths.length > 0 && (
          <>
            <h4 style={{ color: "#e74c3c", margin: "0.5rem 0" }}>
              {t("admin.game_replay_extra.deaths", "Deaths")}
            </h4>
            <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
              {round.night_deaths.map((id) => (
                <li key={id}>{playerName(id)}</li>
              ))}
            </ul>
          </>
        )}

        {round.day_votes && round.day_votes.length > 0 && (
          <>
            <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>
              {t("admin.game_replay_extra.votes", "Votes")}
            </h4>
            <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
              {round.day_votes.map((v, idx) => (
                <li key={idx}>
                  {playerName(v.voter_id)} →{" "}
                  {v.target_id
                    ? playerName(v.target_id)
                    : t("admin.game_replay_extra.nobody", "(nobody)")}{" "}
                  {v.weight > 1 && `(×${v.weight})`}
                </li>
              ))}
            </ul>
          </>
        )}

        {round.hanged && (
          <div style={{ marginTop: "0.5rem", color: "#f0a020" }}>
            {t("admin.game_replay_extra.hanged_label", "Hanged")}:{" "}
            {playerName(round.hanged)}
          </div>
        )}

        {round.last_words && Object.keys(round.last_words).length > 0 && (
          <>
            <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>
              {t("admin.game_replay_extra.last_words", "Last words")}
            </h4>
            {Object.entries(round.last_words).map(([uid, words]) => (
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
                <strong>{playerName(parseInt(uid))}:</strong> {words}
              </blockquote>
            ))}
          </>
        )}
      </div>
    );
  }

  // Mini-App: collapsible <details> stack
  return (
    <details
      key={round.round_num}
      className="webapp-section"
      style={{ marginTop: "0.5rem" }}
    >
      <summary
        style={{
          cursor: "pointer",
          color: "var(--accent)",
          fontWeight: 600,
        }}
      >
        {t("admin.live.round_label", "Round")} #{round.round_num}
        {round.hanged && (
          <span style={{ color: "#f0a020", fontWeight: 400 }}>
            {" "}
            — ⚖️ {nameOf(round.hanged)}
          </span>
        )}
      </summary>
      <div style={{ marginTop: "0.4rem", fontSize: 13 }}>
        {round.night_actions && round.night_actions.length > 0 && (
          <div>
            <strong>🌙 {t("admin.live.actions", "Actions")}:</strong>
            <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
              {round.night_actions.map((a, i) => (
                <li key={i}>
                  {t(`role-${a.role}`, { defaultValue: a.role })} (
                  {nameOf(a.actor_id)}) →{" "}
                  {t(`live.action_${a.action_type}`, {
                    defaultValue: a.action_type,
                  })}
                  {a.target_id ? ` → ${nameOf(a.target_id)}` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}
        {round.day_votes && round.day_votes.length > 0 && (
          <div>
            <strong>🗳 {t("admin.live.votes", "Votes")}:</strong>
            <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
              {round.day_votes.map((v, i) => (
                <li key={i}>
                  {nameOf(v.voter_id)} →{" "}
                  {v.target_id
                    ? nameOf(v.target_id)
                    : t("admin.live.nobody", "(nobody)")}
                  {v.weight > 1 && ` (×${v.weight})`}
                </li>
              ))}
            </ul>
          </div>
        )}
        {round.night_deaths && round.night_deaths.length > 0 && (
          <div style={{ color: "#e74c3c" }}>
            <strong>💀 {t("admin.live.deaths", "Deaths")}:</strong>{" "}
            {round.night_deaths
              .map((id) => `${nameOf(id)} (${roleOf(id)})`)
              .join(", ")}
          </div>
        )}
        {round.last_words && Object.keys(round.last_words).length > 0 && (
          <div style={{ marginTop: 8 }}>
            <strong>💬 {t("admin.live.last_words", "Last words")}:</strong>
            {Object.entries(round.last_words).map(([uid, words]) => (
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
  );
}

// === Small presentational helpers ===

function KPI({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="admin-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" style={{ fontSize: "1.5rem" }}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.03)",
        padding: "0.5rem",
        borderRadius: 6,
      }}
    >
      <div style={{ fontSize: 11, color: "var(--muted)" }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
