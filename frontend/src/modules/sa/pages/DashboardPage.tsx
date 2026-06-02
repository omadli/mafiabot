/**
 * Unified SuperAdmin dashboard.
 *
 * Combined from admin/Dashboard (header live badge, WebSocket live feed
 * via useAdminLive — JWT only) and webapp/SaDashboardPage (richer KPI
 * shape from /global-stats with eight charts). Picks the layout by
 * `surface`:
 *
 *   /admin           desktop sidebar shell, live feed + admin-card grid
 *   /webapp/sa       Telegram Mini App, webapp-section blocks
 *
 * Auth routes through `superAdminApi.globalStats / chart…` to either
 * `/api/admin/*` (JWT) or `/api/sa/*` (initData). The live WebSocket
 * feed is admin-only — it relies on a JWT, the WebApp shell has no
 * persisted token, so the dot is hidden there.
 */

import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { BarChart, HBarChart, LineChart } from "@shared/components/Charts";
import { superAdminApi } from "@shared/api/superAdmin";

import { useSa } from "../context";
import { useAdminLive } from "../hooks/useAdminLive";

export function DashboardPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const isAdmin = surface === "admin";

  // Live feed needs a JWT — only meaningful on the admin shell.
  // Pass a no-op signal on webapp so we don't open a WS without auth.
  const live = useAdminLive(isAdmin);

  const { data, isLoading } = useQuery({
    queryKey: ["sa-global-stats"],
    queryFn: superAdminApi.globalStats,
    refetchInterval: 30_000,
  });

  const { data: eloChart } = useQuery({
    queryKey: ["sa-chart-elo"],
    queryFn: superAdminApi.chartElo,
    refetchInterval: 60_000,
  });

  const { data: cohortChart } = useQuery({
    queryKey: ["sa-chart-cohort"],
    queryFn: superAdminApi.chartCohort,
    refetchInterval: 60_000,
  });

  const { data: gamesChart } = useQuery({
    queryKey: ["sa-chart-games-per-day"],
    queryFn: () => superAdminApi.chartGamesPerDay(30),
    refetchInterval: 60_000,
  });

  const { data: winratesChart } = useQuery({
    queryKey: ["sa-chart-role-winrates"],
    queryFn: superAdminApi.chartRoleWinrates,
    refetchInterval: 60_000,
  });

  const { data: newUsersChart } = useQuery({
    queryKey: ["sa-chart-new-users"],
    queryFn: () => superAdminApi.chartNewUsersPerDay(30),
    refetchInterval: 60_000,
  });

  const { data: newGroupsChart } = useQuery({
    queryKey: ["sa-chart-new-groups"],
    queryFn: () => superAdminApi.chartNewGroupsPerDay(30),
    refetchInterval: 60_000,
  });

  const { data: hourChart } = useQuery({
    queryKey: ["sa-chart-games-by-hour"],
    queryFn: () => superAdminApi.chartGamesByHour(30),
    refetchInterval: 60_000,
  });

  const { data: weekdayChart } = useQuery({
    queryKey: ["sa-chart-games-by-weekday"],
    queryFn: () => superAdminApi.chartGamesByWeekday(30),
    refetchInterval: 60_000,
  });

  if (isLoading || !data) {
    const cls = isAdmin ? "admin-card" : "webapp-section";
    return <div className={cls}>⏳ {t("loading")}</div>;
  }

  const cardCls = isAdmin ? "admin-card" : "webapp-section";

  // === Title ===
  // Admin shell renders the page-title header with the live badge; the
  // Mini App keeps it lightweight because the WS feed isn't available.
  const titleEl = isAdmin ? (
    <h1
      className="admin-page-title"
      style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
    >
      📊 {t("sa.dashboard.title")}
      <span
        style={{
          fontSize: "0.7rem",
          padding: "0.2rem 0.6rem",
          borderRadius: "12px",
          background: live.connected ? "#1a3d2e" : "#3d1a1a",
          color: live.connected ? "#4ade80" : "#e74c3c",
          fontWeight: 600,
          letterSpacing: "0.05em",
        }}
      >
        {live.connected
          ? `🟢 ${t("admin.dashboard.live", "LIVE")}`
          : `🔴 ${t("admin.dashboard.offline", "OFFLINE")}`}
      </span>
    </h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>📊 {t("sa.dashboard.title")}</h2>
  );

  return (
    <>
      {titleEl}

      {isAdmin && live.events.length > 0 && (
        <div className="admin-card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0, color: "var(--muted)" }}>
            📡 {t("admin.dashboard.live_feed", "Live feed")}
          </h3>
          <ul
            style={{
              margin: 0,
              padding: 0,
              listStyle: "none",
              maxHeight: "180px",
              overflowY: "auto",
              fontSize: "0.85rem",
            }}
          >
            {live.events.slice(0, 10).map((e, idx) => (
              <li
                key={idx}
                style={{
                  padding: "0.4rem 0",
                  borderBottom: idx < 9 ? "1px solid #2a2a45" : "none",
                  color: "var(--muted)",
                }}
              >
                <span style={{ color: "var(--accent)" }}>
                  {new Date(e.receivedAt).toLocaleTimeString()}
                </span>{" "}
                <code>{e.type}</code>{" "}
                {Object.entries(e.data).map(([k, v]) => (
                  <span key={k}>
                    <strong>{k}</strong>=<code>{String(v)}</code>{" "}
                  </span>
                ))}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Section surface={surface} title={t("sa.dashboard.users_block")}>
        <KPI surface={surface} label={t("sa.dashboard.users_total")} value={data.users.total} accent="primary" />
        <KPI surface={surface} label={t("sa.dashboard.users_premium")} value={data.users.premium} />
        <KPI surface={surface} label={t("sa.dashboard.users_banned")} value={data.users.banned} accent="danger" />
        <KPI surface={surface} label={t("sa.dashboard.users_active_24h")} value={data.users.active_24h} />
        <KPI surface={surface} label={t("sa.dashboard.users_active_7d")} value={data.users.active_7d} />
        <KPI surface={surface} label={t("sa.dashboard.users_active_30d")} value={data.users.active_30d} />
      </Section>

      <Section surface={surface} title={t("sa.dashboard.groups_block")}>
        <KPI
          surface={surface}
          label={t("sa.dashboard.groups_total_active")}
          value={data.groups.total_active}
          accent="primary"
        />
        <KPI surface={surface} label={t("sa.dashboard.groups_blocked")} value={data.groups.blocked} accent="danger" />
        <KPI surface={surface} label={t("sa.dashboard.groups_onboarded")} value={data.groups.onboarded} />
      </Section>

      <Section surface={surface} title={t("sa.dashboard.games_block")}>
        <KPI surface={surface} label={t("sa.dashboard.games_total")} value={data.games.total} accent="primary" />
        <KPI surface={surface} label={t("sa.dashboard.games_finished")} value={data.games.finished} />
        <KPI surface={surface} label={t("sa.dashboard.games_running")} value={data.games.running} accent="success" />
        <KPI surface={surface} label={t("sa.dashboard.games_cancelled")} value={data.games.cancelled} />
        <KPI surface={surface} label={t("sa.dashboard.games_last_24h")} value={data.games.last_24h} />
        <KPI surface={surface} label={t("sa.dashboard.games_last_7d")} value={data.games.last_7d} />
      </Section>

      <div className={cardCls}>
        <h3 style={{ marginTop: 0 }}>{t("sa.dashboard.winrates_block")}</h3>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
          {t("sa.dashboard.total_player_games")}:{" "}
          <strong>{data.winrates.total_player_games}</strong>
        </p>
        <WinrateBar
          label={t("sa.dashboard.winrates_citizen")}
          pct={data.winrates.citizen_pct}
          wins={data.winrates.citizen_wins}
          color="#4ade80"
        />
        <WinrateBar
          label={t("sa.dashboard.winrates_mafia")}
          pct={data.winrates.mafia_pct}
          wins={data.winrates.mafia_wins}
          color="#e74c3c"
        />
        <WinrateBar
          label={t("sa.dashboard.winrates_singleton")}
          pct={data.winrates.singleton_pct}
          wins={data.winrates.singleton_wins}
          color="#f0a020"
        />
      </div>

      {/* === Charts === */}

      {eloChart && eloChart.bins.some((b) => b.count > 0) && (
        <div className={cardCls}>
          <h3>📈 {t("sa.dashboard.elo_chart")}</h3>
          <BarChart bins={eloChart.bins} />
        </div>
      )}

      {gamesChart && gamesChart.series.length > 0 && (
        <div className={cardCls}>
          <h3>📅 {t("sa.dashboard.games_chart")}</h3>
          <LineChart series={gamesChart.series} />
        </div>
      )}

      {winratesChart && winratesChart.items.length > 0 && (
        <div className={cardCls}>
          <h3>🎯 {t("sa.dashboard.winrate_chart")}</h3>
          <HBarChart
            items={winratesChart.items.map((r) => ({
              label: `${r.role} (${r.games})`,
              value: r.winrate_pct,
              color: r.winrate_pct >= 50 ? "#4ade80" : "#e74c3c",
            }))}
            max={100}
            unit="%"
          />
        </div>
      )}

      {cohortChart && cohortChart.new_users > 0 && (
        <div className={cardCls}>
          <h3>🧪 {t("sa.dashboard.cohort_chart")}</h3>
          <div className="sa-kpi-grid">
            <div className="sa-kpi sa-kpi-primary">
              <div className="sa-kpi-value">{cohortChart.new_users}</div>
              <div className="sa-kpi-label">{t("sa.dashboard.new_users")}</div>
            </div>
            <div className="sa-kpi">
              <div className="sa-kpi-value">{cohortChart.active_7d}</div>
              <div className="sa-kpi-label">
                7d · {(cohortChart.retention_7d * 100).toFixed(1)}%{" "}
                {t("sa.dashboard.retention")}
              </div>
            </div>
            <div className="sa-kpi">
              <div className="sa-kpi-value">{cohortChart.active_30d}</div>
              <div className="sa-kpi-label">
                30d · {(cohortChart.retention_30d * 100).toFixed(1)}%{" "}
                {t("sa.dashboard.retention")}
              </div>
            </div>
          </div>
        </div>
      )}

      {newUsersChart && newUsersChart.series.some((s) => s.count > 0) && (
        <div className={cardCls}>
          <h3>👤 {t("sa.dashboard.new_users_chart")}</h3>
          <LineChart series={newUsersChart.series} color="#4ade80" />
        </div>
      )}

      {newGroupsChart && newGroupsChart.series.some((s) => s.count > 0) && (
        <div className={cardCls}>
          <h3>🏘 {t("sa.dashboard.new_groups_chart")}</h3>
          <LineChart series={newGroupsChart.series} color="#f0a020" />
        </div>
      )}

      {hourChart && hourChart.total > 0 && (
        <div className={cardCls}>
          <h3>🕒 {t("sa.dashboard.hour_chart")}</h3>
          <p style={{ color: "var(--muted)", fontSize: "0.8rem", marginTop: 0 }}>
            {t("sa.dashboard.over_days", { count: hourChart.days }).replace(
              "{{count}}",
              String(hourChart.days),
            )}
          </p>
          <BarChart
            bins={hourChart.bins.map((b) => ({
              label: b.hour.toString().padStart(2, "0"),
              count: b.count,
            }))}
          />
        </div>
      )}

      {weekdayChart && weekdayChart.total > 0 && (
        <div className={cardCls}>
          <h3>📅 {t("sa.dashboard.weekday_chart")}</h3>
          <p style={{ color: "var(--muted)", fontSize: "0.8rem", marginTop: 0 }}>
            {t("sa.dashboard.over_days", { count: weekdayChart.days }).replace(
              "{{count}}",
              String(weekdayChart.days),
            )}
          </p>
          <BarChart
            bins={weekdayChart.bins.map((b) => ({
              label: t(`sa.dashboard.weekday_${b.weekday}`),
              count: b.count,
            }))}
          />
        </div>
      )}
    </>
  );
}

// === Small presentational helpers ===

function Section({
  title,
  surface,
  children,
}: {
  title: string;
  surface: "admin" | "webapp";
  children: React.ReactNode;
}) {
  const cls = surface === "admin" ? "admin-card" : "webapp-section";
  return (
    <div className={cls}>
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <div className="sa-kpi-grid">{children}</div>
    </div>
  );
}

function KPI({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  surface: "admin" | "webapp";
  accent?: "primary" | "danger" | "success";
}) {
  return (
    <div className={`sa-kpi ${accent ? `sa-kpi-${accent}` : ""}`}>
      <div className="sa-kpi-value">{value.toLocaleString()}</div>
      <div className="sa-kpi-label">{label}</div>
    </div>
  );
}

function WinrateBar({
  label,
  pct,
  wins,
  color,
}: {
  label: string;
  pct: number;
  wins: number;
  color: string;
}) {
  return (
    <div style={{ marginBottom: "0.75rem" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "0.25rem",
          fontSize: "0.85rem",
        }}
      >
        <span>{label}</span>
        <span>
          {wins} ({pct}%)
        </span>
      </div>
      <div
        style={{
          width: "100%",
          height: "8px",
          background: "#2a2a45",
          borderRadius: "4px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.min(100, pct)}%`,
            height: "100%",
            background: color,
            transition: "width 0.3s",
          }}
        />
      </div>
    </div>
  );
}
