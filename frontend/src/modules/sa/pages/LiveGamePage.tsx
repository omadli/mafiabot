/**
 * Unified live game spectator page.
 *
 * Combined from admin/AdminLiveGamePage (wide table for player
 * roster, vote tally panels) and webapp/SaLiveGamePage (compact
 * `<details>` stacks, role-emoji map from SA role-configs). Both
 * shells render the same Redis-derived `LiveGameState` via
 * `useLiveGame` — the shared hook picks the JWT WebSocket on
 * `/admin/*` and the initData WebSocket on `/webapp/sa/*` based
 * on auth-store presence.
 *
 * Surface drives layout only: `admin-card` + `admin-table` for the
 * desktop shell, collapsible `webapp-section` panels for the Mini
 * App. Round breakdown is shared via `RoundCard`.
 */

import { Link, useParams } from "react-router-dom";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { superAdminApi } from "@shared/api/superAdmin";
import { ROLE_EMOJI, PHASE_EMOJI } from "@shared/constants/roles";

import { useCountdown } from "../hooks/useCountdown";
import { useLiveGame, type LiveGameState } from "../hooks/useLiveGame";
import { useSa, useSaPath } from "../context";

/**
 * Build a role→emoji map from SA-editable role configs, falling
 * back to the hard-coded ROLE_EMOJI for any role the configs
 * haven't been edited for. The webapp originally pulled this map
 * from role-configs; the admin used the hard-coded table. We do
 * both so super-admin emoji edits show up immediately.
 */
function useRoleEmojiMap(): Record<string, string> {
  const { data } = useQuery({
    queryKey: ["sa-role-configs"],
    queryFn: superAdminApi.roleConfigs,
    staleTime: 60_000,
  });
  return useMemo(() => {
    const out: Record<string, string> = { ...ROLE_EMOJI };
    (data?.items ?? []).forEach((c) => {
      if (c.static_emoji) out[c.role] = c.static_emoji;
    });
    return out;
  }, [data]);
}

function nameOf(
  data: LiveGameState,
  id: number,
  emojiMap: Record<string, string>,
): string {
  const p = data.players.find((x) => x.user_id === id);
  if (!p) return `#${String(id)}`;
  return `${emojiMap[p.role] || ""} ${p.first_name}`;
}

export function LiveGamePage() {
  const { t } = useTranslation();
  const { groupId } = useParams();
  const { surface } = useSa();
  const isAdmin = surface === "admin";
  const groupsBase = useSaPath("/groups");
  const groupDetailBack = useSaPath(`/groups/${groupId ?? "0"}`);

  const gid = parseInt(groupId || "0");
  const { data, isLoading, error, wsConnected, ended } = useLiveGame(gid);
  const remaining = useCountdown(data?.phase_ends_at ?? null);
  const emojiMap = useRoleEmojiMap();

  const cardCls = isAdmin ? "admin-card" : "webapp-section";

  if (isLoading) return <div className={cardCls}>⏳</div>;

  if (error || !data) {
    // Webapp comes from a group's detail page; admin comes from the groups list.
    const backTo = isAdmin ? groupsBase : groupDetailBack;
    return (
      <>
        <Link to={backTo} style={{ color: "var(--muted)" }}>
          ← {t("admin.live.back_to_groups", "Back to groups")}
        </Link>
        <div className={cardCls}>
          <h3 style={{ marginTop: "1rem" }}>
            {t("admin.live.no_active_game", "No active game")}
          </h3>
          <p style={{ color: "var(--muted)" }}>
            {t("admin.live.no_active_hint", "There's no game in progress.")}
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <div style={{ marginBottom: "0.5rem" }}>
        <Link
          to={isAdmin ? groupsBase : groupDetailBack}
          style={{ color: "var(--muted)" }}
        >
          ← {t("admin.live.back_to_groups", "Back to groups")}
        </Link>
      </div>

      {isAdmin ? (
        <h1 className="admin-page-title">
          🎥 {t("admin.live.title", "Live")} —{" "}
          {t("admin.live.group_label", "Group")} #{String(data.group_id)}
        </h1>
      ) : (
        <h2 style={{ margin: "0.5rem 0" }}>
          🎥 {t("admin.live.title", "Live")} #{String(data.group_id)}
        </h2>
      )}

      <div
        style={{
          marginBottom: "1.5rem",
          fontSize: "0.85rem",
          color: wsConnected ? "#27ae60" : "var(--muted)",
        }}
      >
        {wsConnected ? "🟢" : "⚪"} {t("admin.live.ws_status", "WebSocket")}{" "}
        {ended && (
          <span style={{ color: "#e74c3c" }}>
            • {t("admin.live.game_ended", "Game ended")}
          </span>
        )}
      </div>

      {/* === Summary KPI panel === */}
      {isAdmin ? (
        <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
          <KPI
            label={t("admin.live.phase", "Phase")}
            value={`${PHASE_EMOJI[data.phase] || ""} ${data.phase}`}
          />
          <KPI
            label={t("admin.live.round", "Round")}
            value={`#${data.round_num}`}
          />
          <KPI
            label={t("admin.live.timer", "Timer")}
            value={
              data.phase_ends_at
                ? `${Math.floor(remaining / 60)
                    .toString()
                    .padStart(2, "0")}:${(remaining % 60)
                    .toString()
                    .padStart(2, "0")}`
                : "—"
            }
          />
          <KPI
            label={t("admin.live.alive", "Alive")}
            value={`${data.players.filter((p) => p.alive).length} / ${data.players.length}`}
          />
        </div>
      ) : (
        <div className="webapp-section" style={{ marginTop: "0.5rem" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "0.5rem",
              fontSize: "0.9rem",
            }}
          >
            <SmallKPI
              label={t("admin.live.phase", "Phase")}
              value={`${PHASE_EMOJI[data.phase] || ""} ${t(
                `live.phase_${data.phase}`,
                {
                  defaultValue: data.phase,
                },
              )}`}
            />
            <SmallKPI
              label={t("admin.live.round", "Round")}
              value={`#${data.round_num}`}
            />
            <SmallKPI
              label={t("admin.live.timer", "Timer")}
              value={
                data.phase_ends_at
                  ? `${Math.floor(remaining / 60)
                      .toString()
                      .padStart(2, "0")}:${(remaining % 60)
                      .toString()
                      .padStart(2, "0")}`
                  : "—"
              }
            />
            <SmallKPI
              label={t("admin.live.alive", "Alive")}
              value={`${data.players.filter((p) => p.alive).length} / ${data.players.length}`}
            />
          </div>
        </div>
      )}

      <PlayersPanel data={data} surface={surface} emojiMap={emojiMap} />
      <CurrentActionsPanel data={data} surface={surface} emojiMap={emojiMap} />
      <CurrentVotesPanel data={data} surface={surface} emojiMap={emojiMap} />
      <HangingConfirmPanel data={data} surface={surface} emojiMap={emojiMap} />
      <RoundsHistoryPanel data={data} surface={surface} emojiMap={emojiMap} />
    </>
  );
}

// === Panels ===

function PlayersPanel({
  data,
  surface,
  emojiMap,
}: {
  data: LiveGameState;
  surface: "admin" | "webapp";
  emojiMap: Record<string, string>;
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const userBase = useSaPath("/users");
  // Roles are placeholder ("citizen") during registration — only show
  // the real role column after start_game().
  const isRegistration = data.phase === "waiting" || data.round_num === 0;

  if (isAdmin) {
    return (
      <>
        <h3 style={{ color: "var(--muted)" }}>
          {isRegistration
            ? `${t("admin.live.section_registering", "Registering")} (${data.players.length})`
            : `${t("admin.live.section_players", "Players")} (${data.players.length})`}
        </h3>
        <div
          className="admin-card"
          style={{ padding: 0, overflow: "hidden", marginBottom: "1.5rem" }}
        >
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>{t("admin.live.col_player", "Player")}</th>
                <th>{t("admin.live.col_role", "Role")}</th>
                <th>{t("admin.live.col_team", "Team")}</th>
                <th>{t("admin.live.col_alive", "Alive")}</th>
                <th>{t("admin.live.col_items", "Items")}</th>
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
                      <Link to={`${userBase}/${p.user_id}`}>{p.first_name}</Link>
                    </td>
                    <td>
                      {isRegistration ? (
                        <span style={{ color: "var(--muted)" }}>
                          📝 {t("admin.live.role_pending", "Pending")}
                        </span>
                      ) : (
                        <>
                          {emojiMap[p.role]} {p.role}
                        </>
                      )}
                    </td>
                    <td>{isRegistration ? "—" : p.team}</td>
                    <td>
                      {isRegistration ? (
                        <span className="badge">
                          ⏳ {t("admin.live.registering", "Registering")}
                        </span>
                      ) : p.alive ? (
                        <span className="badge green">
                          {t("admin.live.alive_yes", "Alive")}
                        </span>
                      ) : (
                        <span className="badge red">
                          💀 {t("admin.live.round_short", "R")}
                          {p.died_at_round}
                        </span>
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

  return (
    <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
      <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
        {t("admin.live.section_players", "Players")} ({data.players.length})
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
                {p.join_order}. {emojiMap[p.role] || ""}{" "}
                <strong>{p.first_name}</strong>{" "}
                <small style={{ color: "var(--muted)" }}>
                  ({t(`role-${p.role}`, { defaultValue: p.role })})
                </small>
              </span>
              <span style={{ fontSize: "0.75rem" }}>
                {p.alive ? (
                  <span style={{ color: "#4ade80" }}>
                    ✓ {t("admin.live.alive_yes", "Alive")}
                  </span>
                ) : (
                  <span style={{ color: "#e74c3c" }}>
                    💀 {t("admin.live.round_short", "R")}
                    {p.died_at_round}
                  </span>
                )}
              </span>
            </li>
          ))}
      </ul>
    </details>
  );
}

function CurrentActionsPanel({
  data,
  surface,
  emojiMap,
}: {
  data: LiveGameState;
  surface: "admin" | "webapp";
  emojiMap: Record<string, string>;
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const entries = Object.entries(data.current_actions);
  if (data.phase !== "night" && entries.length === 0) return null;

  if (isAdmin) {
    return (
      <>
        <h3 style={{ color: "var(--muted)" }}>
          🌙 {t("admin.live.section_current_actions", "Current actions")} ({entries.length})
        </h3>
        <div className="admin-card" style={{ marginBottom: "1.5rem" }}>
          {entries.length === 0 ? (
            <p style={{ color: "var(--muted)", margin: 0 }}>
              {t("admin.live.no_actions_yet", "No actions yet")}
            </p>
          ) : (
            <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.92rem" }}>
              {entries.map(([uid, a]) => {
                const actor = data.players.find(
                  (p) => p.user_id === parseInt(uid),
                );
                return (
                  <li key={uid}>
                    <code style={{ color: "var(--accent)" }}>{actor?.role}</code>{" "}
                    ({actor?.first_name}) <code>{a.action_type}</code>{" "}
                    {a.target_id !== null && a.target_id !== 0
                      ? `→ ${nameOf(data, a.target_id, emojiMap)}`
                      : ""}
                    {a.used_item && (
                      <span style={{ color: "var(--muted)" }}>
                        {" "}
                        [item: {a.used_item}]
                      </span>
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

  if (entries.length === 0) return null;
  return (
    <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
      <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
        🌙 {t("admin.live.section_current_actions", "Current actions")} ({entries.length})
      </summary>
      <ul style={{ margin: "0.5rem 0 0 1.2rem", fontSize: "0.85rem" }}>
        {entries.map(([uid, a]) => {
          const actor = data.players.find((p) => p.user_id === parseInt(uid));
          return (
            <li key={uid}>
              <strong>{actor?.first_name}</strong> (
              {actor?.role
                ? t(`role-${actor.role}`, { defaultValue: actor.role })
                : ""}
              ) →{" "}
              {t(`live.action_${a.action_type}`, {
                defaultValue: a.action_type,
              })}{" "}
              {a.target_id !== null && a.target_id !== 0
                ? `→ ${nameOf(data, a.target_id, emojiMap)}`
                : ""}
            </li>
          );
        })}
      </ul>
    </details>
  );
}

function CurrentVotesPanel({
  data,
  surface,
  emojiMap,
}: {
  data: LiveGameState;
  surface: "admin" | "webapp";
  emojiMap: Record<string, string>;
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const entries = Object.values(data.current_votes);
  if (data.phase !== "voting" && entries.length === 0) return null;

  const tally = new Map<number, number>();
  for (const v of entries) {
    tally.set(v.target_id, (tally.get(v.target_id) || 0) + v.weight);
  }
  const sortedTally = [...tally.entries()].sort((a, b) => b[1] - a[1]);

  if (isAdmin) {
    return (
      <>
        <h3 style={{ color: "var(--muted)" }}>
          🗳 {t("admin.live.section_current_votes", "Current votes")} ({entries.length})
        </h3>
        <div className="admin-card" style={{ marginBottom: "1.5rem" }}>
          {entries.length === 0 ? (
            <p style={{ color: "var(--muted)", margin: 0 }}>
              {t("admin.live.no_votes_yet", "No votes yet")}
            </p>
          ) : (
            <>
              <h4 style={{ margin: "0 0 0.5rem 0", color: "var(--muted)" }}>
                {t("admin.live.tally", "Tally")}
              </h4>
              <ul
                style={{
                  margin: "0 0 1rem 0",
                  paddingLeft: "1.5rem",
                  fontSize: "0.92rem",
                }}
              >
                {sortedTally.map(([tid, count]) => (
                  <li key={tid}>
                    <strong>
                      {tid === 0
                        ? t("admin.live.nobody", "(nobody)")
                        : nameOf(data, tid, emojiMap)}
                      :
                    </strong>{" "}
                    {count}
                  </li>
                ))}
              </ul>
              <h4 style={{ margin: "0 0 0.5rem 0", color: "var(--muted)" }}>
                {t("admin.live.individual_votes", "Individual votes")}
              </h4>
              <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.9rem" }}>
                {entries.map((v, i) => (
                  <li key={i}>
                    {nameOf(data, v.voter_id, emojiMap)} →{" "}
                    {v.target_id === 0
                      ? t("admin.live.nobody", "(nobody)")
                      : nameOf(data, v.target_id, emojiMap)}{" "}
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

  if (entries.length === 0) return null;
  return (
    <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
      <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
        🗳 {t("admin.live.section_current_votes", "Current votes")} ({entries.length})
      </summary>
      <ul style={{ margin: "0.5rem 0 0 1.2rem", fontSize: "0.85rem" }}>
        {sortedTally.map(([tid, count]) => (
          <li key={tid}>
            <strong>
              {tid === 0
                ? t("admin.live.nobody", "(nobody)")
                : nameOf(data, tid, emojiMap)}
            </strong>
            : {count}
          </li>
        ))}
      </ul>
      <details style={{ marginTop: "0.5rem" }}>
        <summary
          style={{ cursor: "pointer", color: "var(--muted)", fontSize: "0.8rem" }}
        >
          {t("admin.live.individual_votes", "Individual votes")}
        </summary>
        <ul style={{ margin: "0.3rem 0 0 1.2rem", fontSize: "0.8rem" }}>
          {entries.map((v, i) => (
            <li key={i}>
              {nameOf(data, v.voter_id, emojiMap)} →{" "}
              {v.target_id === 0
                ? t("admin.live.nobody", "(nobody)")
                : nameOf(data, v.target_id, emojiMap)}{" "}
              {v.weight > 1 && `(×${v.weight})`}
            </li>
          ))}
        </ul>
      </details>
    </details>
  );
}

function HangingConfirmPanel({
  data,
  surface,
  emojiMap,
}: {
  data: LiveGameState;
  surface: "admin" | "webapp";
  emojiMap: Record<string, string>;
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  if (data.phase !== "hanging_confirm" && data.rounds.length === 0) return null;
  const current = data.rounds[data.rounds.length - 1];
  if (!current) return null;
  const hc = current.extra?.hanging_confirm;
  const target = current.extra?.pending_hang_target;
  if (!target && !hc) return null;

  const yesSum = Object.values(hc?.yes || {}).reduce(
    (s, w) => s + (w as number),
    0,
  );
  const noSum = Object.values(hc?.no || {}).reduce(
    (s, w) => s + (w as number),
    0,
  );

  if (isAdmin) {
    return (
      <>
        <h3 style={{ color: "var(--muted)" }}>
          ⚖️ {t("admin.live.section_hanging_confirm", "Hanging confirm")}
        </h3>
        <div className="admin-card" style={{ marginBottom: "1.5rem" }}>
          {target && (
            <p style={{ margin: 0 }}>
              <strong>
                {t("admin.live.hang_target", "Target")}:
              </strong>{" "}
              {nameOf(data, target as number, emojiMap)}
            </p>
          )}
          <p style={{ margin: "0.5rem 0 0 0" }}>
            👍 <strong style={{ color: "#27ae60" }}>{yesSum}</strong> &nbsp;&nbsp; 👎{" "}
            <strong style={{ color: "#e74c3c" }}>{noSum}</strong>
          </p>
          {(yesSum > 0 || noSum > 0) && (
            <details style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
              <summary style={{ cursor: "pointer", color: "var(--muted)" }}>
                {t("admin.live.individual_hang_votes", "Individual hang votes")}
              </summary>
              <ul style={{ paddingLeft: "1.5rem", marginTop: "0.5rem" }}>
                {Object.entries(hc?.yes || {}).map(([uid, w]) => (
                  <li key={`y-${uid}`}>
                    👍 {nameOf(data, parseInt(uid), emojiMap)}{" "}
                    {(w as number) > 1 && `(×${w as number})`}
                  </li>
                ))}
                {Object.entries(hc?.no || {}).map(([uid, w]) => (
                  <li key={`n-${uid}`}>
                    👎 {nameOf(data, parseInt(uid), emojiMap)}{" "}
                    {(w as number) > 1 && `(×${w as number})`}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      </>
    );
  }

  return (
    <details open className="webapp-section" style={{ marginTop: "0.5rem" }}>
      <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
        ⚖️ {t("admin.live.section_hanging_confirm", "Hanging confirm")}
      </summary>
      <div style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
        {target && (
          <p style={{ margin: 0 }}>
            <strong>{t("admin.live.hang_target", "Target")}:</strong>{" "}
            {nameOf(data, target as number, emojiMap)}
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

function RoundsHistoryPanel({
  data,
  surface,
  emojiMap,
}: {
  data: LiveGameState;
  surface: "admin" | "webapp";
  emojiMap: Record<string, string>;
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  if (data.rounds.length === 0) return null;

  if (isAdmin) {
    return (
      <>
        <h3 style={{ color: "var(--muted)" }}>
          {t("admin.live.section_rounds_history", "Rounds history")} ({data.rounds.length})
        </h3>
        {data.rounds.map((r) => (
          <details
            key={r.round_num}
            className="admin-card"
            style={{ marginBottom: "0.75rem" }}
            open={r.round_num === data.round_num}
          >
            <summary
              style={{
                cursor: "pointer",
                color: "var(--accent)",
                fontSize: "1.05rem",
              }}
            >
              {t("admin.live.round_label", "Round")} #{r.round_num}
              {r.hanged && (
                <span style={{ color: "#f0a020", marginLeft: "0.5rem" }}>
                  — {t("admin.live.hanged", "Hanged")}:{" "}
                  {nameOf(data, r.hanged, emojiMap)}
                </span>
              )}
              {r.night_deaths.length > 0 && (
                <span style={{ color: "#e74c3c", marginLeft: "0.5rem" }}>
                  — 💀 {r.night_deaths.length}
                </span>
              )}
            </summary>
            <RoundBody round={r} data={data} emojiMap={emojiMap} isAdmin />
          </details>
        ))}
      </>
    );
  }

  return (
    <details className="webapp-section" style={{ marginTop: "0.5rem" }}>
      <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
        {t("admin.live.section_rounds_history", "Rounds history")} ({data.rounds.length})
      </summary>
      {data.rounds.map((r) => (
        <details
          key={r.round_num}
          style={{ margin: "0.5rem 0", paddingLeft: "0.5rem" }}
        >
          <summary style={{ cursor: "pointer", fontSize: "0.9rem" }}>
            {t("admin.live.round_label", "Round")} #{r.round_num}
            {r.hanged && (
              <span style={{ color: "#f0a020" }}>
                {" "}
                — {t("admin.live.hanged", "Hanged")}:{" "}
                {nameOf(data, r.hanged, emojiMap)}
              </span>
            )}
          </summary>
          <RoundBody
            round={r}
            data={data}
            emojiMap={emojiMap}
            isAdmin={false}
          />
        </details>
      ))}
    </details>
  );
}

function RoundBody({
  round,
  data,
  emojiMap,
  isAdmin,
}: {
  round: LiveGameState["rounds"][number];
  data: LiveGameState;
  emojiMap: Record<string, string>;
  isAdmin: boolean;
}) {
  const { t } = useTranslation();
  const fontSize = isAdmin ? "0.9rem" : "0.8rem";
  const indent = isAdmin ? "1.5rem" : "1.2rem";

  return (
    <div style={{ marginTop: "0.4rem", fontSize }}>
      {round.night_actions.length > 0 && (
        <>
          {isAdmin ? (
            <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>
              {t("admin.live.actions", "Actions")}
            </h4>
          ) : (
            <strong>{t("admin.live.actions", "Actions")}:</strong>
          )}
          <ul style={{ margin: 0, paddingLeft: indent }}>
            {round.night_actions.map((a, i) => (
              <li key={i}>
                {isAdmin ? (
                  <>
                    <code>{a.role}</code> ({nameOf(data, a.actor_id, emojiMap)}){" "}
                    <code>{a.action_type}</code>{" "}
                    {a.target_id !== null && a.target_id !== 0
                      ? `→ ${nameOf(data, a.target_id, emojiMap)}`
                      : ""}
                  </>
                ) : (
                  <>
                    {t(`role-${a.role}`, { defaultValue: a.role })} (
                    {nameOf(data, a.actor_id, emojiMap)}) →{" "}
                    {t(`live.action_${a.action_type}`, {
                      defaultValue: a.action_type,
                    })}{" "}
                    {a.target_id !== null && a.target_id !== 0
                      ? `→ ${nameOf(data, a.target_id, emojiMap)}`
                      : ""}
                  </>
                )}
              </li>
            ))}
          </ul>
        </>
      )}

      {round.night_deaths.length > 0 && (
        <>
          {isAdmin ? (
            <h4 style={{ color: "#e74c3c", margin: "0.5rem 0" }}>
              {t("admin.live.deaths", "Deaths")}
            </h4>
          ) : (
            <div style={{ color: "#e74c3c", marginTop: 4 }}>
              <strong>{t("admin.live.deaths", "Deaths")}:</strong>{" "}
              {round.night_deaths
                .map((id) => nameOf(data, id, emojiMap))
                .join(", ")}
            </div>
          )}
          {isAdmin && (
            <ul style={{ margin: 0, paddingLeft: indent }}>
              {round.night_deaths.map((id) => (
                <li key={id}>{nameOf(data, id, emojiMap)}</li>
              ))}
            </ul>
          )}
        </>
      )}

      {round.day_votes.length > 0 && (
        <>
          {isAdmin ? (
            <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>
              {t("admin.live.votes", "Votes")}
            </h4>
          ) : (
            <strong>{t("admin.live.votes", "Votes")}:</strong>
          )}
          <ul style={{ margin: 0, paddingLeft: indent }}>
            {round.day_votes.map((v, i) => (
              <li key={i}>
                {nameOf(data, v.voter_id, emojiMap)} →{" "}
                {v.target_id === 0
                  ? t("admin.live.nobody", "(nobody)")
                  : nameOf(data, v.target_id, emojiMap)}{" "}
                {v.weight > 1 && `(×${v.weight})`}
              </li>
            ))}
          </ul>
        </>
      )}

      {Object.keys(round.last_words || {}).length > 0 && (
        <>
          {isAdmin ? (
            <h4 style={{ color: "var(--muted)", margin: "0.5rem 0" }}>
              {t("admin.live.last_words", "Last words")}
            </h4>
          ) : (
            <strong>{t("admin.live.last_words", "Last words")}:</strong>
          )}
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
              <strong>{nameOf(data, parseInt(uid), emojiMap)}:</strong> {words}
            </blockquote>
          ))}
        </>
      )}
    </div>
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
        {value}
      </div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

function SmallKPI({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>{label}</div>
      <div style={{ fontWeight: 600 }}>{value}</div>
    </div>
  );
}
