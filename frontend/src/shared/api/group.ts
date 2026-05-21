/**
 * Group-admin WebApp API client — typed wrappers around `/api/group/*`.
 *
 * Authenticated via the Telegram WebApp `initData` header pair
 * (`X-Telegram-Init-Data` + `X-Chat-Id`) which the shared axios
 * interceptor attaches automatically when running inside Telegram.
 *
 * Sibling clients:
 * - `adminApi` (admin.ts) → web admin `/api/admin/*` (JWT)
 * - `saApi`    (sa.ts)    → SA WebApp `/api/sa/*`    (initData)
 */

import { api } from "./client";

export interface GroupHistoryItem {
  id: string;
  winner_team: "citizens" | "mafia" | "singleton" | null;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  player_count: number;
  alive_at_end: number;
  bounty_per_winner: number | null;
}

export interface GroupLeaderboardItem {
  rank: number;
  user_id: number;
  first_name: string;
  username: string | null;
  elo: number;
  games_total: number;
  games_won: number;
  winrate: number;
}

export interface MessageTemplate {
  key: string;
  default: string;
  override: string;
  placeholders: string;
}

export const groupApi = {
  // === Settings (existing — typed) ===
  settings: async (groupId: number) =>
    (await api.get(`/group/${groupId}/settings`)).data,

  updateSettings: async (groupId: number, section: string, value: unknown) =>
    (await api.post(`/group/${groupId}/settings`, { section, value })).data,

  // === Leaderboard (paginated) ===
  leaderboard: async (
    groupId: number,
    page = 1,
    pageSize = 30,
  ): Promise<{ items: GroupLeaderboardItem[]; page: number; page_size: number; total: number }> =>
    (await api.get(`/group/${groupId}/leaderboard`, { params: { page, page_size: pageSize } })).data,

  // === History (paginated) ===
  history: async (
    groupId: number,
    page = 1,
    pageSize = 20,
  ): Promise<{ items: GroupHistoryItem[]; page: number; page_size: number; total: number }> =>
    (await api.get(`/group/${groupId}/history`, { params: { page, page_size: pageSize } })).data,

  // === Messages templates ===
  listMessages: async (
    groupId: number,
  ): Promise<{ locale: string; items: MessageTemplate[] }> =>
    (await api.get(`/group/${groupId}/messages`)).data,

  saveMessages: async (groupId: number, overrides: Record<string, string>) =>
    (await api.post(`/group/${groupId}/messages`, { overrides })).data,

  // === Atmosphere media (clear-only — uploads happen via bot command) ===
  clearAtmosphere: async (groupId: number, event: string) =>
    (await api.post(`/group/${groupId}/atmosphere_media/clear`, null, { params: { event } })).data,
};
