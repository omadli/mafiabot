import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "@shared/api/client";

interface GameDetail {
  id: string;
  group_id: number;
  status: string;
  winner_team: string | null;
  started_at: string | null;
  finished_at: string | null;
  bounty_per_winner: number | null;
  bounty_pool: number | null;
  history: {
    players?: Player[];
    rounds?: Round[];
    final_alive?: number[];
    winner_team?: string;
    winner_user_ids?: number[];
  };
  settings_snapshot: any;
}

interface Player {
  user_id: number;
  username: string | null;
  first_name: string;
  role: string;
  team: string;
  alive: boolean;
  join_order: number;
  died_at_round: number | null;
  died_at_phase: string | null;
  died_reason: string | null;
}

interface Round {
  round_num: number;
  night_actions?: Array<{
    actor_id: number;
    role: string;
    action_type: string;
    target_id: number | null;
  }>;
  night_deaths?: number[];
  day_votes?: Array<{ voter_id: number; target_id: number; weight: number }>;
  hanged?: number | null;
  last_words?: Record<string, string>;
}

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

export function GameReplayPage() {
  const { gameId } = useParams();

  const { data: game, isLoading } = useQuery({
    queryKey: ["game", gameId],
    queryFn: async () =>
      (await api.get<GameDetail>(`/admin/games/${gameId}`)).data,
    enabled: !!gameId,
  });

  if (isLoading) return <div className="admin-card">⏳</div>;
  if (!game) return <div className="admin-card">Not found</div>;

  const playerById = new Map<number, Player>();
  (game.history.players || []).forEach((p) => playerById.set(p.user_id, p));

  const playerName = (id: number) => {
    const p = playerById.get(id);
    return p ? `${ROLE_EMOJI[p.role] || ""} ${p.first_name}` : `#${id}`;
  };

  const duration =
    game.started_at && game.finished_at
      ? Math.round(
          (new Date(game.finished_at).getTime() - new Date(game.started_at).getTime()) / 60000,
        )
      : null;

  return (
    <>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/admin/games" style={{ color: "var(--muted)" }}>
          ← O'yinlar
        </Link>
      </div>
      <h1 className="admin-page-title">🎬 Game replay</h1>

      <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
        <KPI label="Status" value={game.status} />
        <KPI label="Winner" value={game.winner_team || "—"} />
        <KPI label="Group" value={game.group_id} />
        <KPI label="Davomiyligi" value={duration ? `${duration} daq` : "—"} />
        {game.bounty_per_winner && (
          <KPI label="Bounty" value={`💎 ${game.bounty_per_winner}`} sub={`pool ${game.bounty_pool}`} />
        )}
      </div>

      <h3 style={{ color: "var(--muted)" }}>O'yinchilar ({game.history.players?.length || 0})</h3>
      <div className="admin-card" style={{ padding: 0, overflow: "hidden", marginBottom: "1.5rem" }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>#</th>
              <th>O'yinchi</th>
              <th>Rol</th>
              <th>Tomon</th>
              <th>Holat</th>
              <th>O'lim sababi</th>
            </tr>
          </thead>
          <tbody>
            {(game.history.players || [])
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
                      <span className="badge green">ALIVE</span>
                    ) : (
                      <span className="badge red">💀 R{p.died_at_round}</span>
                    )}
                  </td>
                  <td style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                    {p.died_reason || "—"}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <h3 style={{ color: "var(--muted)" }}>Tunlar ({game.history.rounds?.length || 0})</h3>
      {(game.history.rounds || []).map((round) => (
        <div key={round.round_num} className="admin-card" style={{ marginBottom: "1rem" }}>
          <h3 style={{ marginTop: 0, color: "var(--accent)" }}>🌃 Tun #{round.round_num}</h3>

          {round.night_actions && round.night_actions.length > 0 && (
            <>
              <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>Harakatlar</h4>
              <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
                {round.night_actions.map((a, idx) => (
                  <li key={idx}>
                    <code style={{ color: "var(--accent)" }}>{a.role}</code> ({playerName(a.actor_id)}){" "}
                    <code>{a.action_type}</code>{" "}
                    {a.target_id !== null && a.target_id !== 0 ? `→ ${playerName(a.target_id)}` : ""}
                  </li>
                ))}
              </ul>
            </>
          )}

          {round.night_deaths && round.night_deaths.length > 0 && (
            <>
              <h4 style={{ color: "#e74c3c", margin: "0.5rem 0" }}>💀 O'limlar</h4>
              <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
                {round.night_deaths.map((id) => (
                  <li key={id}>{playerName(id)}</li>
                ))}
              </ul>
            </>
          )}

          {round.day_votes && round.day_votes.length > 0 && (
            <>
              <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>🗳 Ovozlar</h4>
              <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
                {round.day_votes.map((v, idx) => (
                  <li key={idx}>
                    {playerName(v.voter_id)} → {v.target_id ? playerName(v.target_id) : "Hech kim"}{" "}
                    {v.weight > 1 && `(×${v.weight})`}
                  </li>
                ))}
              </ul>
            </>
          )}

          {round.hanged && (
            <div style={{ marginTop: "0.5rem", color: "#f0a020" }}>
              ⚖️ Osildi: {playerName(round.hanged)}
            </div>
          )}

          {round.last_words && Object.keys(round.last_words).length > 0 && (
            <>
              <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>🪦 So'nggi so'zlar</h4>
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
      ))}
    </>
  );
}

function KPI({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
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
