/**
 * Unified group detail page.
 *
 * Combined from admin/GroupDetailPage (desktop tables, JSON dump of
 * settings) and webapp/SaGroupDetailPage (interactive section editors
 * + block / unblock chip). The richer webapp Settings tab is kept
 * for both surfaces — the editors only depend on
 * `superAdminApi.updateGroupSettings`, which now routes the POST to
 * the JWT-protected `/admin/groups/:id/settings` or the initData
 * `/sa/groups/:id/settings` based on the auth store.
 *
 * Surface drives layout only — table chrome on admin
 * (`admin-card` + `admin-table`), `webapp-section` panels on the
 * Mini App.
 */

import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { superAdminApi } from "@shared/api/superAdmin";

import {
  CustomEmojiOverridesEditor,
  GameplayEditor,
  ItemsEditor,
  LanguageEditor,
  RoleEmojiOverridesEditor,
  RolesEditor,
  SilenceEditor,
  TimingsEditor,
} from "../components/GroupSettingsEditors";
import { useSa, useSaPath } from "../context";

type Tab = "games" | "leaderboard" | "settings";

export function GroupDetailPage() {
  const { t } = useTranslation();
  const { groupId: rawId } = useParams();
  const { surface } = useSa();
  const isAdmin = surface === "admin";
  const groupsBase = useSaPath("/groups");
  const livePath = useSaPath(`/groups/${rawId}/live`);

  const gid = parseInt(rawId || "0");
  const [tab, setTab] = useState<Tab>("games");

  if (!gid) {
    const cls = isAdmin ? "admin-card" : "webapp-section";
    return (
      <div className={cls}>{t("sa.group_detail.invalid_id", "Invalid group ID")}</div>
    );
  }

  const tabBtnCls = isAdmin ? "admin-btn" : "webapp-tab";

  return (
    <>
      <Link to={groupsBase} style={{ color: "var(--muted)" }}>
        ← {t("admin.groups.title", "Groups")}
      </Link>

      {isAdmin ? (
        <h1 className="admin-page-title" style={{ marginTop: 8 }}>
          💬 {t("admin.group_detail.title", "Group")} #{String(gid)}
          <Link
            to={livePath}
            className="admin-btn"
            style={{ marginLeft: 12, fontSize: 13 }}
          >
            🎥 {t("admin.live.title", "Live")}
          </Link>
        </h1>
      ) : (
        <>
          <h2 style={{ margin: "0.5rem 0" }}>
            🏘 {t("sa.group_detail.group_label", "Group")} {String(gid)}
          </h2>
          <div
            style={{
              display: "flex",
              gap: 8,
              marginBottom: "0.75rem",
              flexWrap: "wrap",
            }}
          >
            <Link
              to={livePath}
              style={{
                padding: "0.5rem 0.75rem",
                background: "var(--accent)",
                color: "#fff",
                borderRadius: "0.4rem",
                textDecoration: "none",
                fontWeight: 600,
                fontSize: "0.9rem",
              }}
            >
              🎥 {t("admin.live.title", "Live")}
            </Link>
            <GroupModerationButtons groupId={gid} surface={surface} />
          </div>
        </>
      )}

      <div
        className={isAdmin ? undefined : "webapp-tabs"}
        style={
          isAdmin
            ? { display: "flex", gap: 8, marginBottom: "1rem", flexWrap: "wrap" }
            : { marginBottom: "1rem" }
        }
      >
        {(["games", "leaderboard", "settings"] as Tab[]).map((k) => (
          <button
            key={k}
            type="button"
            className={`${tabBtnCls} ${tab === k ? (isAdmin ? "primary" : "active") : ""}`}
            onClick={() => setTab(k)}
          >
            {t(`sa.group_detail.tab_${k}`, k)}
          </button>
        ))}
      </div>

      {isAdmin && (
        <ModerationRowAdmin groupId={gid} />
      )}

      {tab === "games" && <GamesTab gid={gid} surface={surface} />}
      {tab === "leaderboard" && <LeaderboardTab gid={gid} surface={surface} />}
      {tab === "settings" && <SettingsTab gid={gid} surface={surface} />}
    </>
  );
}

// === Tabs ===

function GamesTab({ gid, surface }: { gid: number; surface: "admin" | "webapp" }) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const gameBase = useSaPath("/games");
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-games", gid],
    queryFn: () => superAdminApi.groupGames(gid, 1, 50),
  });

  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const tableCls = isAdmin ? "admin-table" : "sa-table";

  if (isLoading || !data) {
    return <div className={cardCls}>⏳ {t("loading")}</div>;
  }

  return (
    <div className={cardCls} style={isAdmin ? { padding: 0, overflow: "hidden" } : undefined}>
      {!isAdmin && (
        <h3>
          {t("sa.group_detail.games_title", "Games")} ({data.total})
        </h3>
      )}
      <div style={{ overflowX: "auto" }}>
        <table className={tableCls}>
          <thead>
            <tr>
              <th>{t("sa.group_detail.games_col_id", "ID")}</th>
              <th>{t("sa.group_detail.games_col_status", "Status")}</th>
              <th>{t("sa.group_detail.games_col_winner", "Winner")}</th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.games_col_players", "Players")}
              </th>
              <th>{t("sa.group_detail.games_col_started", "Started")}</th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.games_col_duration", "Duration")}
              </th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((g) => (
              <tr key={g.id}>
                <td style={{ fontFamily: "monospace", fontSize: "0.75rem" }}>
                  <Link to={`${gameBase}/${g.id}`} style={{ color: "inherit" }}>
                    {g.id.slice(0, 8)}…
                  </Link>
                </td>
                <td>
                  {isAdmin ? (
                    <span className={`badge ${badgeClass(g.status)}`}>{g.status}</span>
                  ) : (
                    t(`admin.games.status_${g.status}`, g.status)
                  )}
                </td>
                <td>
                  {g.winner_team
                    ? t(`admin.games.team_${g.winner_team}`, g.winner_team)
                    : "—"}
                </td>
                <td style={{ textAlign: "right" }}>{g.players_count}</td>
                <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
                  {g.started_at ? new Date(g.started_at).toLocaleString() : "—"}
                </td>
                <td style={{ textAlign: "right" }}>
                  {g.duration_seconds
                    ? `${Math.round(g.duration_seconds / 60)} ${t("sa.group_detail.games_duration_unit", "min")}`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LeaderboardTab({
  gid,
  surface,
}: {
  gid: number;
  surface: "admin" | "webapp";
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const userBase = useSaPath("/users");
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-leaderboard", gid],
    queryFn: () => superAdminApi.groupLeaderboard(gid, 50),
  });

  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const tableCls = isAdmin ? "admin-table" : "sa-table";

  if (isLoading || !data) {
    return <div className={cardCls}>⏳ {t("loading")}</div>;
  }

  return (
    <div className={cardCls} style={isAdmin ? { padding: 0, overflow: "hidden" } : undefined}>
      {!isAdmin && <h3>{t("sa.group_detail.leaderboard_title", "Leaderboard")}</h3>}
      <div style={{ overflowX: "auto" }}>
        <table className={tableCls}>
          <thead>
            <tr>
              <th>{t("sa.group_detail.lb_col_rank", "#")}</th>
              <th>{t("sa.group_detail.lb_col_player", "Player")}</th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.lb_col_elo", "ELO")}
              </th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.lb_col_games", "Games")}
              </th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.lb_col_wins", "Wins")}
              </th>
              <th style={{ textAlign: "right" }}>
                {t("sa.group_detail.lb_col_wr", "WR")}
              </th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((p) => (
              <tr key={p.user_id}>
                <td style={{ color: "var(--muted)" }}>{p.rank}</td>
                <td>
                  {isAdmin ? (
                    <Link to={`${userBase}/${p.user_id}`} style={{ color: "inherit" }}>
                      {p.first_name}
                      {p.username && (
                        <small style={{ color: "var(--muted)", marginLeft: 6 }}>
                          @{p.username}
                        </small>
                      )}
                    </Link>
                  ) : (
                    <>
                      {p.first_name}
                      {p.username && (
                        <small style={{ color: "var(--muted)" }}> @{p.username}</small>
                      )}
                    </>
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

function SettingsTab({
  gid,
  surface,
}: {
  gid: number;
  surface: "admin" | "webapp";
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const qc = useQueryClient();
  const [savedKey, setSavedKey] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-settings", gid],
    queryFn: () => superAdminApi.groupSettings(gid),
  });

  const mutation = useMutation({
    mutationFn: ({ section, value }: { section: string; value: unknown }) =>
      superAdminApi.updateGroupSettings(gid, section, value),
    onMutate: (vars) => {
      setSavedKey(vars.section);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sa-group-settings", gid] });
      setTimeout(() => setSavedKey(null), 1500);
    },
  });

  const cardCls = isAdmin ? "admin-card" : "webapp-section";

  if (isLoading || !data) {
    return <div className={cardCls}>⏳ {t("loading")}</div>;
  }

  const onSave = (section: string, value: unknown) => {
    mutation.mutate({ section, value });
  };

  const sections: {
    code: string;
    title: string;
    emoji: string;
    render: () => JSX.Element;
  }[] = [
    {
      code: "roles",
      emoji: "🎭",
      title: t("sa.settings.roles", "Roles"),
      render: () => <RolesEditor settings={data} onSave={onSave} />,
    },
    {
      code: "timings",
      emoji: "⏱",
      title: t("sa.settings.timings", "Timings"),
      render: () => <TimingsEditor settings={data} onSave={onSave} />,
    },
    {
      code: "items_allowed",
      emoji: "🛡",
      title: t("sa.settings.items", "Items"),
      render: () => <ItemsEditor settings={data} onSave={onSave} />,
    },
    {
      code: "silence",
      emoji: "🔇",
      title: t("sa.settings.silence", "Silence"),
      render: () => <SilenceEditor settings={data} onSave={onSave} />,
    },
    {
      code: "gameplay",
      emoji: "🎮",
      title: t("sa.settings.gameplay", "Gameplay"),
      render: () => <GameplayEditor settings={data} onSave={onSave} />,
    },
    {
      code: "language",
      emoji: "🌐",
      title: t("sa.settings.language", "Language"),
      render: () => <LanguageEditor settings={data} onSave={onSave} />,
    },
    {
      code: "role_emojis",
      emoji: "🎭",
      title: t("sa.settings.role_emojis", "Role emojis"),
      render: () => <RoleEmojiOverridesEditor settings={data} onSave={onSave} />,
    },
    {
      code: "custom_emojis",
      emoji: "✨",
      title: t("sa.settings.custom_emojis", "Custom emojis"),
      render: () => <CustomEmojiOverridesEditor settings={data} onSave={onSave} />,
    },
  ];

  return (
    <>
      {sections.map((sec, idx) => (
        <details
          key={sec.code}
          open={idx === 0}
          className={cardCls}
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
                ✓ {t("sa.settings.saved", "Saved")}
              </span>
            )}
          </summary>
          <div style={{ marginTop: "0.75rem" }}>{sec.render()}</div>
        </details>
      ))}
    </>
  );
}

// === Moderation actions ===

function ModerationRowAdmin({ groupId }: { groupId: number }) {
  return (
    <div style={{ marginBottom: "1rem" }}>
      <GroupModerationButtons groupId={groupId} surface="admin" />
    </div>
  );
}

function GroupModerationButtons({
  groupId,
  surface,
}: {
  groupId: number;
  surface: "admin" | "webapp";
}) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const isAdmin = surface === "admin";

  const { data: groups } = useQuery({
    queryKey: ["sa-groups"],
    queryFn: () => superAdminApi.groups({ page: 1, page_size: 200 }),
    staleTime: 30_000,
  });
  const isBlocked = useMemo(
    () => groups?.items.find((g) => g.id === groupId)?.is_blocked,
    [groups, groupId],
  );

  const blockMut = useMutation({
    mutationFn: (reason: string) => superAdminApi.blockGroup(groupId, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-groups"] }),
  });
  const unblockMut = useMutation({
    mutationFn: () => superAdminApi.unblockGroup(groupId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-groups"] }),
  });

  const chipCls = isAdmin ? "admin-btn" : "sa-chip";

  if (isBlocked) {
    return (
      <button
        type="button"
        className={`${chipCls} active`}
        disabled={unblockMut.isPending}
        onClick={() => unblockMut.mutate()}
        style={
          isAdmin
            ? { color: "#4ade80" }
            : { padding: "0.5rem 0.75rem", color: "#4ade80" }
        }
      >
        ✅ {t("admin.groups.unblock", "Unblock")}
      </button>
    );
  }
  return (
    <button
      type="button"
      className={chipCls}
      disabled={blockMut.isPending}
      onClick={() => {
        const r = prompt(
          t("admin.prompts.block_reason", "Reason:") + ":",
        );
        if (r) blockMut.mutate(r);
      }}
      style={
        isAdmin ? { color: "#e74c3c" } : { padding: "0.5rem 0.75rem", color: "#e74c3c" }
      }
    >
      🚫 {t("admin.groups.block", "Block")}
    </button>
  );
}

function badgeClass(status: string): string {
  if (status === "finished") return "green";
  if (status === "running") return "yellow";
  if (status === "cancelled") return "red";
  return "";
}
