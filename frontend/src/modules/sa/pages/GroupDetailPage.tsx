/**
 * Unified group detail page.
 *
 * Surface drives layout:
 *   admin  — hero card + stat band + segmented tabs, polished tables
 *   webapp — webapp-section panels, lighter chrome
 *
 * The hero, stat band, leaderboard medals and prompt-modal block-flow
 * are admin-only — the Mini App keeps its previous compact layout so
 * the existing on-device experience is unchanged.
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
import { PromptDialog } from "../components/PromptDialog";
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

  // === Webapp surface keeps the legacy compact layout. =====================
  if (!isAdmin) {
    return (
      <WebappLayout
        gid={gid}
        groupsBase={groupsBase}
        livePath={livePath}
        tab={tab}
        setTab={setTab}
      />
    );
  }

  // === Admin surface — hero + segmented tabs. ==============================
  return (
    <AdminLayout
      gid={gid}
      groupsBase={groupsBase}
      livePath={livePath}
      tab={tab}
      setTab={setTab}
    />
  );
}

// ====================================================================== //
//  Admin layout
// ====================================================================== //

function AdminLayout({
  gid,
  groupsBase,
  livePath,
  tab,
  setTab,
}: {
  gid: number;
  groupsBase: string;
  livePath: string;
  tab: Tab;
  setTab: (t: Tab) => void;
}) {
  const { t } = useTranslation();
  const qc = useQueryClient();

  // The groups list query is shared with GroupsPage and the legacy
  // ModerationButtons; we lean on it here so we don't need a new endpoint.
  const { data: groups } = useQuery({
    queryKey: ["sa-groups"],
    queryFn: () => superAdminApi.groups({ page: 1, page_size: 200 }),
    staleTime: 30_000,
  });
  const summary = useMemo(
    () => groups?.items.find((g) => g.id === gid),
    [groups, gid],
  );

  // Games query is also shared with the Games tab — pulling it here lets us
  // surface counts in the tab labels and a "LIVE" pill in the hero without
  // extra requests.
  const { data: gamesData } = useQuery({
    queryKey: ["sa-group-games", gid],
    queryFn: () => superAdminApi.groupGames(gid, 1, 50),
  });

  const liveGame = useMemo(
    () => gamesData?.items.find((g) => g.status === "running") ?? null,
    [gamesData],
  );

  const finished = useMemo(
    () => gamesData?.items.filter((g) => g.status === "finished") ?? [],
    [gamesData],
  );
  const avgMinutes = useMemo(() => {
    if (finished.length === 0) return null;
    const total = finished.reduce(
      (acc, g) => acc + (g.duration_seconds ?? 0),
      0,
    );
    return Math.round(total / finished.length / 60);
  }, [finished]);

  const isBlocked = !!summary?.is_blocked;
  const title = summary?.title?.trim() || `${t("sa.group_detail.group_label", "Group")} #${gid}`;
  const initial = title.charAt(0).toUpperCase();

  const blockMut = useMutation({
    mutationFn: (reason: string) => superAdminApi.blockGroup(gid, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-groups"] }),
  });
  const unblockMut = useMutation({
    mutationFn: () => superAdminApi.unblockGroup(gid),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-groups"] }),
  });

  const [blockOpen, setBlockOpen] = useState(false);

  return (
    <>
      <Link to={groupsBase} className="sa-detail-back">
        ← {t("admin.groups.title", "Groups")}
      </Link>

      <section
        className={`sa-detail-hero${isBlocked ? " blocked" : ""}`}
      >
        <div className="sa-detail-hero-row">
          <div className="sa-detail-hero-avatar group">{initial || "?"}</div>

          <div className="sa-detail-hero-body">
            <h1 className="sa-detail-hero-title">
              {title}
              {liveGame && (
                <span className="sa-detail-pill live">
                  ● {t("sa.group_detail_ext.live_badge", "LIVE")}
                </span>
              )}
              {isBlocked && (
                <span className="sa-detail-pill blocked">
                  🚫 {t("admin.groups.blocked", "Blocked")}
                </span>
              )}
              {summary && !summary.onboarding_completed && !isBlocked && (
                <span className="sa-detail-pill muted">
                  ⏳ {t("admin.groups.not_onboarded", "Not onboarded")}
                </span>
              )}
              {summary && summary.is_active && summary.onboarding_completed && !isBlocked && (
                <span className="sa-detail-pill success">
                  ✓ {t("admin.groups.active", "Active")}
                </span>
              )}
            </h1>

            <div className="sa-detail-hero-meta">
              <span>{t("sa.group_detail_ext.hero_meta_id", "ID")}: <code style={{ color: "var(--fg)" }}>{String(gid)}</code></span>
              {summary?.created_at && (
                <>
                  <span className="dot" />
                  <span>
                    {t("sa.group_detail_ext.hero_meta_created", "Created")}:{" "}
                    {new Date(summary.created_at).toLocaleDateString()}
                  </span>
                </>
              )}
              <span className="dot" />
              <span>
                {t("sa.group_detail_ext.hero_meta_last_game", "Last game")}:{" "}
                {summary?.last_game_at
                  ? new Date(summary.last_game_at).toLocaleString()
                  : t("sa.group_detail_ext.hero_meta_never", "Never")}
              </span>
            </div>
          </div>

          <div className="sa-detail-hero-actions">
            <Link to={livePath} className="admin-btn primary">
              🎥 {t("admin.live.title", "Live")}
            </Link>
            {isBlocked ? (
              <button
                type="button"
                className="admin-btn"
                style={{ color: "#4ade80", borderColor: "#1f4732" }}
                disabled={unblockMut.isPending}
                onClick={() => unblockMut.mutate()}
              >
                ✅ {t("admin.groups.unblock", "Unblock")}
              </button>
            ) : (
              <button
                type="button"
                className="admin-btn danger"
                disabled={blockMut.isPending}
                onClick={() => setBlockOpen(true)}
              >
                🚫 {t("admin.groups.block", "Block")}
              </button>
            )}
          </div>
        </div>

        <div className="sa-detail-stat-band">
          <Stat
            label={t("sa.group_detail_ext.summary_games", "Games")}
            value={summary ? summary.games_total : "—"}
          />
          <Stat
            label={t("sa.group_detail_ext.summary_finished", "Finished")}
            value={finished.length}
          />
          <Stat
            label={t("sa.group_detail_ext.summary_running", "Running")}
            value={liveGame ? 1 : 0}
            valueClass={liveGame ? "success" : "muted"}
          />
          <Stat
            label={t("sa.group_detail_ext.summary_avg_duration", "Avg duration")}
            value={avgMinutes !== null ? `${avgMinutes} ${t("sa.group_detail.games_duration_unit", "min")}` : "—"}
            valueClass={avgMinutes === null ? "muted" : undefined}
          />
        </div>
      </section>

      {isBlocked && (
        <div className="sa-detail-danger-zone">
          <div className="icon">⚠️</div>
          <div className="body">
            <h3 className="title">
              {t("sa.group_detail_ext.blocked_zone_title", "Group is blocked")}
            </h3>
            <div className="meta">
              {t("admin.groups.blocked", "Blocked")} ·{" "}
              {summary?.last_game_at
                ? `${t("sa.group_detail_ext.hero_meta_last_game", "Last game")}: ${new Date(summary.last_game_at).toLocaleDateString()}`
                : t("sa.group_detail_ext.hero_meta_never", "Never")}
            </div>
          </div>
          <div>
            <button
              type="button"
              className="admin-btn"
              style={{ color: "#4ade80", borderColor: "#1f4732" }}
              disabled={unblockMut.isPending}
              onClick={() => unblockMut.mutate()}
            >
              ✅ {t("admin.groups.unblock", "Unblock")}
            </button>
          </div>
        </div>
      )}

      <div className="sa-detail-tabs">
        {(["games", "leaderboard", "settings"] as Tab[]).map((k) => (
          <button
            key={k}
            type="button"
            className={`sa-detail-tab ${tab === k ? "active" : ""}`}
            onClick={() => setTab(k)}
          >
            {t(`sa.group_detail.tab_${k}`, k)}
            {k === "games" && gamesData && gamesData.total > 0 && (
              <span className="count">{gamesData.total}</span>
            )}
          </button>
        ))}
      </div>

      {tab === "games" && <GamesTabAdmin gid={gid} preloaded={gamesData} />}
      {tab === "leaderboard" && <LeaderboardTabAdmin gid={gid} />}
      {tab === "settings" && <SettingsTab gid={gid} surface="admin" />}

      <PromptDialog
        open={blockOpen}
        title={t("sa.group_detail_ext.block_prompt_title", "Block this group")}
        subtitle={t("sa.group_detail_ext.block_prompt_subtitle", "After blocking, /game stops working.")}
        label={t("sa.group_detail_ext.block_prompt_label", "Block reason")}
        placeholder={t("sa.group_detail_ext.block_preset_spam", "Spam")}
        confirmLabel={t("sa.group_detail_ext.block_confirm", "Block")}
        variant="danger"
        presets={[
          { label: `🗑 ${t("sa.group_detail_ext.block_preset_spam", "Spam")}`, value: t("sa.group_detail_ext.block_preset_spam", "Spam") },
          { label: `⚠️ ${t("sa.group_detail_ext.block_preset_abuse", "Abuse")}`, value: t("sa.group_detail_ext.block_preset_abuse", "Abuse") },
          { label: `💤 ${t("sa.group_detail_ext.block_preset_inactive", "Inactive")}`, value: t("sa.group_detail_ext.block_preset_inactive", "Inactive") },
        ]}
        onConfirm={async (v) => {
          await blockMut.mutateAsync(v);
        }}
        onClose={() => setBlockOpen(false)}
      />
    </>
  );
}

// ====================================================================== //
//  Webapp layout — preserved from the original implementation
// ====================================================================== //

function WebappLayout({
  gid,
  groupsBase,
  livePath,
  tab,
  setTab,
}: {
  gid: number;
  groupsBase: string;
  livePath: string;
  tab: Tab;
  setTab: (t: Tab) => void;
}) {
  const { t } = useTranslation();
  return (
    <>
      <Link to={groupsBase} style={{ color: "var(--muted)" }}>
        ← {t("admin.groups.title", "Groups")}
      </Link>
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
        <GroupModerationButtonsWebapp groupId={gid} />
      </div>

      <div className="webapp-tabs">
        {(["games", "leaderboard", "settings"] as Tab[]).map((k) => (
          <button
            key={k}
            type="button"
            className={`webapp-tab ${tab === k ? "active" : ""}`}
            onClick={() => setTab(k)}
          >
            {t(`sa.group_detail.tab_${k}`, k)}
          </button>
        ))}
      </div>

      {tab === "games" && <GamesTabWebapp gid={gid} />}
      {tab === "leaderboard" && <LeaderboardTabWebapp gid={gid} />}
      {tab === "settings" && <SettingsTab gid={gid} surface="webapp" />}
    </>
  );
}

// ====================================================================== //
//  Tabs — admin
// ====================================================================== //

function GamesTabAdmin({
  gid,
  preloaded,
}: {
  gid: number;
  preloaded?: Awaited<ReturnType<typeof superAdminApi.groupGames>>;
}) {
  const { t } = useTranslation();
  const gameBase = useSaPath("/games");
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-games", gid],
    queryFn: () => superAdminApi.groupGames(gid, 1, 50),
    initialData: preloaded,
  });

  if (isLoading || !data) {
    return <div className="admin-card">⏳ {t("loading")}</div>;
  }

  if (data.items.length === 0) {
    return (
      <div className="admin-card">
        <div className="sa-detail-empty">
          <span className="icon">🎲</span>
          <div>{t("sa.group_detail_ext.games_empty", "No games yet")}</div>
          <small>{t("sa.group_detail_ext.games_empty_hint", "Run /game inside the group to start.")}</small>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-card sa-detail-table-section">
      <div className="sa-detail-section-header">
        <h3>{t("sa.group_detail.games_title", "Games")}</h3>
        <span className="hint">{data.total}</span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="admin-table">
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
                <td style={{ fontFamily: "monospace", fontSize: "0.78rem" }}>
                  <Link to={`${gameBase}/${g.id}`} style={{ color: "inherit" }}>
                    {g.id.slice(0, 8)}…
                  </Link>
                </td>
                <td>
                  <span className={`badge ${badgeClass(g.status)}`}>
                    {t(`admin.games.status_${g.status}`, g.status)}
                  </span>
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

function LeaderboardTabAdmin({ gid }: { gid: number }) {
  const { t } = useTranslation();
  const userBase = useSaPath("/users");
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-leaderboard", gid],
    queryFn: () => superAdminApi.groupLeaderboard(gid, 50),
  });

  if (isLoading || !data) {
    return <div className="admin-card">⏳ {t("loading")}</div>;
  }

  if (data.items.length === 0) {
    return (
      <div className="admin-card">
        <div className="sa-detail-empty">
          <span className="icon">🏆</span>
          <div>{t("sa.group_detail_ext.leaderboard_empty", "No leaderboard yet")}</div>
          <small>
            {t("sa.group_detail_ext.leaderboard_empty_hint", "Ranks will appear after the first finished game.")}
          </small>
        </div>
      </div>
    );
  }

  const maxElo = Math.max(...data.items.map((p) => p.elo), 1);

  return (
    <div className="admin-card sa-detail-table-section">
      <div className="sa-detail-section-header">
        <h3>{t("sa.group_detail.leaderboard_title", "Leaderboard")}</h3>
        <span className="hint">{data.items.length}</span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th style={{ width: 50 }}>{t("sa.group_detail.lb_col_rank", "#")}</th>
              <th>{t("sa.group_detail.lb_col_player", "Player")}</th>
              <th style={{ textAlign: "right" }}>{t("sa.group_detail.lb_col_elo", "ELO")}</th>
              <th style={{ textAlign: "right" }}>{t("sa.group_detail.lb_col_games", "Games")}</th>
              <th style={{ textAlign: "right" }}>{t("sa.group_detail.lb_col_wins", "Wins")}</th>
              <th style={{ minWidth: 130 }}>{t("sa.group_detail.lb_col_wr", "WR")}</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((p) => {
              const medalCls =
                p.rank === 1 ? "gold" : p.rank === 2 ? "silver" : p.rank === 3 ? "bronze" : "";
              const wrCls = p.winrate_pct >= 50 ? "success" : "danger";
              const eloPct = Math.round((p.elo / maxElo) * 100);
              return (
                <tr key={p.user_id}>
                  <td>
                    <span className={`sa-detail-medal ${medalCls}`}>
                      {p.rank}
                    </span>
                  </td>
                  <td>
                    <Link to={`${userBase}/${p.user_id}`} style={{ color: "inherit" }}>
                      <strong>{p.first_name}</strong>
                    </Link>
                    {p.username && (
                      <div>
                        <small style={{ color: "var(--muted)" }}>@{p.username}</small>
                      </div>
                    )}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <strong>{p.elo}</strong>
                    <div
                      className="sa-detail-mini-bar"
                      style={{ width: 70, marginLeft: "auto" }}
                    >
                      <span style={{ width: `${eloPct}%` }} />
                    </div>
                  </td>
                  <td style={{ textAlign: "right" }}>{p.games_total}</td>
                  <td style={{ textAlign: "right" }}>{p.games_won}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span
                        style={{
                          color: wrCls === "success" ? "#4ade80" : "#e74c3c",
                          fontWeight: 600,
                          minWidth: 38,
                        }}
                      >
                        {p.winrate_pct}%
                      </span>
                      <div className={`sa-detail-mini-bar ${wrCls}`} style={{ flex: 1 }}>
                        <span style={{ width: `${Math.min(100, p.winrate_pct)}%` }} />
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ====================================================================== //
//  Tabs — webapp (compact, original)
// ====================================================================== //

function GamesTabWebapp({ gid }: { gid: number }) {
  const { t } = useTranslation();
  const gameBase = useSaPath("/games");
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-games", gid],
    queryFn: () => superAdminApi.groupGames(gid, 1, 50),
  });

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {t("loading")}</div>;
  }

  return (
    <div className="webapp-section">
      <h3>{t("sa.group_detail.games_title", "Games")} ({data.total})</h3>
      <div style={{ overflowX: "auto" }}>
        <table className="sa-table">
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
                <td>{t(`admin.games.status_${g.status}`, g.status)}</td>
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

function LeaderboardTabWebapp({ gid }: { gid: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-group-leaderboard", gid],
    queryFn: () => superAdminApi.groupLeaderboard(gid, 50),
  });

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {t("loading")}</div>;
  }

  return (
    <div className="webapp-section">
      <h3>{t("sa.group_detail.leaderboard_title", "Leaderboard")}</h3>
      <div style={{ overflowX: "auto" }}>
        <table className="sa-table">
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

// ====================================================================== //
//  Settings tab — shared
// ====================================================================== //

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

  // Admin gets an in-page section index for quick navigation between
  // settings blocks. Each section anchor is `sa-set-<code>`.
  if (isAdmin) {
    return (
      <>
        <div className="admin-card" style={{ marginBottom: "1rem" }}>
          <div className="sa-detail-section-header" style={{ marginBottom: "0.4rem" }}>
            <h3>{t("sa.group_detail_ext.settings_index_title", "Sections")}</h3>
          </div>
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              flexWrap: "wrap",
            }}
          >
            {sections.map((sec) => (
              <a
                key={sec.code}
                href={`#sa-set-${sec.code}`}
                className="admin-btn small"
                style={{ textDecoration: "none" }}
              >
                {sec.emoji} {sec.title}
              </a>
            ))}
          </div>
        </div>

        {sections.map((sec) => (
          <section
            key={sec.code}
            id={`sa-set-${sec.code}`}
            className={cardCls}
            style={{ scrollMarginTop: "1rem", marginBottom: "1rem" }}
          >
            <div className="sa-detail-section-header">
              <h3>
                {sec.emoji} {sec.title}
              </h3>
              {savedKey === sec.code && (
                <span style={{ color: "#4ade80", fontSize: "0.8rem" }}>
                  ✓ {t("sa.settings.saved", "Saved")}
                </span>
              )}
            </div>
            <div>{sec.render()}</div>
          </section>
        ))}
      </>
    );
  }

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

// ====================================================================== //
//  Webapp moderation buttons (kept as-is for the Mini App)
// ====================================================================== //

function GroupModerationButtonsWebapp({ groupId }: { groupId: number }) {
  const { t } = useTranslation();
  const qc = useQueryClient();

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

  if (isBlocked) {
    return (
      <button
        type="button"
        className="sa-chip active"
        disabled={unblockMut.isPending}
        onClick={() => unblockMut.mutate()}
        style={{ padding: "0.5rem 0.75rem", color: "#4ade80" }}
      >
        ✅ {t("admin.groups.unblock", "Unblock")}
      </button>
    );
  }
  return (
    <button
      type="button"
      className="sa-chip"
      disabled={blockMut.isPending}
      onClick={() => {
        // eslint-disable-next-line no-alert
        const r = prompt(t("admin.prompts.block_reason", "Reason:") + ":");
        if (r) blockMut.mutate(r);
      }}
      style={{ padding: "0.5rem 0.75rem", color: "#e74c3c" }}
    >
      🚫 {t("admin.groups.block", "Block")}
    </button>
  );
}

// ====================================================================== //
//  Helpers
// ====================================================================== //

function Stat({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string | number;
  valueClass?: string;
}) {
  return (
    <div className="cell">
      <div className="cell-label">{label}</div>
      <div className={`cell-value ${valueClass ?? ""}`}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
    </div>
  );
}

function badgeClass(status: string): string {
  if (status === "finished") return "green";
  if (status === "running") return "yellow";
  if (status === "cancelled") return "red";
  return "";
}
