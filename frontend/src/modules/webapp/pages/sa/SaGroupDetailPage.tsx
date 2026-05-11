import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

type Tab = "games" | "leaderboard" | "settings";

export function SaGroupDetailPage() {
  const { t } = useI18n();
  const { groupId: rawId } = useParams();
  const groupId = parseInt(rawId ?? "0");
  const [tab, setTab] = useState<Tab>("games");

  if (!groupId) return <div className="webapp-section">Invalid group ID</div>;

  return (
    <>
      <Link to="/webapp/sa/groups" style={{ color: "var(--muted)" }}>
        {t("group-back")}
      </Link>

      <h2 style={{ margin: "0.5rem 0" }}>🏘 Group {groupId}</h2>

      <div className="webapp-tabs" style={{ marginBottom: "1rem" }}>
        <button
          className={`webapp-tab ${tab === "games" ? "active" : ""}`}
          onClick={() => setTab("games")}
        >
          🎲 {t("group-tab-games")}
        </button>
        <button
          className={`webapp-tab ${tab === "leaderboard" ? "active" : ""}`}
          onClick={() => setTab("leaderboard")}
        >
          🏆 {t("group-tab-leaderboard")}
        </button>
        <button
          className={`webapp-tab ${tab === "settings" ? "active" : ""}`}
          onClick={() => setTab("settings")}
        >
          ⚙️ {t("group-tab-settings")}
        </button>
      </div>

      {tab === "games" && <GamesTab groupId={groupId} />}
      {tab === "leaderboard" && <LeaderboardTab groupId={groupId} />}
      {tab === "settings" && <SettingsTab groupId={groupId} />}
    </>
  );
}

function GamesTab({ groupId }: { groupId: number }) {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-games", groupId],
    queryFn: () => saApi.groupGames(groupId, 1, 50),
  });

  if (isLoading || !data) return <div className="webapp-section">⏳ {t("loading")}</div>;

  return (
    <div className="webapp-section">
      <h3>{t("group-games-title")} ({data.total})</h3>
      <div style={{ overflowX: "auto" }}>
        <table className="sa-table">
          <thead>
            <tr>
              <th>Game ID</th>
              <th>Status</th>
              <th>Winner</th>
              <th style={{ textAlign: "right" }}>Players</th>
              <th style={{ textAlign: "right" }}>Duration</th>
              <th>Started</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((g) => (
              <tr key={g.id}>
                <td style={{ fontFamily: "monospace", fontSize: "0.75rem" }}>
                  {g.id.slice(0, 8)}…
                </td>
                <td>{g.status}</td>
                <td>{g.winner_team ?? "—"}</td>
                <td style={{ textAlign: "right" }}>{g.players_count}</td>
                <td style={{ textAlign: "right" }}>
                  {g.duration_seconds ? `${Math.round(g.duration_seconds / 60)} min` : "—"}
                </td>
                <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
                  {g.started_at ? new Date(g.started_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LeaderboardTab({ groupId }: { groupId: number }) {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-leaderboard", groupId],
    queryFn: () => saApi.groupLeaderboard(groupId, 50),
  });

  if (isLoading || !data) return <div className="webapp-section">⏳ {t("loading")}</div>;

  return (
    <div className="webapp-section">
      <h3>{t("group-leaderboard-title")}</h3>
      <div style={{ overflowX: "auto" }}>
        <table className="sa-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Player</th>
              <th style={{ textAlign: "right" }}>ELO</th>
              <th style={{ textAlign: "right" }}>Games</th>
              <th style={{ textAlign: "right" }}>Wins</th>
              <th style={{ textAlign: "right" }}>WR%</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((p) => (
              <tr key={p.user_id}>
                <td>{p.rank}</td>
                <td>
                  {p.first_name}
                  {p.username && (
                    <small style={{ color: "var(--muted)" }}> @{p.username}</small>
                  )}
                </td>
                <td style={{ textAlign: "right", fontWeight: 600 }}>{p.elo}</td>
                <td style={{ textAlign: "right" }}>{p.games_total}</td>
                <td style={{ textAlign: "right" }}>{p.games_won}</td>
                <td
                  style={{
                    textAlign: "right",
                    color: p.winrate_pct >= 50 ? "#4ade80" : "#e74c3c",
                  }}
                >
                  {p.winrate_pct}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SettingsTab({ groupId }: { groupId: number }) {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-settings", groupId],
    queryFn: () => saApi.groupSettings(groupId),
  });

  if (isLoading || !data) return <div className="webapp-section">⏳ {t("loading")}</div>;

  return (
    <div className="webapp-section">
      <h3>{t("group-settings-title")}</h3>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
        Read-only view. Use bot's /settings command inside the group for full editing
        (or the existing /webapp/settings/&lt;id&gt; flow as group admin).
      </p>

      <details style={{ marginBottom: "0.5rem" }} open>
        <summary>
          <strong>🎭 Roles</strong>
        </summary>
        <pre style={{ fontSize: "0.75rem", overflowX: "auto" }}>
          {JSON.stringify(data.roles, null, 2)}
        </pre>
      </details>

      <details style={{ marginBottom: "0.5rem" }}>
        <summary>
          <strong>⏱ Timings</strong>
        </summary>
        <pre style={{ fontSize: "0.75rem", overflowX: "auto" }}>
          {JSON.stringify(data.timings, null, 2)}
        </pre>
      </details>

      <details style={{ marginBottom: "0.5rem" }}>
        <summary>
          <strong>🛡 Items</strong>
        </summary>
        <pre style={{ fontSize: "0.75rem", overflowX: "auto" }}>
          {JSON.stringify(data.items_allowed, null, 2)}
        </pre>
      </details>

      <details style={{ marginBottom: "0.5rem" }}>
        <summary>
          <strong>🔇 Silence</strong>
        </summary>
        <pre style={{ fontSize: "0.75rem", overflowX: "auto" }}>
          {JSON.stringify(data.silence, null, 2)}
        </pre>
      </details>

      <details>
        <summary>
          <strong>🎮 Gameplay</strong>
        </summary>
        <pre style={{ fontSize: "0.75rem", overflowX: "auto" }}>
          {JSON.stringify(data.gameplay, null, 2)}
        </pre>
      </details>
    </div>
  );
}
