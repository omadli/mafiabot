import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

import {
  GameplayEditor,
  ItemsEditor,
  LanguageEditor,
  RolesEditor,
  SilenceEditor,
  TimingsEditor,
} from "./GroupSettingsEditors";

type Tab = "games" | "leaderboard" | "settings";

export function SaGroupDetailPage() {
  const { t } = useI18n();
  const { groupId: rawId } = useParams();
  const groupId = parseInt(rawId ?? "0");
  const [tab, setTab] = useState<Tab>("games");

  if (!groupId)
    return (
      <div className="webapp-section">{t("sa.group_detail.invalid_id")}</div>
    );

  return (
    <>
      <Link to="/webapp/sa/groups" style={{ color: "var(--muted)" }}>
        {t("group-back")}
      </Link>

      <h2 style={{ margin: "0.5rem 0" }}>
        🏘 {t("sa.group_detail.group_label")} {groupId}
      </h2>

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
  const { t: tFlat } = useI18n();
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-games", groupId],
    queryFn: () => saApi.groupGames(groupId, 1, 50),
  });

  if (isLoading || !data)
    return <div className="webapp-section">⏳ {tFlat("loading")}</div>;

  return (
    <div className="webapp-section">
      <h3>
        {tFlat("group-games-title")} ({data.total})
      </h3>
      <div style={{ overflowX: "auto" }}>
        <table className="sa-table">
          <thead>
            <tr>
              <th>{t("sa.group_detail.games_col_id")}</th>
              <th>{t("sa.group_detail.games_col_status")}</th>
              <th>{t("sa.group_detail.games_col_winner")}</th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.games_col_players")}
              </th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.games_col_duration")}
              </th>
              <th>{t("sa.group_detail.games_col_started")}</th>
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
                  {g.duration_seconds
                    ? `${Math.round(g.duration_seconds / 60)} ${t("sa.group_detail.games_duration_unit")}`
                    : "—"}
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
  const { t: tFlat } = useI18n();
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-leaderboard", groupId],
    queryFn: () => saApi.groupLeaderboard(groupId, 50),
  });

  if (isLoading || !data)
    return <div className="webapp-section">⏳ {tFlat("loading")}</div>;

  return (
    <div className="webapp-section">
      <h3>{tFlat("group-leaderboard-title")}</h3>
      <div style={{ overflowX: "auto" }}>
        <table className="sa-table">
          <thead>
            <tr>
              <th>{t("sa.group_detail.lb_col_rank")}</th>
              <th>{t("sa.group_detail.lb_col_player")}</th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.lb_col_elo")}
              </th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.lb_col_games")}
              </th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.lb_col_wins")}
              </th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.lb_col_wr")}
              </th>
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
  const { t: tFlat } = useI18n();
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [savedKey, setSavedKey] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-settings", groupId],
    queryFn: () => saApi.groupSettings(groupId),
  });

  const mutation = useMutation({
    mutationFn: ({ section, value }: { section: string; value: unknown }) =>
      saApi.updateGroupSettings(groupId, section, value),
    onMutate: (vars) => {
      // Show a "saved" badge tagged with the section name
      setSavedKey(vars.section);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sa-group-settings", groupId] });
      // Clear the badge after a moment
      setTimeout(() => setSavedKey(null), 1500);
    },
  });

  if (isLoading || !data) return <div className="webapp-section">⏳ {tFlat("loading")}</div>;

  const onSave = (section: string, value: unknown) => {
    mutation.mutate({ section, value });
  };

  const sections: { code: string; title: string; emoji: string; render: () => JSX.Element }[] = [
    {
      code: "roles",
      emoji: "🎭",
      title: t("admin.settings.roles"),
      render: () => <RolesEditor settings={data} onSave={onSave} />,
    },
    {
      code: "timings",
      emoji: "⏱",
      title: t("admin.settings.timings"),
      render: () => <TimingsEditor settings={data} onSave={onSave} />,
    },
    {
      code: "items_allowed",
      emoji: "🛡",
      title: t("admin.settings.items"),
      render: () => <ItemsEditor settings={data} onSave={onSave} />,
    },
    {
      code: "silence",
      emoji: "🔇",
      title: t("admin.settings.silence"),
      render: () => <SilenceEditor settings={data} onSave={onSave} />,
    },
    {
      code: "gameplay",
      emoji: "🎮",
      title: t("admin.settings.gameplay"),
      render: () => <GameplayEditor settings={data} onSave={onSave} />,
    },
    {
      code: "language",
      emoji: "🌐",
      title: t("admin.settings.language"),
      render: () => <LanguageEditor settings={data} onSave={onSave} />,
    },
  ];

  return (
    <>
      {sections.map((sec, idx) => (
        <details
          key={sec.code}
          open={idx === 0}
          className="webapp-section"
          style={{ marginBottom: "0.5rem" }}
        >
          <summary
            style={{
              cursor: "pointer",
              listStyle: "none",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0.25rem 0",
            }}
          >
            <strong style={{ color: "var(--accent)" }}>
              {sec.emoji} {sec.title}
            </strong>
            {savedKey === sec.code && (
              <span style={{ color: "#4ade80", fontSize: "0.8rem" }}>
                ✓ {t("admin.settings.saved")}
              </span>
            )}
          </summary>
          <div style={{ marginTop: "0.75rem" }}>{sec.render()}</div>
        </details>
      ))}
    </>
  );
}
