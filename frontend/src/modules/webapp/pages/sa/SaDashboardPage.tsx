import { useQuery } from "@tanstack/react-query";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

export function SaDashboardPage() {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-global-stats"],
    queryFn: saApi.globalStats,
    refetchInterval: 30_000,
  });

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {t("loading")}</div>;
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

      <Section title={t("winrates-block")}>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
          {t("total-player-games")}: <strong>{data.winrates.total_player_games}</strong>
        </p>
        <WinrateBar
          label={t("winrates-citizen")}
          pct={data.winrates.citizen_pct}
          wins={data.winrates.citizen_wins}
          color="#4ade80"
        />
        <WinrateBar
          label={t("winrates-mafia")}
          pct={data.winrates.mafia_pct}
          wins={data.winrates.mafia_wins}
          color="#e74c3c"
        />
        <WinrateBar
          label={t("winrates-singleton")}
          pct={data.winrates.singleton_pct}
          wins={data.winrates.singleton_wins}
          color="#f0a020"
        />
      </Section>
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
