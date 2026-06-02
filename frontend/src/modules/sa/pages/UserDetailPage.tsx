/**
 * Unified user detail page.
 *
 * Surface drives layout:
 *   admin  — identity hero, grouped KPI sections, action grid,
 *            prompt-modal mutations, richer tab tables
 *   webapp — compact list cards + sa-chip actions (legacy)
 *
 * Auth routes through `superAdminApi.user/userTransactions/
 * userGames/userAchievements/ban/unban/grantDiamonds/grantPremium`
 * → /api/{admin|sa}/users/:userId/...
 */

import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { HBarChart } from "@shared/components/Charts";
import {
  superAdminApi,
  type SaTransaction,
  type SaUserDetail,
  type SaUserGame,
} from "@shared/api/superAdmin";

import { PromptDialog } from "../components/PromptDialog";
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
  const [banOpen, setBanOpen] = useState(false);
  const [grantOpen, setGrantOpen] = useState(false);
  const [premiumOpen, setPremiumOpen] = useState(false);

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

  if (isLoading || !user) {
    const cls = isAdmin ? "admin-card" : "webapp-section";
    return <div className={cls}>⏳ {t("loading")}</div>;
  }

  // === Webapp surface keeps the legacy compact layout. =====================
  if (!isAdmin) {
    return (
      <WebappLayout
        user={user}
        uid={uid}
        usersBase={usersBase}
        gamesBase={gamesBase}
        tab={tab}
        setTab={setTab}
        sendOpen={sendOpen}
        setSendOpen={setSendOpen}
        onLegacyBan={(reason) => banMutation.mutate(reason)}
        onLegacyUnban={() => unbanMutation.mutate()}
        onLegacyGrant={(n) => grantMutation.mutate(n)}
        onLegacyPremium={(n) => premiumMutation.mutate(n)}
        pendingFlags={{
          ban: banMutation.isPending,
          unban: unbanMutation.isPending,
          grant: grantMutation.isPending,
          premium: premiumMutation.isPending,
        }}
      />
    );
  }

  // === Admin surface ======================================================
  const fullName =
    user.first_name +
    (user.last_name ? ` ${user.last_name}` : "");
  const initial = (user.first_name?.charAt(0) || "?").toUpperCase();

  const winrate =
    user.stats && user.stats.games_total > 0
      ? Math.round((user.stats.games_won / user.stats.games_total) * 100)
      : 0;

  return (
    <>
      <Link to={usersBase} className="sa-detail-back">
        ← {t("sa.users.title", "Users")}
      </Link>

      <section
        className={`sa-detail-hero${user.is_banned ? " banned" : ""}`}
      >
        <div className="sa-detail-hero-row">
          <div className="sa-detail-hero-avatar">{initial}</div>

          <div className="sa-detail-hero-body">
            <h1 className="sa-detail-hero-title">
              {fullName}
              {user.is_premium && (
                <span className="sa-detail-pill premium">👑 PREMIUM</span>
              )}
              {user.is_banned && (
                <span className="sa-detail-pill banned">🚫 BAN</span>
              )}
            </h1>

            <div className="sa-detail-hero-meta">
              {user.username ? (
                <a
                  href={`https://t.me/${user.username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "var(--accent)", textDecoration: "none" }}
                >
                  @{user.username}
                </a>
              ) : (
                <span style={{ color: "var(--muted)" }}>—</span>
              )}
              <span className="dot" />
              <span>
                {t("sa.user_detail_ext.hero_meta_id", "Telegram ID")}:{" "}
                <code style={{ color: "var(--fg)" }}>{String(user.id)}</code>
              </span>
              <span className="dot" />
              <span>
                {t("sa.user_detail_ext.hero_meta_joined", "Joined")}:{" "}
                {new Date(user.joined_at).toLocaleDateString()}
              </span>
              {user.language_code && (
                <>
                  <span className="dot" />
                  <span>
                    {t("sa.user_detail_ext.hero_meta_lang", "Language")}:{" "}
                    <strong style={{ color: "var(--fg)" }}>{user.language_code}</strong>
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="sa-detail-hero-actions">
            <button
              type="button"
              className="admin-btn primary"
              onClick={() => setSendOpen(true)}
            >
              📨 {t("sa.send_msg.button", "Send message")}
            </button>
          </div>
        </div>

        <div className="sa-detail-stat-band">
          <Cell
            label={t("sa.user_detail_ext.wallet_diamonds", "💎 Diamonds")}
            value={user.diamonds}
          />
          <Cell
            label={t("sa.user_detail_ext.wallet_dollars", "💵 Dollars")}
            value={user.dollars}
          />
          <Cell
            label={t("sa.user_detail_ext.wallet_xp", "⭐ XP")}
            value={user.xp}
          />
          <Cell
            label={t("sa.user_detail_ext.wallet_level", "🎯 Level")}
            value={user.level}
          />
          <Cell
            label={t("sa.user_detail_ext.perf_elo", "🏆 ELO")}
            value={user.stats?.elo ?? "—"}
            valueClass={user.stats ? undefined : "muted"}
          />
          <Cell
            label={t("sa.user_detail_ext.perf_winrate", "Win rate")}
            value={user.stats ? `${winrate}%` : "—"}
            valueClass={
              !user.stats ? "muted" : winrate >= 50 ? "success" : "danger"
            }
          />
        </div>
      </section>

      {user.is_banned && (
        <div className="sa-detail-danger-zone">
          <div className="icon">🚫</div>
          <div className="body">
            <h3 className="title">
              {t("sa.user_detail_ext.banned_zone_title", "User is banned")}
            </h3>
            {user.ban_reason && (
              <div className="reason">
                <strong>{t("admin.user_detail.ban_reason", "Reason")}:</strong>{" "}
                {user.ban_reason}
              </div>
            )}
            {user.banned_until && (
              <div className="meta">
                {t("sa.user_detail_ext.banned_zone_until", "Ends")}:{" "}
                {new Date(user.banned_until).toLocaleString()}
              </div>
            )}
          </div>
          <div>
            <button
              type="button"
              className="admin-btn"
              style={{ color: "#4ade80", borderColor: "#1f4732" }}
              disabled={unbanMutation.isPending}
              onClick={() => unbanMutation.mutate()}
            >
              ✅ {t("sa.users.unban", "Unban")}
            </button>
          </div>
        </div>
      )}

      <div className="sa-detail-tabs">
        {(["overview", "games", "achievements", "transactions"] as Tab[]).map((k) => (
          <button
            key={k}
            type="button"
            className={`sa-detail-tab ${tab === k ? "active" : ""}`}
            onClick={() => setTab(k)}
          >
            {t(`sa.user_detail.tab_${k}`)}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <OverviewAdmin
          user={user}
          onBan={() => setBanOpen(true)}
          onUnban={() => unbanMutation.mutate()}
          onGrant={() => setGrantOpen(true)}
          onPremium={() => setPremiumOpen(true)}
          onSend={() => setSendOpen(true)}
          banPending={banMutation.isPending}
          unbanPending={unbanMutation.isPending}
          grantPending={grantMutation.isPending}
          premiumPending={premiumMutation.isPending}
        />
      )}
      {tab === "games" && (
        <UserGamesTabAdmin uid={uid} gamesBase={gamesBase} />
      )}
      {tab === "achievements" && <UserAchievementsTabAdmin uid={uid} />}
      {tab === "transactions" && <UserTransactionsTabAdmin uid={uid} />}

      <SendMessageDialog
        userId={user.id}
        userName={fullName}
        open={sendOpen}
        onClose={() => setSendOpen(false)}
      />
      <PromptDialog
        open={banOpen}
        title={t("sa.user_detail_ext.ban_prompt_title", "Ban user")}
        subtitle={t("sa.user_detail_ext.ban_prompt_subtitle", "The reason is also sent to the user as a DM.")}
        label={t("sa.user_detail_ext.ban_prompt_label", "Ban reason")}
        confirmLabel={t("sa.user_detail_ext.ban_confirm", "Ban")}
        variant="danger"
        presets={[
          { label: `🗑 ${t("sa.user_detail_ext.ban_preset_spam", "Spam")}`, value: t("sa.user_detail_ext.ban_preset_spam", "Spam") },
          { label: `⚠️ ${t("sa.user_detail_ext.ban_preset_abuse", "Harassment")}`, value: t("sa.user_detail_ext.ban_preset_abuse", "Harassment") },
          { label: `🤖 ${t("sa.user_detail_ext.ban_preset_cheat", "Cheat / bot")}`, value: t("sa.user_detail_ext.ban_preset_cheat", "Cheat / bot") },
        ]}
        onConfirm={async (v) => {
          await banMutation.mutateAsync(v);
        }}
        onClose={() => setBanOpen(false)}
      />
      <PromptDialog
        open={grantOpen}
        title={t("sa.user_detail_ext.grant_prompt_title", "Grant diamonds")}
        subtitle={t("sa.user_detail_ext.grant_prompt_subtitle", "Diamonds are added to the user's balance.")}
        label={t("sa.user_detail_ext.grant_prompt_label", "Diamond amount")}
        inputType="number"
        min={1}
        max={1_000_000}
        confirmLabel={t("sa.user_detail_ext.grant_confirm", "Grant")}
        presets={[
          { label: "+10", value: "10" },
          { label: "+50", value: "50" },
          { label: "+100", value: "100" },
          { label: "+500", value: "500" },
        ]}
        onConfirm={async (v) => {
          await grantMutation.mutateAsync(parseInt(v, 10));
        }}
        onClose={() => setGrantOpen(false)}
      />
      <PromptDialog
        open={premiumOpen}
        title={t("sa.user_detail_ext.premium_prompt_title", "Grant premium")}
        subtitle={t("sa.user_detail_ext.premium_prompt_subtitle", "Premium expiry is extended by this many days.")}
        label={t("sa.user_detail_ext.premium_prompt_label", "Days (1..365)")}
        inputType="number"
        min={1}
        max={365}
        confirmLabel={t("sa.user_detail_ext.premium_confirm", "Grant premium")}
        presets={[
          { label: "7d", value: "7" },
          { label: "30d", value: "30" },
          { label: "90d", value: "90" },
          { label: "365d", value: "365" },
        ]}
        onConfirm={async (v) => {
          await premiumMutation.mutateAsync(parseInt(v, 10));
        }}
        onClose={() => setPremiumOpen(false)}
      />
    </>
  );
}

// ====================================================================== //
//  Admin overview tab
// ====================================================================== //

interface OverviewAdminProps {
  user: SaUserDetail;
  onBan: () => void;
  onUnban: () => void;
  onGrant: () => void;
  onPremium: () => void;
  onSend: () => void;
  banPending: boolean;
  unbanPending: boolean;
  grantPending: boolean;
  premiumPending: boolean;
}

function OverviewAdmin({
  user,
  onBan,
  onUnban,
  onGrant,
  onPremium,
  onSend,
  banPending,
  unbanPending,
  grantPending,
  premiumPending,
}: OverviewAdminProps) {
  const { t } = useTranslation();
  const stats = user.stats;
  const winrate =
    stats && stats.games_total > 0
      ? Math.round((stats.games_won / stats.games_total) * 100)
      : 0;

  const teamItems = stats
    ? [
        {
          label: t("admin.user_detail.team_civilian", "Civilians"),
          value: stats.citizen_wins,
          color: "#4ade80",
        },
        {
          label: t("admin.user_detail.team_mafia", "Mafia"),
          value: stats.mafia_wins,
          color: "#e74c3c",
        },
        {
          label: t("admin.user_detail.team_singleton", "Singleton"),
          value: stats.singleton_wins,
          color: "#f0a020",
        },
      ]
    : [];

  return (
    <>
      {/* === Performance / progress KPIs === */}
      {stats ? (
        <>
          <section className="admin-card">
            <div className="sa-detail-section-header">
              <h3>📊 {t("sa.user_detail_ext.performance_block", "Game performance")}</h3>
            </div>
            <div className="admin-grid">
              <KPI label={t("sa.user_detail_ext.perf_games", "Games")} value={stats.games_total} />
              <KPI
                label={t("sa.user_detail_ext.perf_wins", "Wins")}
                value={stats.games_won}
                sub={`${winrate}%`}
              />
              <KPI
                label={t("sa.user_detail_ext.perf_losses", "Losses")}
                value={stats.games_lost}
              />
              <KPI
                label={t("sa.user_detail_ext.perf_elo", "🏆 ELO")}
                value={stats.elo}
              />
              <KPI
                label={t("sa.user_detail_ext.perf_streak", "🔥 Best streak")}
                value={stats.longest_win_streak}
              />
              {user.afk_warnings > 0 && (
                <KPI
                  label={t("sa.user_detail_ext.perf_afk", "AFK warnings")}
                  value={user.afk_warnings}
                />
              )}
            </div>
          </section>

          <section className="admin-card">
            <div className="sa-detail-section-header">
              <h3>⚔️ {t("sa.user_detail_ext.team_block", "Wins by team")}</h3>
            </div>
            <HBarChart items={teamItems} />
          </section>
        </>
      ) : (
        <div className="admin-card">
          <div className="sa-detail-empty">
            <span className="icon">🎲</span>
            <div>{t("sa.user_detail.no_games", "No games yet")}</div>
          </div>
        </div>
      )}

      {/* === Actions === */}
      <section className="admin-card">
        <div className="sa-detail-section-header">
          <h3>🛠 {t("sa.user_detail.actions", "Actions")}</h3>
          {user.premium_expires_at && (
            <span className="hint">
              👑 {t("sa.user_detail_ext.premium_until", "Premium until")}:{" "}
              {new Date(user.premium_expires_at).toLocaleDateString()}
            </span>
          )}
        </div>
        <div className="sa-detail-action-grid">
          {user.is_banned ? (
            <ActionTile
              icon="✅"
              label={t("sa.user_detail_ext.unban_action_label", "Lift ban")}
              hint={t("sa.user_detail_ext.unban_action_hint", "User can play again")}
              cta={t("sa.users.unban", "Unban")}
              onClick={onUnban}
              disabled={unbanPending}
            />
          ) : (
            <ActionTile
              icon="🚫"
              label={t("sa.user_detail_ext.ban_action_label", "Ban user")}
              hint={t("sa.user_detail_ext.ban_action_hint", "Restricts access to the bot")}
              cta={t("sa.users.ban", "Ban")}
              variant="danger"
              onClick={onBan}
              disabled={banPending}
            />
          )}
          <ActionTile
            icon="💎"
            label={t("sa.user_detail_ext.grant_action_label", "Grant diamonds")}
            hint={t("sa.user_detail_ext.grant_action_hint", "Adds diamonds to balance")}
            cta="+ 💎"
            onClick={onGrant}
            disabled={grantPending}
          />
          <ActionTile
            icon="👑"
            label={t("sa.user_detail_ext.premium_action_label", "Grant premium")}
            hint={t("sa.user_detail_ext.premium_action_hint", "Extends premium expiry")}
            cta="+ 👑"
            onClick={onPremium}
            disabled={premiumPending}
          />
          <ActionTile
            icon="📨"
            label={t("sa.send_msg.button", "Send message")}
            hint={t("sa.user_detail_ext.send_action_hint", "Direct admin DM")}
            cta="✉️"
            onClick={onSend}
          />
        </div>
      </section>
    </>
  );
}

// ====================================================================== //
//  Admin games tab
// ====================================================================== //

function UserGamesTabAdmin({
  uid,
  gamesBase,
}: {
  uid: number;
  gamesBase: string;
}) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-games", uid],
    queryFn: () => superAdminApi.userGames(uid),
  });

  if (isLoading || !data) {
    return <div className="admin-card">⏳ …</div>;
  }
  if (data.items.length === 0) {
    return (
      <div className="admin-card">
        <div className="sa-detail-empty">
          <span className="icon">🎲</span>
          <div>{t("sa.user_detail.no_games", "No games yet")}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-card sa-detail-table-section">
      <div className="sa-detail-section-header">
        <h3>🎲 {t("sa.user_detail.tab_games", "Games")}</h3>
        <span className="hint">{data.total}</span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t("admin.user_detail_extra.games_time", "Time")}</th>
              <th>{t("admin.user_detail_extra.games_game", "Game")}</th>
              <th>{t("admin.user_detail_extra.games_role", "Role")}</th>
              <th>{t("admin.user_detail_extra.games_team", "Team")}</th>
              <th>{t("admin.user_detail_extra.games_result", "Result")}</th>
              <th style={{ textAlign: "right" }}>{t("admin.user_detail_extra.games_elo", "ELO")}</th>
              <th style={{ textAlign: "right" }}>{t("admin.user_detail_extra.games_xp", "XP")}</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((g: SaUserGame) => (
              <tr key={g.id}>
                <td style={{ color: "var(--muted)", fontSize: "0.8rem", whiteSpace: "nowrap" }}>
                  {new Date(g.played_at).toLocaleString()}
                </td>
                <td style={{ fontFamily: "monospace", fontSize: "0.78rem" }}>
                  <Link to={`${gamesBase}/${g.game_id}`}>{g.game_id.slice(0, 8)}…</Link>
                </td>
                <td>{g.role}</td>
                <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>{g.team}</td>
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
                <td style={{ textAlign: "right", color: g.elo_change >= 0 ? "#4ade80" : "#e74c3c" }}>
                  <strong>{g.elo_after}</strong>{" "}
                  <small>({g.elo_change >= 0 ? "+" : ""}{g.elo_change})</small>
                </td>
                <td style={{ textAlign: "right" }}>+{g.xp_earned}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ====================================================================== //
//  Admin achievements tab
// ====================================================================== //

function UserAchievementsTabAdmin({ uid }: { uid: number }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-achievements", uid],
    queryFn: () => superAdminApi.userAchievements(uid),
  });

  if (isLoading || !data) {
    return <div className="admin-card">⏳ …</div>;
  }
  if (data.items.length === 0) {
    return (
      <div className="admin-card">
        <div className="sa-detail-empty">
          <span className="icon">🏆</span>
          <div>
            {t("sa.user_detail_ext.achievements_empty", "No achievements yet")}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-grid">
      {data.items.map((a) => (
        <div key={a.code} className="admin-card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2.4rem" }}>{a.icon || "🏅"}</div>
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

// ====================================================================== //
//  Admin transactions tab
// ====================================================================== //

function UserTransactionsTabAdmin({ uid }: { uid: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-tx", uid],
    queryFn: () => superAdminApi.userTransactions(uid),
  });

  if (isLoading || !data) {
    return <div className="admin-card">⏳</div>;
  }
  if (data.items.length === 0) {
    return (
      <div className="admin-card">
        <div className="sa-detail-empty">
          <span className="icon">💸</span>
          <div>
            {t("sa.user_detail_ext.transactions_empty", "No transactions yet")}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-card sa-detail-table-section">
      <div className="sa-detail-section-header">
        <h3>💎 {t("sa.user_detail.tab_transactions", "Transactions")}</h3>
        <span className="hint">{data.total}</span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t("admin.user_detail_extra.tx_time", "Time")}</th>
              <th>{t("admin.user_detail_extra.tx_type", "Type")}</th>
              <th style={{ textAlign: "right" }}>💎</th>
              <th style={{ textAlign: "right" }}>💵</th>
              <th style={{ textAlign: "right" }}>⭐</th>
              <th>{t("admin.user_detail_extra.tx_item", "Item")}</th>
              <th>{t("admin.user_detail_extra.tx_status", "Status")}</th>
              <th>{t("admin.user_detail_extra.tx_note", "Note")}</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((tx: SaTransaction) => (
              <tr key={tx.id}>
                <td style={{ color: "var(--muted)", fontSize: "0.8rem", whiteSpace: "nowrap" }}>
                  {new Date(tx.created_at).toLocaleString()}
                </td>
                <td style={{ fontFamily: "monospace", fontSize: "0.78rem" }}>{tx.type}</td>
                <td
                  style={{
                    textAlign: "right",
                    color:
                      tx.diamonds_amount && tx.diamonds_amount > 0
                        ? "#4ade80"
                        : tx.diamonds_amount && tx.diamonds_amount < 0
                          ? "#e74c3c"
                          : "var(--muted)",
                  }}
                >
                  {tx.diamonds_amount ?? "—"}
                </td>
                <td style={{ textAlign: "right" }}>{tx.dollars_amount ?? "—"}</td>
                <td style={{ textAlign: "right" }}>{tx.stars_amount ?? "—"}</td>
                <td style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{tx.item ?? "—"}</td>
                <td>
                  <span
                    className={`badge ${
                      tx.status === "completed"
                        ? "green"
                        : tx.status === "failed"
                          ? "red"
                          : "yellow"
                    }`}
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
    </div>
  );
}

// ====================================================================== //
//  Webapp layout — preserved legacy
// ====================================================================== //

interface WebappLayoutProps {
  user: SaUserDetail;
  uid: number;
  usersBase: string;
  gamesBase: string;
  tab: Tab;
  setTab: (t: Tab) => void;
  sendOpen: boolean;
  setSendOpen: (b: boolean) => void;
  onLegacyBan: (reason: string) => void;
  onLegacyUnban: () => void;
  onLegacyGrant: (n: number) => void;
  onLegacyPremium: (n: number) => void;
  pendingFlags: {
    ban: boolean;
    unban: boolean;
    grant: boolean;
    premium: boolean;
  };
}

function WebappLayout({
  user,
  uid,
  usersBase,
  gamesBase,
  tab,
  setTab,
  sendOpen,
  setSendOpen,
  onLegacyBan,
  onLegacyUnban,
  onLegacyGrant,
  onLegacyPremium,
  pendingFlags,
}: WebappLayoutProps) {
  const { t } = useTranslation();

  const onBan = () => {
    // eslint-disable-next-line no-alert
    const reason = prompt(t("sa.user_detail.ban_prompt", "Reason:"));
    if (reason) onLegacyBan(reason);
  };
  const onGrant = () => {
    // eslint-disable-next-line no-alert
    const raw = prompt(t("sa.user_detail.grant_prompt", "Amount:"));
    const n = parseInt(raw || "0");
    if (n > 0) onLegacyGrant(n);
  };
  const onPremium = () => {
    // eslint-disable-next-line no-alert
    const raw = prompt(t("sa.user_detail.premium_prompt", "Days (1..365):"));
    const n = parseInt(raw || "0");
    if (n > 0 && n <= 365) onLegacyPremium(n);
  };

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
        <h2 style={{ margin: "0.5rem 0" }}>
          👤 {user.first_name} {user.is_premium && "👑"} {user.is_banned && "🚫"}
        </h2>
        <button
          type="button"
          className="sa-chip"
          onClick={() => setSendOpen(true)}
          style={{ padding: "0.35rem 0.7rem" }}
        >
          📨 {t("sa.send_msg.button", "Send message")}
        </button>
      </div>

      <p style={{ margin: 0, color: "var(--muted)", fontSize: 13 }}>
        #{String(user.id)} {user.username && `· @${user.username}`}
      </p>

      <SendMessageDialog
        userId={user.id}
        userName={user.first_name + (user.last_name ? " " + user.last_name : "")}
        open={sendOpen}
        onClose={() => setSendOpen(false)}
      />

      <div className="webapp-section" style={{ marginTop: "0.5rem" }}>
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
          {(["overview", "games", "achievements", "transactions"] as Tab[]).map((k) => (
            <button
              key={k}
              type="button"
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
              <WebappStat label="💎" value={user.diamonds} />
              <WebappStat label="💵" value={user.dollars} />
              <WebappStat label="⭐ XP" value={user.xp} />
              <WebappStat label="🎯 Lvl" value={user.level} />
              {user.stats && (
                <>
                  <WebappStat
                    label={t("sa.user_detail.games_total")}
                    value={user.stats.games_total}
                  />
                  <WebappStat
                    label={t("sa.user_detail.wins")}
                    value={user.stats.games_won}
                  />
                  <WebappStat label="🏆 ELO" value={user.stats.elo} />
                  <WebappStat
                    label={t("sa.user_detail.longest_streak")}
                    value={user.stats.longest_win_streak}
                  />
                </>
              )}
            </div>
          </div>

          <div className="webapp-section">
            <h3 style={{ marginTop: 0 }}>🛠 {t("sa.user_detail.actions")}</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {user.is_banned ? (
                <button
                  type="button"
                  className="sa-chip active"
                  disabled={pendingFlags.unban}
                  onClick={onLegacyUnban}
                >
                  ✅ {t("sa.users.unban", "Unban")}
                </button>
              ) : (
                <button
                  type="button"
                  className="sa-chip"
                  disabled={pendingFlags.ban}
                  onClick={onBan}
                  style={{ color: "#e74c3c" }}
                >
                  🚫 {t("sa.users.ban", "Ban")}
                </button>
              )}
              <button
                type="button"
                className="sa-chip"
                disabled={pendingFlags.grant}
                onClick={onGrant}
              >
                💎 {t("sa.users.grant_diamonds", "Grant diamonds")}
              </button>
              <button
                type="button"
                className="sa-chip"
                disabled={pendingFlags.premium}
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
            {user.is_banned && user.ban_reason && (
              <p style={{ marginTop: 8, fontSize: 13, color: "#e74c3c" }}>
                <strong>{t("admin.user_detail.ban_reason", "Ban reason")}:</strong>{" "}
                {user.ban_reason}
              </p>
            )}
          </div>
        </>
      )}
      {tab === "games" && <UserGamesTabWebapp uid={uid} />}
      {tab === "achievements" && <UserAchievementsTabWebapp uid={uid} />}
      {tab === "transactions" && (
        <UserTransactionsTabWebapp uid={uid} gamesBase={gamesBase} />
      )}
    </>
  );
}

function UserGamesTabWebapp({ uid }: { uid: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-games", uid],
    queryFn: () => superAdminApi.userGames(uid),
  });
  if (isLoading || !data) return <div className="webapp-section">⏳ …</div>;
  if (data.items.length === 0)
    return <div className="webapp-section">{t("sa.user_detail.no_games")}</div>;

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

function UserAchievementsTabWebapp({ uid }: { uid: number }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-achievements", uid],
    queryFn: () => superAdminApi.userAchievements(uid),
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
              <div>
                <strong>{a.name_i18n?.[lang] || a.name_i18n?.uz || a.code}</strong>
              </div>
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

function UserTransactionsTabWebapp({
  uid,
}: {
  uid: number;
  gamesBase: string;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["sa-user-tx", uid],
    queryFn: () => superAdminApi.userTransactions(uid),
  });
  if (isLoading || !data) return <div className="webapp-section">⏳</div>;

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

// ====================================================================== //
//  Small presentational helpers
// ====================================================================== //

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
      <div className="kpi-value" style={{ fontSize: "1.6rem" }}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

function Cell({
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

function WebappStat({ label, value }: { label: string; value: number | string }) {
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

function ActionTile({
  icon,
  label,
  hint,
  cta,
  onClick,
  disabled,
  variant,
}: {
  icon: string;
  label: string;
  hint: string;
  cta: string;
  onClick: () => void;
  disabled?: boolean;
  variant?: "danger";
}) {
  return (
    <div className={`sa-detail-action-tile ${variant === "danger" ? "danger" : ""}`}>
      <div className="icon">{icon}</div>
      <div className="body">
        <div className="label">{label}</div>
        <div className="hint">{hint}</div>
      </div>
      <div className="cta">
        <button
          type="button"
          className={`admin-btn ${variant === "danger" ? "danger" : "primary"}`}
          onClick={onClick}
          disabled={disabled}
        >
          {cta}
        </button>
      </div>
    </div>
  );
}
