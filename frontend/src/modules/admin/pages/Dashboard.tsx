import { useQuery } from "@tanstack/react-query";

import { api } from "@shared/api/client";

interface DashboardData {
  users: { total: number; premium: number; banned: number; premium_rate: number };
  groups: { total: number; active: number };
  games: { total: number; finished: number; running: number };
  activity: { dau: number; wau: number; mau: number };
  generated_at: string;
}

export function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get<DashboardData>("/admin/dashboard")).data,
    refetchInterval: 30_000,
  });

  if (isLoading) return <div className="admin-card">⏳ Yuklanmoqda...</div>;
  if (error || !data)
    return <div className="admin-card" style={{ color: "#e74c3c" }}>❌ Xato yuklash</div>;

  return (
    <>
      <h1 className="admin-page-title">📊 Dashboard</h1>

      <h3 style={{ color: "var(--muted)", marginTop: 0 }}>Foydalanuvchilar</h3>
      <div className="admin-grid" style={{ marginBottom: "2rem" }}>
        <KPI label="Jami" value={data.users.total} />
        <KPI label="Premium" value={data.users.premium} sub={`${(data.users.premium_rate * 100).toFixed(1)}%`} />
        <KPI label="Banlangan" value={data.users.banned} />
      </div>

      <h3 style={{ color: "var(--muted)" }}>Aktivlik</h3>
      <div className="admin-grid" style={{ marginBottom: "2rem" }}>
        <KPI label="DAU (24h)" value={data.activity.dau} />
        <KPI label="WAU (7d)" value={data.activity.wau} />
        <KPI label="MAU (30d)" value={data.activity.mau} />
      </div>

      <h3 style={{ color: "var(--muted)" }}>Guruhlar va o'yinlar</h3>
      <div className="admin-grid">
        <KPI label="Guruhlar" value={data.groups.total} sub={`${data.groups.active} aktiv`} />
        <KPI label="Jami o'yinlar" value={data.games.total} />
        <KPI label="Tugagan" value={data.games.finished} />
        <KPI label="Hozir o'ynalmoqda" value={data.games.running} />
      </div>

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
