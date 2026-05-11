import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";
import { BarChart, HBarChart, LineChart } from "@shared/components/Charts";

export function SaDashboardPage() {
  const { t: tFlat } = useI18n();
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-global-stats"],
    queryFn: saApi.globalStats,
    refetchInterval: 30_000,
  });

  const { data: eloChart } = useQuery({
    queryKey: ["sa-chart-elo"],
    queryFn: saApi.chartElo,
    refetchInterval: 60_000,
  });

  const { data: gamesChart } = useQuery({
    queryKey: ["sa-chart-games-per-day"],
    queryFn: () => saApi.chartGamesPerDay(30),
    refetchInterval: 60_000,
  });

  const { data: cohortChart } = useQuery({
    queryKey: ["sa-chart-cohort"],
    queryFn: saApi.chartCohort,
    refetchInterval: 60_000,
  });

  const { data: winratesChart } = useQuery({
    queryKey: ["sa-chart-role-winrates"],
    queryFn: saApi.chartRoleWinrates,
    refetchInterval: 60_000,
  });

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {tFlat("loading")}</div>;
  }

  return (
    <>
      <h2 style={{ marginTop: 0 }}>📊 {t("dashboard-title")}</h2>

      <Section title={t("users-block")}>
        <KPI label={t("users-total")} value={data.users.total} accent="primary" />
        <KPI label={t("users-premium")} value={data.users.premium} />
        <KPI label={t("users-banned")} value={data.users.banned} accent="danger" />
        <KPI label={t("users-active-24h")} value={data.users.active_24h} />
        <KPI label={t("users-active-7d")} value={data.users.active_7d} />
        <KPI label={t("users-active-30d")} value={data.users.active_30d} />
      </Section>

      <Section title={t("groups-block")}>
        <KPI
          label={t("groups-total-active")}
          value={data.groups.total_active}
          accent="primary"
        />
        <KPI label={t("groups-blocked")} value={data.groups.blocked} accent="danger" />
        <KPI label={t("groups-onboarded")} value={data.groups.onboarded} />
      </Section>

      <Section title={t("games-block")}>
        <KPI label={t("games-total")} value={data.games.total} accent="primary" />
        <KPI label={t("games-finished")} value={data.games.finished} />
        <KPI label={t("games-running")} value={data.games.running} accent="success" />
        <KPI label={t("games-cancelled")} value={data.games.cancelled} />
        <KPI label={t("games-last-24h")} value={data.games.last_24h} />
        <KPI label={t("games-last-7d")} value={data.games.last_7d} />
      </Section>

      <Section title={tFlat("winrates-block")}>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
          {tFlat("total-player-games")}: <strong>{data.winrates.total_player_games}</strong>
        </p>
        <WinrateBar
          label={tFlat("winrates-citizen")}
          pct={data.winrates.citizen_pct}
          wins={data.winrates.citizen_wins}
          color="#4ade80"
        />
        <WinrateBar
          label={tFlat("winrates-mafia")}
          pct={data.winrates.mafia_pct}
          wins={data.winrates.mafia_wins}
          color="#e74c3c"
        />
        <WinrateBar
          label={tFlat("winrates-singleton")}
          pct={data.winrates.singleton_pct}
          wins={data.winrates.singleton_wins}
          color="#f0a020"
        />
      </Section>

      {/* === Charts === */}

      {eloChart && eloChart.bins.some((b) => b.count > 0) && (
        <div className="webapp-section">
          <h3>📈 {t("sa.dashboard.elo_chart")}</h3>
          <BarChart bins={eloChart.bins} />
        </div>
      )}

      {gamesChart && gamesChart.series.length > 0 && (
        <div className="webapp-section">
          <h3>📅 {t("sa.dashboard.games_chart")}</h3>
          <LineChart series={gamesChart.series} />
        </div>
      )}

      {winratesChart && winratesChart.items.length > 0 && (
        <div className="webapp-section">
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
        <div className="webapp-section">
          <h3>🧪 {t("sa.dashboard.cohort_chart")}</h3>
          <div className="sa-kpi-grid">
            <div className="sa-kpi sa-kpi-primary">
              <div className="sa-kpi-value">{cohortChart.new_users}</div>
              <div className="sa-kpi-label">{t("sa.dashboard.new_users")}</div>
            </div>
            <div className="sa-kpi">
              <div className="sa-kpi-value">{cohortChart.active_7d}</div>
              <div className="sa-kpi-label">
                7d · {(cohortChart.retention_7d * 100).toFixed(1)}% {t("sa.dashboard.retention")}
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
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="webapp-section">
      <h3>{title}</h3>
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
