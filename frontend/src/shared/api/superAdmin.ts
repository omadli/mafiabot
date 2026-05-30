/**
 * Unified super-admin API client.
 *
 * The backend exposes the same super-admin operations under two prefixes:
 *
 *   /api/admin/*  — JWT-protected, used by the website at /admin/*
 *   /api/sa/*     — Telegram initData-protected, used by the WebApp at /webapp/sa/*
 *
 * Pages that should work on BOTH surfaces import from this file instead of
 * the per-surface `adminApi` / `saApi` clients. The path is chosen at call
 * time from `authStore.token`: when a JWT is present we hit `/admin/*`;
 * otherwise we fall back to `/sa/*`. This keeps the same React component
 * mounted in either surface without it needing to know how the user
 * authenticated.
 *
 * Types are re-exported from `./sa` to avoid duplication.
 */

import { authStore } from "@shared/store/auth";

import { api } from "./client";
import type {
  GroupGamesResponse,
  GroupLeaderboardResponse,
  GroupSettings,
  GroupsPage,
  RoleConfig,
  RoleStat,
  SystemSettings,
  TopPlayer,
  TopPlayersSort,
  EmojiConfig,
} from "./sa";

export type {
  GroupGamesResponse,
  GroupLeaderboardResponse,
  GroupSettings,
  GroupsPage,
  RoleConfig,
  RoleStat,
  SystemSettings,
  TopPlayer,
  TopPlayersSort,
  EmojiConfig,
};

/**
 * Pick the auth-appropriate URL prefix for the current surface.
 *
 * The two backends are duplicated — same operations, different auth — so
 * the only thing the dispatcher decides is which prefix to send the
 * request to. JWT presence is the marker because the WebApp shell never
 * persists a token (initData is the auth medium there).
 */
function p(adminPath: string, saPath: string): string {
  return authStore.getState().token ? adminPath : saPath;
}

export const superAdminApi = {
  // === Identity ===

  // Both backends expose a "who am I" endpoint under different paths.
  me: async () =>
    (await api.get(p("/admin/me", "/sa/me"))).data,

  // === Role configs ===

  roleConfigs: async (): Promise<{ items: RoleConfig[] }> =>
    (await api.get(p("/admin/role-configs", "/sa/role-configs"))).data,

  updateRoleConfig: async (
    role: string,
    patch: Partial<Pick<
      RoleConfig,
      "name_uz" | "name_ru" | "name_en" | "static_emoji" | "custom_emoji_id" | "team" | "order_idx"
    >>,
  ): Promise<RoleConfig> =>
    (await api.post(p(`/admin/role-configs/${role}`, `/sa/role-configs/${role}`), patch)).data,

  // === Emoji configs ===

  emojiConfigs: async (): Promise<{ items: EmojiConfig[] }> =>
    (await api.get(p("/admin/emoji-configs", "/sa/emoji-configs"))).data,

  updateEmojiConfig: async (
    code: string,
    patch: Partial<Pick<
      EmojiConfig,
      "name_uz" | "name_ru" | "name_en" | "static_emoji" | "custom_emoji_id" | "category" | "order_idx"
    >>,
  ): Promise<EmojiConfig> =>
    (await api.post(p(`/admin/emoji-configs/${code}`, `/sa/emoji-configs/${code}`), patch)).data,

  // === Role stats ===

  roleStats: async (): Promise<{ roles: RoleStat[] }> =>
    (await api.get(p("/admin/role-stats", "/sa/role-stats"))).data,

  // === Top players ===

  topPlayers: async (
    sort: TopPlayersSort = "elo",
    limit = 50,
  ): Promise<{ sort: string; items: TopPlayer[] }> =>
    (await api.get(p("/admin/top-players", "/sa/top-players"), { params: { sort, limit } })).data,

  // === System settings ===

  systemSettings: async (): Promise<SystemSettings> =>
    (await api.get(p("/admin/system-settings", "/sa/system-settings"))).data,

  updateSystemSetting: async (
    section: "item_prices" | "rewards" | "exchange" | "premium",
    key: string,
    value: unknown,
  ): Promise<{ ok: boolean; section: string; key: string; value: unknown }> =>
    (
      await api.post(p("/admin/system-settings", "/sa/system-settings"), {
        section,
        key,
        value,
      })
    ).data,

  // === Groups browser ===

  groups: async (page = 1, pageSize = 50): Promise<GroupsPage> =>
    (
      await api.get(p("/admin/groups", "/sa/groups"), {
        params: { page, page_size: pageSize },
      })
    ).data,

  groupGames: async (
    groupId: number,
    page = 1,
    pageSize = 50,
  ): Promise<GroupGamesResponse> =>
    (
      await api.get(
        p(`/admin/groups/${groupId}/games`, `/sa/groups/${groupId}/games`),
        { params: { page, page_size: pageSize } },
      )
    ).data,

  groupLeaderboard: async (
    groupId: number,
    limit = 30,
  ): Promise<GroupLeaderboardResponse> =>
    (
      await api.get(
        p(`/admin/groups/${groupId}/leaderboard`, `/sa/groups/${groupId}/leaderboard`),
        { params: { limit } },
      )
    ).data,

  groupSettings: async (groupId: number): Promise<GroupSettings> =>
    (
      await api.get(
        p(`/admin/groups/${groupId}/settings`, `/sa/groups/${groupId}/settings`),
      )
    ).data,

  groupLive: async (groupId: number): Promise<unknown> =>
    (
      await api.get(
        p(`/admin/groups/${groupId}/live`, `/sa/groups/${groupId}/live`),
      )
    ).data,
};
