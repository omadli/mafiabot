/**
 * SuperAdmin API client — typed wrappers around /api/sa/* endpoints.
 *
 * Authentication: Telegram WebApp initData is automatically attached to every
 * request by the shared axios interceptor (client.ts). The backend's
 * get_current_super_admin dependency verifies the HMAC and checks the
 * Telegram user.id against SUPER_ADMIN_TELEGRAM_IDS env.
 */

import { api } from "./client";

// === Identity ===

export interface SuperAdminMe {
  telegram_id: number;
  first_name: string;
  username: string | null;
  language_code: "uz" | "ru" | "en";
}

export const saApi = {
  me: async (): Promise<SuperAdminMe> => (await api.get("/sa/me")).data,

  // === Global stats ===
  globalStats: async (): Promise<GlobalStats> => (await api.get("/sa/global-stats")).data,

  // === Role stats ===
  roleStats: async (): Promise<{ roles: RoleStat[] }> => (await api.get("/sa/role-stats")).data,

  // === Top players ===
  topPlayers: async (
    sort: TopPlayersSort = "elo",
    limit = 50,
  ): Promise<{ sort: string; items: TopPlayer[] }> =>
    (await api.get("/sa/top-players", { params: { sort, limit } })).data,

  // === Groups browser ===
  groups: async (page = 1, pageSize = 50): Promise<GroupsPage> =>
    (await api.get("/sa/groups", { params: { page, page_size: pageSize } })).data,

  // === Per-group ===
  groupGames: async (
    groupId: number,
    page = 1,
    pageSize = 50,
  ): Promise<GroupGamesResponse> =>
    (
      await api.get(`/sa/groups/${groupId}/games`, {
        params: { page, page_size: pageSize },
      })
    ).data,

  groupLeaderboard: async (groupId: number, limit = 30): Promise<GroupLeaderboardResponse> =>
    (await api.get(`/sa/groups/${groupId}/leaderboard`, { params: { limit } })).data,

  groupSettings: async (groupId: number): Promise<GroupSettings> =>
    (await api.get(`/sa/groups/${groupId}/settings`)).data,

  groupLive: async (groupId: number): Promise<unknown> =>
    (await api.get(`/sa/groups/${groupId}/live`)).data,

  updateGroupSettings: async (
    groupId: number,
    section: string,
    value: unknown,
  ): Promise<{ ok: boolean; section: string }> =>
    (
      await api.post(`/sa/groups/${groupId}/settings`, {
        section,
        value,
      })
    ).data,

  // === System settings ===
  systemSettings: async (): Promise<SystemSettings> =>
    (await api.get("/sa/system-settings")).data,

  updateSystemSetting: async (
    section: "item_prices" | "rewards" | "exchange" | "premium",
    key: string,
    value: unknown,
  ): Promise<{ ok: boolean; section: string; key: string; value: unknown }> =>
    (await api.post("/sa/system-settings", { section, key, value })).data,

  // === Role configs (per-role names + emojis, cached) ===
  // Note: `/sa/role-configs` is initData-auth (Telegram WebApp).
  // For the web `/admin` (JWT auth) use `adminApi.roleConfigs()` from admin.ts.
  roleConfigs: async (): Promise<{ items: RoleConfig[] }> =>
    (await api.get("/sa/role-configs")).data,

  updateRoleConfig: async (
    role: string,
    patch: Partial<Pick<
      RoleConfig,
      | "name_uz" | "name_ru" | "name_en"
      | "static_emoji" | "custom_emoji_id"
      | "team" | "order_idx"
    >>,
  ): Promise<RoleConfig> =>
    (await api.post(`/sa/role-configs/${role}`, patch)).data,

  // === Emoji configs (scene / item / action / status / currency) ===
  emojiConfigs: async (): Promise<{ items: EmojiConfig[] }> =>
    (await api.get("/sa/emoji-configs")).data,

  updateEmojiConfig: async (
    code: string,
    patch: Partial<Pick<
      EmojiConfig,
      | "name_uz" | "name_ru" | "name_en"
      | "static_emoji" | "custom_emoji_id"
      | "category" | "order_idx"
    >>,
  ): Promise<EmojiConfig> =>
    (await api.post(`/sa/emoji-configs/${code}`, patch)).data,

  // === Charts ===
  chartElo: async (): Promise<{ bins: { label: string; count: number }[] }> =>
    (await api.get("/sa/charts/elo")).data,

  chartGamesPerDay: async (days = 30): Promise<{ series: { date: string; count: number }[] }> =>
    (await api.get("/sa/charts/games-per-day", { params: { days } })).data,

  chartCohort: async (): Promise<CohortChart> => (await api.get("/sa/charts/cohort")).data,

  chartRoleWinrates: async (): Promise<{ items: RoleWinrate[] }> =>
    (await api.get("/sa/charts/role-winrates")).data,

  // === Users browser + moderation ===
  users: async (params: {
    search?: string; is_banned?: boolean; is_premium?: boolean;
    page?: number; page_size?: number;
  } = {}): Promise<SaUsersPage> =>
    (await api.get("/sa/users", { params })).data,

  user: async (userId: number): Promise<SaUserDetail> =>
    (await api.get(`/sa/users/${userId}`)).data,

  banUser: async (userId: number, reason: string, durationHours: number | null = null) =>
    (await api.post(`/sa/users/${userId}/ban`, {
      reason, duration_hours: durationHours,
    })).data,

  unbanUser: async (userId: number) =>
    (await api.post(`/sa/users/${userId}/unban`)).data,

  grantDiamonds: async (userId: number, amount: number, reason = "sa grant") =>
    (await api.post(`/sa/users/${userId}/grant-diamonds`, { amount, reason })).data,

  grantPremium: async (userId: number, days: number) =>
    (await api.post(`/sa/users/${userId}/grant-premium`, { days })).data,

  userTransactions: async (userId: number, page = 1, page_size = 50):
    Promise<{ total: number; page: number; items: SaTransaction[] }> =>
    (await api.get(`/sa/users/${userId}/transactions`, { params: { page, page_size } })).data,

  userGames: async (userId: number, page = 1, page_size = 20):
    Promise<{ total: number; page: number; items: SaUserGame[] }> =>
    (await api.get(`/sa/users/${userId}/games`, { params: { page, page_size } })).data,

  userAchievements: async (userId: number): Promise<{ items: SaAchievement[] }> =>
    (await api.get(`/sa/users/${userId}/achievements`)).data,

  // === Groups moderation ===
  blockGroup: async (groupId: number, reason: string) =>
    (await api.post(`/sa/groups/${groupId}/block`, { reason })).data,

  unblockGroup: async (groupId: number) =>
    (await api.post(`/sa/groups/${groupId}/unblock`)).data,

  // === Games list + replay ===
  games: async (params: {
    status?: string; group_id?: number; page?: number; page_size?: number;
  } = {}): Promise<SaGamesPage> =>
    (await api.get("/sa/games", { params })).data,

  game: async (gameId: string): Promise<SaGameDetail> =>
    (await api.get(`/sa/games/${gameId}`)).data,

  // === Audit log ===
  audit: async (params: {
    action?: string; actor_id?: number; page?: number; page_size?: number;
  } = {}): Promise<SaAuditPage> =>
    (await api.get("/sa/audit", { params })).data,
};

export interface SaUserListItem {
  id: number;
  username: string | null;
  first_name: string;
  diamonds: number;
  dollars: number;
  xp: number;
  level: number;
  is_premium: boolean;
  is_banned: boolean;
  games_total: number;
  elo: number;
  created_at: string;
}

export interface SaUsersPage {
  total: number;
  page: number;
  page_size: number;
  items: SaUserListItem[];
}

export interface SaUserDetail extends SaUserListItem {
  last_name: string | null;
  language_code: string | null;
  premium_expires_at: string | null;
  banned_until: string | null;
  ban_reason: string | null;
  afk_warnings: number;
  joined_at: string;
  stats: {
    games_total: number;
    games_won: number;
    games_lost: number;
    elo: number;
    longest_win_streak: number;
    role_stats: Record<string, unknown>;
    citizen_wins: number;
    mafia_wins: number;
    singleton_wins: number;
  } | null;
}

export interface SaTransaction {
  id: string;
  type: string;
  stars_amount: number | null;
  diamonds_amount: number | null;
  dollars_amount: number | null;
  item: string | null;
  status: string;
  note: string | null;
  created_at: string;
}

export interface SaUserGame {
  id: string;
  game_id: string;
  group_id: number;
  role: string;
  team: string;
  won: boolean;
  survived: boolean;
  death_reason: string | null;
  elo_before: number;
  elo_after: number;
  elo_change: number;
  xp_earned: number;
  played_at: string;
}

export interface SaAchievement {
  code: string;
  name_i18n: Record<string, string>;
  icon: string | null;
  diamonds_reward: number;
  unlocked_at: string;
}

export interface SaGameListItem {
  id: string;
  group_id: number;
  status: string;
  winner_team: string | null;
  started_at: string | null;
  finished_at: string | null;
  bounty_per_winner: number | null;
}

export interface SaGamesPage {
  total: number;
  page: number;
  page_size: number;
  items: SaGameListItem[];
}

export interface SaGameDetail extends SaGameListItem {
  history: unknown;
  settings_snapshot: unknown;
  bounty_pool: number | null;
}

export interface SaAuditEntry {
  id: string;
  actor_id: number | null;
  actor_admin_id: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  payload: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface SaAuditPage {
  total: number;
  page: number;
  page_size: number;
  items: SaAuditEntry[];
}

export interface CohortChart {
  new_users: number;
  active_7d: number;
  active_30d: number;
  retention_7d: number;
  retention_30d: number;
}

export interface RoleWinrate {
  role: string;
  games: number;
  wins: number;
  winrate_pct: number;
}

// === Types ===

export interface GlobalStats {
  generated_at: string;
  users: {
    total: number;
    premium: number;
    banned: number;
    active_24h: number;
    active_7d: number;
    active_30d: number;
  };
  groups: {
    total_active: number;
    blocked: number;
    onboarded: number;
  };
  games: {
    total: number;
    finished: number;
    running: number;
    cancelled: number;
    last_24h: number;
    last_7d: number;
  };
  winrates: {
    total_player_games: number;
    citizen_wins: number;
    mafia_wins: number;
    singleton_wins: number;
    citizen_pct: number;
    mafia_pct: number;
    singleton_pct: number;
  };
}

export interface RoleStat {
  role: string;
  games_played: number;
  wins: number;
  winrate_pct: number;
  avg_elo_change: number;
  avg_xp_earned: number;
}

export type TopPlayersSort =
  | "elo"
  | "games_won"
  | "games_total"
  | "longest_win_streak"
  | "level";

export interface TopPlayer {
  rank: number;
  user_id: number;
  first_name: string;
  username: string | null;
  is_premium: boolean;
  level: number;
  xp: number;
  elo: number;
  games_total: number;
  games_won: number;
  winrate_pct: number;
  longest_win_streak: number;
  citizen_wins: number;
  mafia_wins: number;
  singleton_wins: number;
}

export interface GroupsPage {
  total: number;
  page: number;
  items: GroupSummary[];
}

export interface GroupSummary {
  id: number;
  title: string;
  is_active: boolean;
  is_blocked: boolean;
  onboarding_completed: boolean;
  games_total: number;
  last_game_at: string | null;
  created_at: string | null;
}

export interface GroupGamesResponse {
  group_id: number;
  total: number;
  page: number;
  items: GroupGameSummary[];
}

export interface GroupGameSummary {
  id: string;
  status: string;
  winner_team: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  players_count: number;
  bounty_per_winner: number | null;
}

export interface GroupLeaderboardResponse {
  group_id: number;
  items: GroupLeaderboardEntry[];
}

export interface GroupLeaderboardEntry {
  rank: number;
  user_id: number;
  first_name: string;
  username: string | null;
  elo: number;
  games_total: number;
  games_won: number;
  winrate_pct: number;
}

export interface GroupSettings {
  group_id: number;
  language: string;
  roles: Record<string, boolean>;
  timings: Record<string, number>;
  silence: Record<string, boolean>;
  items_allowed: Record<string, boolean>;
  afk: Record<string, unknown>;
  permissions: Record<string, unknown>;
  gameplay: Record<string, unknown>;
  display: Record<string, boolean>;
  messages: Record<string, unknown>;
  atmosphere_media: Record<string, string | null>;
}

export type RoleTeam = "civilians" | "mafia" | "singletons";

export interface RoleConfig {
  role: string;
  team: RoleTeam;
  name_uz: string;
  name_ru: string;
  name_en: string;
  static_emoji: string;
  custom_emoji_id: string;
  order_idx: number;
  updated_at: string | null;
  updated_by_tg_id: number | null;
}

export type EmojiCategory = "scene" | "status" | "item" | "action" | "currency";

export interface EmojiConfig {
  code: string;
  category: EmojiCategory;
  name_uz: string;
  name_ru: string;
  name_en: string;
  static_emoji: string;
  custom_emoji_id: string;
  order_idx: number;
  updated_at: string | null;
  updated_by_tg_id: number | null;
}

export interface SystemSettings {
  item_prices: Record<string, { dollars: number; diamonds: number }>;
  rewards: Record<string, number>;
  exchange: Record<string, number | boolean>;
  premium: Record<string, number>;
  updated_at: string | null;
  updated_by_tg_id: number | null;
}
