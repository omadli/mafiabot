import { useQuery } from "@tanstack/react-query";

import { api } from "@shared/api/client";

import { useAdminLive } from "../hooks/useAdminLive";

interface DashboardData {
  users: { total: number; premium: number; banned: number; premium_rate: number };
  groups: { total: number; active: number };
  games: { total: number; finished: number; running: number };
  activity: { dau: number; wau: number; mau: number };
  generated_at: string;
}

interface EloChart {
  bins: { label: string; count: number }[];
}

interface CohortChart {
  new_users: number;
  active_7d: number;
  active_30d: number;
  retention_7d: number;
  retention_30d: number;
}

interface GamesPerDayChart {
  series: { date: string; count: number }[];
}

export function Dashboard() {
  const { events, connected } = useAdminLive();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get<DashboardData>("/admin/dashboard")).data,
    refetchInterval: 30_000,
  });

  const { data: elo } = useQuery({
    queryKey: ["chart-elo"],
    queryFn: async () => (await api.get<EloChart>("/admin/charts/elo")).data,
    refetchInterval: 60_000,
  });

  const { data: cohort } = useQuery({
    queryKey: ["chart-cohort"],
    queryFn: async () => (await api.get<CohortChart>("/admin/charts/cohort")).data,
    refetchInterval: 60_000,
  });

  const { data: gamesPerDay } = useQuery({
    queryKey: ["chart-games-per-day"],
    queryFn: async () =>
      (await api.get<GamesPerDayChart>("/admin/charts/games-per-day")).data,
    refetchInterval: 60_000,
  });

  if (isLoading || !data) return <div className="admin-card">⏳</div>;

  return (
    <>
      <h1 className="admin-page-title" style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        📊 Dashboard
        <span
          style={{
            fontSize: "0.7rem",
            padding: "0.2rem 0.6rem",
            borderRadius: "12px",
            background: connected ? "#1a3d2e" : "#3d1a1a",
            color: connected ? "#4ade80" : "#e74c3c",
            fontWeight: 600,
            letterSpacing: "0.05em",
          }}
        >
          {connected ? "🟢 LIVE" : "🔴 OFFLINE"}
        </span>
      </h1>

      {events.length > 0 && (
        <div className="admin-card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0, color: "var(--muted)" }}>📡 Live oqim</h3>
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
            {events.slice(0, 10).map((e, idx) => (
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

      <h3 style={{ color: "var(--muted)", marginTop: 0 }}>Foydalanuvchilar</h3>
      <div className="admin-grid" style={{ marginBottom: "2rem" }}>
        <KPI label="Jami" value={data.users.total} />
        <KPI
          label="Premium"
          value={data.users.premium}
          sub={`${(data.users.premium_rate * 100).toFixed(1)}%`}
        />
        <KPI label="Banlangan" value={data.users.banned} />
      </div>

      <h3 style={{ color: "var(--muted)" }}>Aktivlik</h3>
      <div className="admin-grid" style={{ marginBottom: "2rem" }}>
        <KPI label="DAU (24h)" value={data.activity.dau} />
        <KPI label="WAU (7d)" value={data.activity.wau} />
        <KPI label="MAU (30d)" value={data.activity.mau} />
      </div>

      <h3 style={{ color: "var(--muted)" }}>Guruhlar va o'yinlar</h3>
      <div className="admin-grid" style={{ marginBottom: "2rem" }}>
        <KPI label="Guruhlar" value={data.groups.total} sub={`${data.groups.active} aktiv`} />
        <KPI label="Jami o'yinlar" value={data.games.total} />
        <KPI label="Tugagan" value={data.games.finished} />
        <KPI label="Hozir o'ynalmoqda" value={data.games.running} />
      </div>

      {elo && elo.bins.some((b) => b.count > 0) && (
        <>
          <h3 style={{ color: "var(--muted)" }}>📈 ELO taqsimoti</h3>
          <div className="admin-card" style={{ marginBottom: "2rem" }}>
            <BarChart bins={elo.bins} />
          </div>
        </>
      )}

      {cohort && cohort.new_users > 0 && (
        <>
          <h3 style={{ color: "var(--muted)" }}>🎯 Cohort retention (so'nggi 30 kun)</h3>
          <div className="admin-grid" style={{ marginBottom: "2rem" }}>
            <KPI label="Yangi foydalanuvchilar" value={cohort.new_users} />
            <KPI
              label="Aktiv (7 kun)"
              value={cohort.active_7d}
              sub={`${(cohort.retention_7d * 100).toFixed(1)}% retention`}
            />
            <KPI
              label="Aktiv (30 kun)"
              value={cohort.active_30d}
              sub={`${(cohort.retention_30d * 100).toFixed(1)}% retention`}
            />
          </div>
        </>
      )}

      {gamesPerDay && (
        <>
          <h3 style={{ color: "var(--muted)" }}>📅 Kunlik o'yinlar (so'nggi 30 kun)</h3>
          <div className="admin-card" style={{ marginBottom: "2rem" }}>
            <LineChart series={gamesPerDay.series} />
          </div>
        </>
      )}

      <p style={{ marginTop: "2rem", color: "var(--muted)", fontSize: "0.8rem" }}>
        Yangilangan: {new Date(data.generated_at).toLocaleString()}
      </p>
    </>
  );
}

function KPI({ label, value, sub }: { label: string; value: number; sub?: string }) {
  return (
    <div className="admin-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value.toLocaleString()}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

function BarChart({ bins }: { bins: { label: string; count: number }[] }) {
  const max = Math.max(...bins.map((b) => b.count), 1);
  return (
    <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end", height: "200px" }}>
      {bins.map((b) => (
        <div
          key={b.label}
          style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}
        >
          <div
            style={{
              width: "100%",
              height: `${(b.count / max) * 170}px`,
              background: "var(--accent)",
              borderRadius: "6px 6px 0 0",
              minHeight: b.count > 0 ? "4px" : "0",
              transition: "height 0.3s",
              position: "relative",
            }}
          >
            {b.count > 0 && (
              <div
                style={{
                  position: "absolute",
                  top: "-1.5rem",
                  left: 0,
                  right: 0,
                  textAlign: "center",
                  fontSize: "0.75rem",
                  color: "var(--fg)",
                }}
              >
                {b.count}
              </div>
            )}
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--muted)", marginTop: "0.5rem", textAlign: "center" }}>
            {b.label}
          </div>
        </div>
      ))}
    </div>
  );
}

function LineChart({ series }: { series: { date: string; count: number }[] }) {
  const max = Math.max(...series.map((s) => s.count), 1);
  const width = 800;
  const height = 200;
  const padding = 30;

  const points = series.map((s, i) => {
    const x = padding + (i * (width - 2 * padding)) / Math.max(1, series.length - 1);
    const y = height - padding - ((s.count / max) * (height - 2 * padding));
    return { x, y, ...s };
  });

  const pathD = points.map((p, i) => (i === 0 ? `M${p.x},${p.y}` : `L${p.x},${p.y}`)).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "200px" }}>
      <path d={pathD} fill="none" stroke="var(--accent)" strokeWidth="2" />
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3" fill="var(--accent)">
          <title>
            {p.date}: {p.count}
          </title>
        </circle>
      ))}
      <text x={padding} y={height - 5} fill="var(--muted)" fontSize="10">
        {series[0]?.date}
      </text>
      <text x={width - padding - 60} y={height - 5} fill="var(--muted)" fontSize="10">
        {series[series.length - 1]?.date}
      </text>
    </svg>
  );
}
