import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

import { SendMessageDialog } from "../../../sa/components/SendMessageDialog";

type Tab = "overview" | "games" | "achievements" | "transactions";

export function SaUserDetailPage() {
  const { t } = useTranslation();
  const { t: tFlat } = useI18n();
  const { userId } = useParams();
  const uid = parseInt(userId || "0");
  const [tab, setTab] = useState<Tab>("overview");
  const [sendOpen, setSendOpen] = useState(false);
  const qc = useQueryClient();

  const { data: user, isLoading } = useQuery({
    queryKey: ["sa-user", uid],
    queryFn: () => saApi.user(uid),
    enabled: uid > 0,
  });

  const banMutation = useMutation({
    mutationFn: (reason: string) => saApi.banUser(uid, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-user", uid] }),
  });
  const unbanMutation = useMutation({
    mutationFn: () => saApi.unbanUser(uid),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-user", uid] }),
  });
  const grantMutation = useMutation({
    mutationFn: (amount: number) => saApi.grantDiamonds(uid, amount),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-user", uid] }),
  });
  const premiumMutation = useMutation({
    mutationFn: (days: number) => saApi.grantPremium(uid, days),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-user", uid] }),
  });

  if (isLoading || !user) {
    return <div className="webapp-section">⏳ {tFlat("loading")}</div>;
  }

  const onBan = () => {
    const reason = prompt(t("sa.user_detail.ban_prompt"));
    if (reason) banMutation.mutate(reason);
  };
  const onGrant = () => {
    const raw = prompt(t("sa.user_detail.grant_prompt"));
    const n = parseInt(raw || "0");
    if (n > 0) grantMutation.mutate(n);
  };
  const onPremium = () => {
    const raw = prompt(t("sa.user_detail.premium_prompt"));
    const n = parseInt(raw || "0");
    if (n > 0 && n <= 365) premiumMutation.mutate(n);
  };

  return (
    <>
      <Link to="/webapp/sa/users" style={{ color: "var(--muted)" }}>
        ← {t("sa.users.title")}
      </Link>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "0.5rem",
          flexWrap: "wrap",
        }}
      >
        <h2 style={{ margin: "0.5rem 0" }}>
          👤 {user.first_name} {user.is_premium && "👑"} {user.is_banned && "🚫"}
        </h2>
        <button
          type="button"
          className="sa-chip"
          onClick={() => setSendOpen(true)}
          style={{ padding: "0.35rem 0.7rem" }}
        >
          📨 {t("sa.send_msg.button")}
        </button>
      </div>
      <p style={{ margin: 0, color: "var(--muted)", fontSize: 13 }}>
        #{user.id} {user.username && `· @${user.username}`}
      </p>

      <SendMessageDialog
        userId={user.id}
        userName={user.first_name}
        open={sendOpen}
        onClose={() => setSendOpen(false)}
      />

      <div className="webapp-section" style={{ marginTop: "0.5rem" }}>
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
          {(["overview", "games", "achievements", "transactions"] as Tab[]).map((k) => (
            <button
              key={k}
              className={`sa-chip ${tab === k ? "active" : ""}`}
              onClick={() => setTab(k)}
              style={{ padding: "0.35rem 0.7rem" }}
            >
              {t(`sa.user_detail.tab_${k}`)}
            </button>
          ))}
        </div>
      </div>

      {tab === "overview" && (
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
                  <Stat label={t("sa.user_detail.games_total")} value={user.stats.games_total} />
                  <Stat label={t("sa.user_detail.wins")} value={user.stats.games_won} />
                  <Stat label="🏆 ELO" value={user.stats.elo} />
                  <Stat label={t("sa.user_detail.longest_streak")} value={user.stats.longest_win_streak} />
                </>
              )}
            </div>
          </div>

          <div className="webapp-section">
            <h3>🛠 {t("sa.user_detail.actions")}</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {user.is_banned ? (
                <button
                  className="sa-chip active"
                  disabled={unbanMutation.isPending}
                  onClick={() => unbanMutation.mutate()}
                >
                  ✅ {t("sa.users.unban")}
                </button>
              ) : (
                <button
                  className="sa-chip"
                  disabled={banMutation.isPending}
                  onClick={onBan}
                  style={{ color: "#e74c3c" }}
                >
                  🚫 {t("sa.users.ban")}
                </button>
              )}
              <button
                className="sa-chip"
                disabled={grantMutation.isPending}
                onClick={onGrant}
              >
                💎 {t("sa.users.grant_diamonds")}
              </button>
              <button
                className="sa-chip"
                disabled={premiumMutation.isPending}
                onClick={onPremium}
              >
                👑 {t("sa.user_detail.grant_premium")}
              </button>
            </div>
            {user.is_banned && user.ban_reason && (
              <p style={{ marginTop: 8, fontSize: 13, color: "#e74c3c" }}>
                <strong>{t("admin.user_detail.ban_reason")}:</strong> {user.ban_reason}
              </p>
            )}
            {user.premium_expires_at && (
              <p style={{ marginTop: 4, fontSize: 12, color: "var(--muted)" }}>
                👑 {new Date(user.premium_expires_at).toLocaleString()}
              </p>
            )}
          </div>
        </>
      )}

      {tab === "games" && <UserGamesTab uid={uid} />}
      {tab === "achievements" && <UserAchievementsTab uid={uid} />}
      {tab === "transactions" && <UserTransactionsTab uid={uid} />}
    </>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.03)", padding: "0.5rem", borderRadius: 6 }}>
      <div style={{ fontSize: 11, color: "var(--muted)" }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600 }}>{value}</div>
    </div>
  );
}

function UserGamesTab({ uid }: { uid: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-games", uid],
    queryFn: () => saApi.userGames(uid),
  });
  if (isLoading || !data) return <div className="webapp-section">⏳ …</div>;
  if (data.items.length === 0)
    return <div className="webapp-section">{t("sa.user_detail.no_games")}</div>;
  return (
    <div className="webapp-section" style={{ padding: 0 }}>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {data.items.map((g) => (
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
                {t(`role-${g.role}`, { defaultValue: g.role })}{" "}
                {g.won ? (
                  <span style={{ color: "#4ade80" }}>✓</span>
                ) : (
                  <span style={{ color: "#e74c3c" }}>✗</span>
                )}
                {!g.survived && " 💀"}
              </span>
              <span style={{ color: g.elo_change >= 0 ? "#4ade80" : "#e74c3c" }}>
                {g.elo_change >= 0 ? "+" : ""}{g.elo_change}
              </span>
            </div>
            <small style={{ color: "var(--muted)" }}>
              {new Date(g.played_at).toLocaleString()} · grp {g.group_id}
            </small>
          </li>
        ))}
      </ul>
    </div>
  );
}

function UserAchievementsTab({ uid }: { uid: number }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-achievements", uid],
    queryFn: () => saApi.userAchievements(uid),
  });
  if (isLoading || !data) return <div className="webapp-section">⏳ …</div>;
  if (data.items.length === 0)
    return <div className="webapp-section">{t("sa.user_detail.no_achievements")}</div>;
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
              <div><strong>{a.name_i18n?.[lang] || a.name_i18n?.uz || a.code}</strong></div>
              <small style={{ color: "var(--muted)" }}>
                💎 {a.diamonds_reward} · {new Date(a.unlocked_at).toLocaleDateString()}
              </small>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function UserTransactionsTab({ uid }: { uid: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-tx", uid],
    queryFn: () => saApi.userTransactions(uid),
  });
  if (isLoading || !data) return <div className="webapp-section">⏳ …</div>;
  return (
    <div className="webapp-section" style={{ padding: 0 }}>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {data.items.map((tx) => (
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
