import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "@shared/api/client";

interface UserDetail {
  id: number;
  username: string | null;
  first_name: string;
  last_name: string | null;
  diamonds: number;
  dollars: number;
  xp: number;
  level: number;
  is_premium: boolean;
  is_banned: boolean;
  ban_reason: string | null;
  joined_at: string;
  stats: {
    games_total: number;
    games_won: number;
    games_lost: number;
    elo: number;
    longest_win_streak: number;
    role_stats: Record<string, { games: number; wins: number; winrate?: number; elo?: number }>;
    citizen_wins: number;
    mafia_wins: number;
    singleton_wins: number;
  } | null;
}

type Tab = "overview" | "transactions" | "games" | "achievements";

export function UserDetailPage() {
  const { t } = useTranslation();
  const { userId } = useParams();
  const uid = parseInt(userId || "0");
  const [tab, setTab] = useState<Tab>("overview");

  const { data: user, isLoading } = useQuery({
    queryKey: ["user", uid],
    queryFn: async () => (await api.get<UserDetail>(`/admin/users/${uid}`)).data,
    enabled: !!uid,
  });

  if (isLoading) return <div className="admin-card">⏳ {t("loading")}...</div>;
  if (!user) return <div className="admin-card">{t("admin.common.user_not_found")}</div>;

  return (
    <>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/admin/users" style={{ color: "var(--muted)" }}>
          {t("admin.user_detail_extra.back")}
        </Link>
      </div>
      <h1 className="admin-page-title">
        👤 {user.first_name} {user.last_name || ""}
        {user.is_premium && (
          <span className="badge yellow" style={{ marginLeft: "1rem" }}>
            {t("admin.user_detail_extra.premium_badge")}
          </span>
        )}
        {user.is_banned && (
          <span className="badge red" style={{ marginLeft: "0.5rem" }}>
            {t("admin.user_detail_extra.ban_badge")}
          </span>
        )}
      </h1>

      <div className="webapp-tabs" style={{ marginBottom: "1rem" }}>
        <TabBtn id="overview" current={tab} setTab={setTab}>
          {t("admin.user_detail_extra.tab_overview")}
        </TabBtn>
        <TabBtn id="games" current={tab} setTab={setTab}>
          {t("admin.user_detail_extra.tab_games")}
        </TabBtn>
        <TabBtn id="achievements" current={tab} setTab={setTab}>
          {t("admin.user_detail_extra.tab_achievements")}
        </TabBtn>
        <TabBtn id="transactions" current={tab} setTab={setTab}>
          {t("admin.user_detail_extra.tab_transactions")}
        </TabBtn>
      </div>

      {tab === "overview" && <Overview user={user} />}
      {tab === "transactions" && <Transactions userId={uid} />}
      {tab === "games" && <Games userId={uid} />}
      {tab === "achievements" && <Achievements userId={uid} />}
    </>
  );
}

function TabBtn({
  id,
  current,
  setTab,
  children,
}: {
  id: Tab;
  current: Tab;
  setTab: (t: Tab) => void;
  children: React.ReactNode;
}) {
  return (
    <button
      className={`webapp-tab ${current === id ? "active" : ""}`}
      onClick={() => setTab(id)}
    >
      {children}
    </button>
  );
}

function Overview({ user }: { user: UserDetail }) {
  const { t } = useTranslation();
  return (
    <>
      <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
        <KPI label={t("admin.user_detail_extra.id")} value={user.id} />
        <KPI
          label={t("admin.user_detail_extra.username")}
          value={user.username ? `@${user.username}` : "—"}
        />
        <KPI label={t("admin.user_detail_extra.level")} value={user.level} />
        <KPI label={t("admin.user_detail_extra.diamonds")} value={user.diamonds} />
        <KPI label={t("admin.user_detail_extra.dollars")} value={user.dollars} />
        <KPI label={t("admin.user_detail_extra.xp")} value={user.xp} />
      </div>

      {user.stats ? (
        <>
          <h3 style={{ color: "var(--muted)" }}>{t("admin.user_detail.stats")}</h3>
          <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
            <KPI label={t("admin.user_detail.games_total")} value={user.stats.games_total} />
            <KPI
              label={t("admin.user_detail.wins")}
              value={user.stats.games_won}
              sub={`WR ${
                user.stats.games_total
                  ? Math.round((user.stats.games_won / user.stats.games_total) * 100)
                  : 0
              }%`}
            />
            <KPI label={t("admin.user_detail.elo")} value={user.stats.elo} />
            <KPI
              label={t("admin.user_detail.longest_streak")}
              value={user.stats.longest_win_streak}
            />
          </div>

          <h3 style={{ color: "var(--muted)" }}>{t("admin.user_detail.by_team")}</h3>
          <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
            <KPI
              label={`👨🏼 ${t("admin.user_detail.team_civilian")}`}
              value={user.stats.citizen_wins}
            />
            <KPI
              label={`🤵🏼 ${t("admin.user_detail.team_mafia")}`}
              value={user.stats.mafia_wins}
            />
            <KPI
              label={`🎯 ${t("admin.user_detail.team_singleton")}`}
              value={user.stats.singleton_wins}
            />
          </div>

          <h3 style={{ color: "var(--muted)" }}>{t("admin.user_detail.by_role")}</h3>
          <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>{t("admin.user_detail_extra.games_role")}</th>
                  <th>{t("admin.user_detail.games_total")}</th>
                  <th>{t("admin.user_detail.wins")}</th>
                  <th>WR</th>
                  <th>{t("admin.user_detail.elo")}</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(user.stats.role_stats).map(([role, data]) => (
                  <tr key={role}>
                    <td>{role}</td>
                    <td>{data.games || 0}</td>
                    <td>{data.wins || 0}</td>
                    <td>{Math.round((data.winrate || 0) * 100)}%</td>
                    <td>{data.elo || 1000}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="admin-card">{t("admin.user_detail.no_games")}</div>
      )}

      {user.is_banned && user.ban_reason && (
        <div
          className="admin-card"
          style={{ marginTop: "1rem", borderColor: "#c0392b", color: "#e74c3c" }}
        >
          {t("admin.user_detail_extra.ban_reason_label")}: {user.ban_reason}
        </div>
      )}
    </>
  );
}

function KPI({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="admin-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" style={{ fontSize: "1.5rem" }}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

function Transactions({ userId }: { userId: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["user-transactions", userId],
    queryFn: async () =>
      (await api.get<{ items: any[] }>(`/admin/users/${userId}/transactions`)).data,
  });

  if (isLoading) return <div className="admin-card">⏳</div>;

  return (
    <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
      <table className="admin-table">
        <thead>
          <tr>
            <th>{t("admin.user_detail_extra.tx_time")}</th>
            <th>{t("admin.user_detail_extra.tx_type")}</th>
            <th>💎</th>
            <th>💵</th>
            <th>⭐</th>
            <th>{t("admin.user_detail_extra.tx_item")}</th>
            <th>{t("admin.user_detail_extra.tx_status")}</th>
            <th>{t("admin.user_detail_extra.tx_note")}</th>
          </tr>
        </thead>
        <tbody>
          {data?.items.map((t) => (
            <tr key={t.id}>
              <td style={{ color: "var(--muted)" }}>
                {new Date(t.created_at).toLocaleString()}
              </td>
              <td style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>{t.type}</td>
              <td style={{ color: t.diamonds_amount > 0 ? "#4ade80" : "#e74c3c" }}>
                {t.diamonds_amount || "—"}
              </td>
              <td>{t.dollars_amount || "—"}</td>
              <td>{t.stars_amount || "—"}</td>
              <td>{t.item || "—"}</td>
              <td>
                <span
                  className={`badge ${t.status === "completed" ? "green" : t.status === "failed" ? "red" : "yellow"}`}
                >
                  {t.status}
                </span>
              </td>
              <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>{t.note || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Games({ userId }: { userId: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["user-games", userId],
    queryFn: async () =>
      (await api.get<{ items: any[] }>(`/admin/users/${userId}/games`)).data,
  });

  if (isLoading) return <div className="admin-card">⏳</div>;

  return (
    <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
      <table className="admin-table">
        <thead>
          <tr>
            <th>{t("admin.user_detail_extra.games_time")}</th>
            <th>{t("admin.user_detail_extra.games_game")}</th>
            <th>{t("admin.user_detail_extra.games_role")}</th>
            <th>{t("admin.user_detail_extra.games_team")}</th>
            <th>{t("admin.user_detail_extra.games_result")}</th>
            <th>{t("admin.user_detail_extra.games_elo")}</th>
            <th>{t("admin.user_detail_extra.games_xp")}</th>
          </tr>
        </thead>
        <tbody>
          {data?.items.map((g) => (
            <tr key={g.id}>
              <td style={{ color: "var(--muted)" }}>
                {new Date(g.played_at).toLocaleString()}
              </td>
              <td style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                <Link to={`/admin/games/${g.game_id}`}>{g.game_id.slice(0, 8)}…</Link>
              </td>
              <td>{g.role}</td>
              <td>{g.team}</td>
              <td>
                {g.won ? (
                  <span className="badge green">
                    {t("admin.user_detail_extra.result_win")}
                  </span>
                ) : (
                  <span className="badge red">
                    {t("admin.user_detail_extra.result_loss")}
                  </span>
                )}
                {g.survived && (
                  <span className="badge" style={{ marginLeft: "0.3rem" }}>
                    🛡 {t("admin.user_detail_extra.alive")}
                  </span>
                )}
              </td>
              <td style={{ color: g.elo_change >= 0 ? "#4ade80" : "#e74c3c" }}>
                {g.elo_after} ({g.elo_change >= 0 ? "+" : ""}
                {g.elo_change})
              </td>
              <td>{g.xp_earned}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Achievements({ userId }: { userId: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["user-achievements", userId],
    queryFn: async () =>
      (await api.get<{ items: any[] }>(`/admin/users/${userId}/achievements`)).data,
  });

  if (isLoading) return <div className="admin-card">⏳</div>;
  if (!data?.items.length)
    return <div className="admin-card">{t("admin.user_detail.no_achievements")}</div>;

  return (
    <div className="admin-grid">
      {data.items.map((a) => (
        <div key={a.code} className="admin-card">
          <div style={{ fontSize: "2rem" }}>{a.icon}</div>
          <div style={{ fontWeight: 600, marginTop: "0.5rem" }}>
            {a.name_i18n.uz || a.name_i18n.en || a.code}
          </div>
          <div className="kpi-sub">
            💎 {a.diamonds_reward} · {new Date(a.unlocked_at).toLocaleDateString()}
          </div>
        </div>
      ))}
    </div>
  );
}
