/**
 * Unified user detail page.
 *
 * Combined from admin/UserDetailPage (detailed table layout for the
 * Transactions / Games / Achievements tabs, KPI grid) and
 * webapp/SaUserDetailPage (compact list cards, inline ban /
 * grant-diamonds / grant-premium chips). Picks the layout by
 * `surface`:
 *
 *   /admin/users/:userId           desktop tables + KPI cards
 *   /webapp/sa/users/:userId       mobile list rows + chip buttons
 *
 * Auth routes through `superAdminApi.user/userTransactions/
 * userGames/userAchievements/ban/unban/grantDiamonds/grantPremium`
 * → /api/{admin|sa}/users/:userId/...
 */

import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import {
  superAdminApi,
  type SaTransaction,
  type SaUserDetail,
  type SaUserGame,
} from "@shared/api/superAdmin";

import { SendMessageDialog } from "../components/SendMessageDialog";
import { useSa, useSaPath } from "../context";

type Tab = "overview" | "games" | "achievements" | "transactions";

export function UserDetailPage() {
  const { t } = useTranslation();
  const { userId } = useParams();
  const { surface } = useSa();
  const isAdmin = surface === "admin";
  const usersBase = useSaPath("/users");
  const gamesBase = useSaPath("/games");
  const qc = useQueryClient();

  const uid = parseInt(userId || "0");
  const [tab, setTab] = useState<Tab>("overview");
  const [sendOpen, setSendOpen] = useState(false);

  const { data: user, isLoading } = useQuery({
    queryKey: ["sa-user", uid],
    queryFn: () => superAdminApi.user(uid),
    enabled: uid > 0,
  });

  const banMutation = useMutation({
    mutationFn: (reason: string) => superAdminApi.banUser(uid, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-user", uid] }),
  });
  const unbanMutation = useMutation({
    mutationFn: () => superAdminApi.unbanUser(uid),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-user", uid] }),
  });
  const grantMutation = useMutation({
    mutationFn: (amount: number) =>
      superAdminApi.grantDiamonds(uid, amount, "admin manual grant"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-user", uid] }),
  });
  const premiumMutation = useMutation({
    mutationFn: (days: number) => superAdminApi.grantPremium(uid, days),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-user", uid] }),
  });

  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const chipCls = isAdmin ? "admin-btn" : "sa-chip";

  if (isLoading || !user) {
    return <div className={cardCls}>⏳ {t("loading")}</div>;
  }

  const onBan = () => {
    const reason = prompt(t("sa.user_detail.ban_prompt", "Reason:"));
    if (reason) banMutation.mutate(reason);
  };
  const onGrant = () => {
    const raw = prompt(t("sa.user_detail.grant_prompt", "Amount:"));
    const n = parseInt(raw || "0");
    if (n > 0) grantMutation.mutate(n);
  };
  const onPremium = () => {
    const raw = prompt(t("sa.user_detail.premium_prompt", "Days (1..365):"));
    const n = parseInt(raw || "0");
    if (n > 0 && n <= 365) premiumMutation.mutate(n);
  };

  const titleEl = isAdmin ? (
    <h1 className="admin-page-title" style={{ margin: 0 }}>
      👤 {user.first_name} {user.last_name || ""}
      {user.is_premium && (
        <span className="badge yellow" style={{ marginLeft: "1rem" }}>
          👑 PREMIUM
        </span>
      )}
      {user.is_banned && (
        <span className="badge red" style={{ marginLeft: "0.5rem" }}>
          🚫 BAN
        </span>
      )}
    </h1>
  ) : (
    <h2 style={{ margin: "0.5rem 0" }}>
      👤 {user.first_name} {user.is_premium && "👑"} {user.is_banned && "🚫"}
    </h2>
  );

  return (
    <>
      <div style={{ marginBottom: "0.5rem" }}>
        <Link to={usersBase} style={{ color: "var(--muted)" }}>
          ← {t("sa.users.title", "Users")}
        </Link>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        {titleEl}
        <button
          type="button"
          className={chipCls}
          onClick={() => setSendOpen(true)}
          style={!isAdmin ? { padding: "0.35rem 0.7rem" } : undefined}
        >
          📨 {t("sa.send_msg.button", "Send message")}
        </button>
      </div>

      {/* `String(user.id)` keeps the ID free of thousand-separators —
          Telegram IDs are identifiers, not amounts. */}
      <p style={{ margin: 0, color: "var(--muted)", fontSize: 13 }}>
        #{String(user.id)} {user.username && `· @${user.username}`}
      </p>

      <SendMessageDialog
        userId={user.id}
        userName={user.first_name + (user.last_name ? " " + user.last_name : "")}
        open={sendOpen}
        onClose={() => setSendOpen(false)}
      />

      {/* Tab bar */}
      <div
        className={isAdmin ? undefined : "webapp-section"}
        style={
          isAdmin
            ? { display: "flex", gap: "0.5rem", margin: "1rem 0", flexWrap: "wrap" }
            : { marginTop: "0.5rem" }
        }
      >
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
          {(["overview", "games", "achievements", "transactions"] as Tab[]).map((k) => (
            <button
              key={k}
              type="button"
              className={`${chipCls} ${tab === k ? "active" : ""}`}
              onClick={() => setTab(k)}
              style={!isAdmin ? { padding: "0.35rem 0.7rem" } : undefined}
            >
              {t(`sa.user_detail.tab_${k}`)}
            </button>
          ))}
        </div>
      </div>

      {tab === "overview" && (
        <Overview
          user={user}
          surface={surface}
          onBan={onBan}
          onUnban={() => unbanMutation.mutate()}
          onGrant={onGrant}
          onPremium={onPremium}
          banPending={banMutation.isPending}
          unbanPending={unbanMutation.isPending}
          grantPending={grantMutation.isPending}
          premiumPending={premiumMutation.isPending}
        />
      )}
      {tab === "games" && (
        <UserGamesTab uid={uid} surface={surface} gamesBase={gamesBase} />
      )}
      {tab === "achievements" && <UserAchievementsTab uid={uid} surface={surface} />}
      {tab === "transactions" && <UserTransactionsTab uid={uid} surface={surface} />}
    </>
  );
}

// === Overview tab ===

interface OverviewProps {
  user: SaUserDetail;
  surface: "admin" | "webapp";
  onBan: () => void;
  onUnban: () => void;
  onGrant: () => void;
  onPremium: () => void;
  banPending: boolean;
  unbanPending: boolean;
  grantPending: boolean;
  premiumPending: boolean;
}

function Overview({
  user,
  surface,
  onBan,
  onUnban,
  onGrant,
  onPremium,
  banPending,
  unbanPending,
  grantPending,
  premiumPending,
}: OverviewProps) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const chipCls = isAdmin ? "admin-btn" : "sa-chip";

  if (isAdmin) {
    return (
      <>
        <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
          <KPI label="ID" value={String(user.id)} />
          <KPI
            label={t("admin.user_detail_extra.username", "Username")}
            value={user.username ? `@${user.username}` : "—"}
          />
          <KPI label={t("admin.user_detail_extra.level", "Level")} value={user.level} />
          <KPI label="💎" value={user.diamonds} />
          <KPI label="💵" value={user.dollars} />
          <KPI label="⭐ XP" value={user.xp} />
        </div>

        <ActionBar
          chipCls={chipCls}
          isAdmin
          user={user}
          onBan={onBan}
          onUnban={onUnban}
          onGrant={onGrant}
          onPremium={onPremium}
          banPending={banPending}
          unbanPending={unbanPending}
          grantPending={grantPending}
          premiumPending={premiumPending}
        />

        {user.stats ? (
          <>
            <h3 style={{ color: "var(--muted)" }}>{t("sa.user_detail.stats")}</h3>
            <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
              <KPI
                label={t("sa.user_detail.games_total")}
                value={user.stats.games_total}
              />
              <KPI
                label={t("sa.user_detail.wins")}
                value={user.stats.games_won}
                sub={`WR ${
                  user.stats.games_total
                    ? Math.round(
                        (user.stats.games_won / user.stats.games_total) * 100,
                      )
                    : 0
                }%`}
              />
              <KPI label="🏆 ELO" value={user.stats.elo} />
              <KPI
                label={t("sa.user_detail.longest_streak")}
                value={user.stats.longest_win_streak}
              />
            </div>

            <h3 style={{ color: "var(--muted)" }}>
              {t("admin.user_detail.by_team", "By team")}
            </h3>
            <div className="admin-grid" style={{ marginBottom: "1.5rem" }}>
              <KPI
                label={`👨🏼 ${t("admin.user_detail.team_civilian", "Civilians")}`}
                value={user.stats.citizen_wins}
              />
              <KPI
                label={`🤵🏼 ${t("admin.user_detail.team_mafia", "Mafia")}`}
                value={user.stats.mafia_wins}
              />
              <KPI
                label={`🎯 ${t("admin.user_detail.team_singleton", "Singleton")}`}
                value={user.stats.singleton_wins}
              />
            </div>
          </>
        ) : (
          <div className={cardCls}>{t("sa.user_detail.no_games")}</div>
        )}

        {user.is_banned && user.ban_reason && (
          <div
            className={cardCls}
            style={{ marginTop: "1rem", borderColor: "#c0392b", color: "#e74c3c" }}
          >
            <strong>
              {t("admin.user_detail.ban_reason", "Ban reason")}:
            </strong>{" "}
            {user.ban_reason}
          </div>
        )}
      </>
    );
  }

  return (
    <>
      <div className="webapp-section">
        <h3>📊 {t("sa.user_detail.stats")}</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <Stat label="💎" value={user.diamonds} />
          <Stat label="💵" value={user.dollars} />
          <Stat label="⭐ XP" value={user.xp} />
          <Stat label="🎯 Lvl" value={user.level} />
          {user.stats && (
            <>
              <Stat
                label={t("sa.user_detail.games_total")}
                value={user.stats.games_total}
              />
              <Stat
                label={t("sa.user_detail.wins")}
                value={user.stats.games_won}
              />
              <Stat label="🏆 ELO" value={user.stats.elo} />
              <Stat
                label={t("sa.user_detail.longest_streak")}
                value={user.stats.longest_win_streak}
              />
            </>
          )}
        </div>
      </div>

      <ActionBar
        chipCls={chipCls}
        isAdmin={false}
        user={user}
        onBan={onBan}
        onUnban={onUnban}
        onGrant={onGrant}
        onPremium={onPremium}
        banPending={banPending}
        unbanPending={unbanPending}
        grantPending={grantPending}
        premiumPending={premiumPending}
      />
    </>
  );
}

function ActionBar({
  chipCls,
  isAdmin,
  user,
  onBan,
  onUnban,
  onGrant,
  onPremium,
  banPending,
  unbanPending,
  grantPending,
  premiumPending,
}: {
  chipCls: string;
  isAdmin: boolean;
  user: SaUserDetail;
  onBan: () => void;
  onUnban: () => void;
  onGrant: () => void;
  onPremium: () => void;
  banPending: boolean;
  unbanPending: boolean;
  grantPending: boolean;
  premiumPending: boolean;
}) {
  const { t } = useTranslation();
  const cardCls = isAdmin ? "admin-card" : "webapp-section";

  return (
    <div className={cardCls} style={{ marginBottom: isAdmin ? "1.5rem" : undefined }}>
      <h3 style={{ marginTop: 0 }}>🛠 {t("sa.user_detail.actions")}</h3>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {user.is_banned ? (
          <button
            type="button"
            className={`${chipCls} active`}
            disabled={unbanPending}
            onClick={onUnban}
          >
            ✅ {t("sa.users.unban", "Unban")}
          </button>
        ) : (
          <button
            type="button"
            className={chipCls}
            disabled={banPending}
            onClick={onBan}
            style={{ color: "#e74c3c" }}
          >
            🚫 {t("sa.users.ban", "Ban")}
          </button>
        )}
        <button
          type="button"
          className={chipCls}
          disabled={grantPending}
          onClick={onGrant}
        >
          💎 {t("sa.users.grant_diamonds", "Grant diamonds")}
        </button>
        <button
          type="button"
          className={chipCls}
          disabled={premiumPending}
          onClick={onPremium}
        >
          👑 {t("sa.user_detail.grant_premium", "Grant premium")}
        </button>
      </div>
      {user.premium_expires_at && (
        <p style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}>
          👑 {new Date(user.premium_expires_at).toLocaleString()}
        </p>
      )}
      {!isAdmin && user.is_banned && user.ban_reason && (
        <p style={{ marginTop: 8, fontSize: 13, color: "#e74c3c" }}>
          <strong>{t("admin.user_detail.ban_reason", "Ban reason")}:</strong>{" "}
          {user.ban_reason}
        </p>
      )}
    </div>
  );
}

// === Games tab ===

function UserGamesTab({
  uid,
  surface,
  gamesBase,
}: {
  uid: number;
  surface: "admin" | "webapp";
  gamesBase: string;
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-games", uid],
    queryFn: () => superAdminApi.userGames(uid),
  });

  if (isLoading || !data) {
    const cls = isAdmin ? "admin-card" : "webapp-section";
    return <div className={cls}>⏳ …</div>;
  }
  if (data.items.length === 0) {
    const cls = isAdmin ? "admin-card" : "webapp-section";
    return <div className={cls}>{t("sa.user_detail.no_games")}</div>;
  }

  if (isAdmin) {
    return (
      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t("admin.user_detail_extra.games_time", "Time")}</th>
              <th>{t("admin.user_detail_extra.games_game", "Game")}</th>
              <th>{t("admin.user_detail_extra.games_role", "Role")}</th>
              <th>{t("admin.user_detail_extra.games_team", "Team")}</th>
              <th>{t("admin.user_detail_extra.games_result", "Result")}</th>
              <th>{t("admin.user_detail_extra.games_elo", "ELO")}</th>
              <th>{t("admin.user_detail_extra.games_xp", "XP")}</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((g: SaUserGame) => (
              <tr key={g.id}>
                <td style={{ color: "var(--muted)" }}>
                  {new Date(g.played_at).toLocaleString()}
                </td>
                <td style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                  <Link to={`${gamesBase}/${g.game_id}`}>{g.game_id.slice(0, 8)}…</Link>
                </td>
                <td>{g.role}</td>
                <td>{g.team}</td>
                <td>
                  {g.won ? (
                    <span className="badge green">
                      {t("admin.user_detail_extra.result_win", "Win")}
                    </span>
                  ) : (
                    <span className="badge red">
                      {t("admin.user_detail_extra.result_loss", "Loss")}
                    </span>
                  )}
                  {g.survived && (
                    <span className="badge" style={{ marginLeft: "0.3rem" }}>
                      🛡 {t("admin.user_detail_extra.alive", "Alive")}
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

  return (
    <div className="webapp-section" style={{ padding: 0 }}>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {data.items.map((g: SaUserGame) => (
          <li
            key={g.id}
            style={{
              borderBottom: "1px solid #2a2a45",
              padding: "0.5rem 0.8rem",
              fontSize: 13,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 6 }}>
              <span>
                {g.role}{" "}
                {g.won ? (
                  <span style={{ color: "#4ade80" }}>✓</span>
                ) : (
                  <span style={{ color: "#e74c3c" }}>✗</span>
                )}
                {!g.survived && " 💀"}
              </span>
              <span style={{ color: g.elo_change >= 0 ? "#4ade80" : "#e74c3c" }}>
                {g.elo_change >= 0 ? "+" : ""}
                {g.elo_change}
              </span>
            </div>
            <small style={{ color: "var(--muted)" }}>
              {new Date(g.played_at).toLocaleString()} · grp {String(g.group_id)}
            </small>
          </li>
        ))}
      </ul>
    </div>
  );
}

// === Achievements tab ===

function UserAchievementsTab({
  uid,
  surface,
}: {
  uid: number;
  surface: "admin" | "webapp";
}) {
  const { t, i18n } = useTranslation();
  const isAdmin = surface === "admin";
  const lang = i18n.language;
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-achievements", uid],
    queryFn: () => superAdminApi.userAchievements(uid),
  });

  if (isLoading || !data) {
    const cls = isAdmin ? "admin-card" : "webapp-section";
    return <div className={cls}>⏳ …</div>;
  }
  if (data.items.length === 0) {
    const cls = isAdmin ? "admin-card" : "webapp-section";
    return <div className={cls}>{t("sa.user_detail.no_achievements")}</div>;
  }

  if (isAdmin) {
    return (
      <div className="admin-grid">
        {data.items.map((a) => (
          <div key={a.code} className="admin-card">
            <div style={{ fontSize: "2rem" }}>{a.icon || "🏅"}</div>
            <div style={{ fontWeight: 600, marginTop: "0.5rem" }}>
              {a.name_i18n[lang] || a.name_i18n.uz || a.code}
            </div>
            <div className="kpi-sub">
              💎 {a.diamonds_reward} ·{" "}
              {new Date(a.unlocked_at).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="webapp-section" style={{ padding: 0 }}>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {data.items.map((a) => (
          <li
            key={a.code}
            style={{
              borderBottom: "1px solid #2a2a45",
              padding: "0.5rem 0.8rem",
              display: "flex",
              gap: 10,
              alignItems: "center",
            }}
          >
            <div style={{ fontSize: 26 }}>{a.icon || "🏅"}</div>
            <div style={{ flex: 1 }}>
              <div>
                <strong>{a.name_i18n?.[lang] || a.name_i18n?.uz || a.code}</strong>
              </div>
              <small style={{ color: "var(--muted)" }}>
                💎 {a.diamonds_reward} ·{" "}
                {new Date(a.unlocked_at).toLocaleDateString()}
              </small>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

// === Transactions tab ===

function UserTransactionsTab({
  uid,
  surface,
}: {
  uid: number;
  surface: "admin" | "webapp";
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-tx", uid],
    queryFn: () => superAdminApi.userTransactions(uid),
  });

  if (isLoading || !data) {
    const cls = isAdmin ? "admin-card" : "webapp-section";
    return <div className={cls}>⏳</div>;
  }

  if (isAdmin) {
    return (
      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t("admin.user_detail_extra.tx_time", "Time")}</th>
              <th>{t("admin.user_detail_extra.tx_type", "Type")}</th>
              <th>💎</th>
              <th>💵</th>
              <th>⭐</th>
              <th>{t("admin.user_detail_extra.tx_item", "Item")}</th>
              <th>{t("admin.user_detail_extra.tx_status", "Status")}</th>
              <th>{t("admin.user_detail_extra.tx_note", "Note")}</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((tx: SaTransaction) => (
              <tr key={tx.id}>
                <td style={{ color: "var(--muted)" }}>
                  {new Date(tx.created_at).toLocaleString()}
                </td>
                <td style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>{tx.type}</td>
                <td
                  style={{
                    color:
                      tx.diamonds_amount && tx.diamonds_amount > 0
                        ? "#4ade80"
                        : "#e74c3c",
                  }}
                >
                  {tx.diamonds_amount ?? "—"}
                </td>
                <td>{tx.dollars_amount ?? "—"}</td>
                <td>{tx.stars_amount ?? "—"}</td>
                <td>{tx.item ?? "—"}</td>
                <td>
                  <span
                    className={`badge ${tx.status === "completed" ? "green" : tx.status === "failed" ? "red" : "yellow"}`}
                  >
                    {tx.status}
                  </span>
                </td>
                <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
                  {tx.note ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="webapp-section" style={{ padding: 0 }}>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {data.items.map((tx: SaTransaction) => (
          <li
            key={tx.id}
            style={{
              borderBottom: "1px solid #2a2a45",
              padding: "0.5rem 0.8rem",
              fontSize: 13,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{tx.type}</strong>
              <span style={{ color: "var(--muted)" }}>{tx.status}</span>
            </div>
            <small style={{ color: "var(--muted)" }}>
              {tx.stars_amount && `⭐${tx.stars_amount} · `}
              {tx.diamonds_amount && `💎${tx.diamonds_amount} · `}
              {tx.dollars_amount && `💵${tx.dollars_amount} · `}
              {new Date(tx.created_at).toLocaleString()}
            </small>
            {tx.note && (
              <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 3 }}>
                {tx.note}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

// === Small presentational helpers ===

function KPI({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
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

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.03)",
        padding: "0.5rem",
        borderRadius: 6,
      }}
    >
      <div style={{ fontSize: 11, color: "var(--muted)" }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
