import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { adminApi } from "@shared/api/admin";

type Tab = "games" | "leaderboard" | "settings";

export function GroupDetailPage() {
  const { t } = useTranslation();
  const { groupId } = useParams();
  const gid = parseInt(groupId || "0");
  const [tab, setTab] = useState<Tab>("games");

  return (
    <>
      <Link to="/admin/groups" style={{ color: "var(--muted)" }}>
        ← {t("admin.groups.title")}
      </Link>
      <h1 className="admin-page-title" style={{ marginTop: 8 }}>
        💬 {t("admin.group_detail.title")} #{gid}
        <Link
          to={`/admin/groups/${gid}/live`}
          className="admin-btn"
          style={{ marginLeft: 12, fontSize: 13 }}
        >
          🎥 {t("admin.live.title")}
        </Link>
      </h1>

      <div style={{ display: "flex", gap: 8, marginBottom: "1rem" }}>
        {(["games", "leaderboard", "settings"] as Tab[]).map((k) => (
          <button
            key={k}
            className={`admin-btn ${tab === k ? "primary" : ""}`}
            onClick={() => setTab(k)}
          >
            {t(`admin.group_detail.tab_${k}`)}
          </button>
        ))}
      </div>

      {tab === "games" && <GamesTab gid={gid} />}
      {tab === "leaderboard" && <LeaderboardTab gid={gid} />}
      {tab === "settings" && <SettingsTab gid={gid} />}
    </>
  );
}

function GamesTab({ gid }: { gid: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["admin-group-games", gid],
    queryFn: () => adminApi.groupGames(gid),
  });
  if (isLoading || !data) return <div className="admin-card">⏳ {t("loading")}</div>;
  return (
    <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
      <table className="admin-table">
        <thead>
          <tr>
            <th>{t("admin.group_detail.games_id")}</th>
            <th>{t("admin.group_detail.games_status")}</th>
            <th>{t("admin.group_detail.games_winner")}</th>
            <th style={{ textAlign: "right" }}>{t("admin.group_detail.games_players")}</th>
            <th>{t("admin.group_detail.games_started")}</th>
            <th style={{ textAlign: "right" }}>{t("admin.group_detail.games_duration")}</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((g) => (
            <tr key={g.id}>
              <td>
                <Link to={`/admin/games/${g.id}`} style={{ color: "inherit" }}>
                  <code style={{ fontSize: 12 }}>{g.id.slice(0, 8)}</code>
                </Link>
              </td>
              <td>
                <span className={`badge ${badgeClass(g.status)}`}>{g.status}</span>
              </td>
              <td>{g.winner_team ?? "—"}</td>
              <td style={{ textAlign: "right" }}>{g.players_count}</td>
              <td style={{ fontSize: 12, color: "var(--muted)" }}>
                {g.started_at && new Date(g.started_at).toLocaleString()}
              </td>
              <td style={{ textAlign: "right" }}>
                {g.duration_seconds ? `${Math.floor(g.duration_seconds / 60)}m` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LeaderboardTab({ gid }: { gid: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["admin-group-leaderboard", gid],
    queryFn: () => adminApi.groupLeaderboard(gid),
  });
  if (isLoading || !data) return <div className="admin-card">⏳ {t("loading")}</div>;
  return (
    <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
      <table className="admin-table">
        <thead>
          <tr>
            <th>#</th>
            <th>{t("admin.group_detail.lb_name")}</th>
            <th style={{ textAlign: "right" }}>{t("admin.group_detail.lb_elo")}</th>
            <th style={{ textAlign: "right" }}>{t("admin.group_detail.lb_games")}</th>
            <th style={{ textAlign: "right" }}>{t("admin.group_detail.lb_wins")}</th>
            <th style={{ textAlign: "right" }}>{t("admin.group_detail.lb_winrate")}</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((p) => (
            <tr key={p.user_id}>
              <td style={{ color: "var(--muted)" }}>{p.rank}</td>
              <td>
                <Link to={`/admin/users/${p.user_id}`} style={{ color: "inherit" }}>
                  {p.first_name}
                  {p.username && (
                    <small style={{ color: "var(--muted)", marginLeft: 6 }}>
                      @{p.username}
                    </small>
                  )}
                </Link>
              </td>
              <td style={{ textAlign: "right", fontWeight: 600 }}>{p.elo}</td>
              <td style={{ textAlign: "right" }}>{p.games_total}</td>
              <td style={{ textAlign: "right" }}>{p.games_won}</td>
              <td style={{ textAlign: "right" }}>{p.winrate_pct}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SettingsTab({ gid }: { gid: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["admin-group-settings", gid],
    queryFn: () => adminApi.groupSettings(gid),
  });
  if (isLoading || !data) return <div className="admin-card">⏳ {t("loading")}</div>;
  return (
    <div className="admin-card">
      <h3 className="admin-section-title">{t("admin.group_detail.settings_readonly_note")}</h3>
      <p style={{ color: "var(--muted)", fontSize: 13 }}>
        {t("admin.group_detail.settings_hint")}
      </p>
      <pre style={{
        background: "rgba(0,0,0,0.3)",
        padding: 12,
        borderRadius: 6,
        fontSize: 12,
        overflow: "auto",
        maxHeight: 600,
      }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

function badgeClass(status: string): string {
  if (status === "finished") return "green";
  if (status === "running") return "yellow";
  if (status === "cancelled") return "red";
  return "";
}
