/**
 * Web admin API client — typed wrappers around /api/admin/* endpoints.
 *
 * Authentication: JWT (Bearer) attached automatically by the shared axios
 * interceptor. The backend's `get_current_admin` dependency validates the
 * token against an AdminAccount row.
 *
 * Sibling: `saApi` (sa.ts) — Telegram-initData-authenticated `/api/sa/*`
 * endpoints, used inside the Telegram WebApp.
 *
 * Both surfaces (web `/admin` and webapp `/webapp/sa`) cover the same
 * super-admin concerns, but each has its own auth dependency, so we keep
 * the typed wrappers separate.
 */

import { api } from "./client";
import type {
  EmojiConfig,
  RoleConfig,
  RoleStat,
  TopPlayer,
  TopPlayersSort,
  RoleWinrate,
  SystemSettings,
  GroupSettings,
} from "./sa";

export const adminApi = {
  // === Role configs (mirrors /sa/role-configs, JWT auth) ===
  roleConfigs: async (): Promise<{ items: RoleConfig[] }> =>
    (await api.get("/admin/role-configs")).data,

  updateRoleConfig: async (
    role: string,
    patch: Partial<Pick<
      RoleConfig,
      | "name_uz" | "name_ru" | "name_en"
      | "static_emoji" | "custom_emoji_id"
      | "team" | "order_idx"
    >>,
  ): Promise<RoleConfig> =>
    (await api.post(`/admin/role-configs/${role}`, patch)).data,

  // === Emoji configs (mirrors /sa/emoji-configs, JWT auth) ===
  emojiConfigs: async (): Promise<{ items: EmojiConfig[] }> =>
    (await api.get("/admin/emoji-configs")).data,

  updateEmojiConfig: async (
    code: string,
    patch: Partial<Pick<
      EmojiConfig,
      | "name_uz" | "name_ru" | "name_en"
      | "static_emoji" | "custom_emoji_id"
      | "category" | "order_idx"
    >>,
  ): Promise<EmojiConfig> =>
    (await api.post(`/admin/emoji-configs/${code}`, patch)).data,

  // === Role stats (mirrors /sa/role-stats) ===
  roleStats: async (): Promise<{ roles: RoleStat[] }> =>
    (await api.get("/admin/role-stats")).data,

  // === Top players (mirrors /sa/top-players) ===
  topPlayers: async (
    sort: TopPlayersSort = "elo",
    limit = 50,
  ): Promise<{ sort: string; items: TopPlayer[] }> =>
    (await api.get("/admin/top-players", { params: { sort, limit } })).data,

  // === System settings (mirrors /sa/system-settings) ===
  systemSettings: async (): Promise<SystemSettings> =>
    (await api.get("/admin/system-settings")).data,

  updateSystemSetting: async (
    section: "item_prices" | "rewards" | "exchange" | "premium",
    key: string,
    value: unknown,
  ): Promise<{ ok: boolean; section: string; key: string; value: unknown }> =>
    (await api.post("/admin/system-settings", { section, key, value })).data,

  // === Group detail (games / leaderboard / settings) ===
  groupGames: async (groupId: number, page = 1, pageSize = 50):
    Promise<{ group_id: number; total: number; page: number; items: GroupGameRow[] }> =>
    (await api.get(`/admin/groups/${groupId}/games`, {
      params: { page, page_size: pageSize },
    })).data,

  groupLeaderboard: async (groupId: number, limit = 30):
    Promise<{ group_id: number; items: GroupLeaderboardRow[] }> =>
    (await api.get(`/admin/groups/${groupId}/leaderboard`, { params: { limit } })).data,

  groupSettings: async (groupId: number): Promise<GroupSettings> =>
    (await api.get(`/admin/groups/${groupId}/settings`)).data,

  updateGroupSettings: async (
    groupId: number,
    section: string,
    value: unknown,
  ): Promise<{ ok: boolean; section: string }> =>
    (await api.post(`/admin/groups/${groupId}/settings`, { section, value })).data,

  // === Charts (role-winrates mirror) ===
  chartRoleWinrates: async (): Promise<{ items: RoleWinrate[] }> =>
    (await api.get("/admin/charts/role-winrates")).data,
};

export interface GroupGameRow {
  id: string;
  status: string;
  winner_team: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  players_count: number;
  bounty_per_winner: number | null;
}

export interface GroupLeaderboardRow {
  rank: number;
  user_id: number;
  first_name: string;
  username: string | null;
  elo: number;
  games_total: number;
  games_won: number;
  winrate_pct: number;
}
