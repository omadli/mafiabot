/**
 * Backward-compat hook — wraps react-i18next so existing SuperAdmin pages
 * that imported useI18n keep working without churn.
 *
 * For new code prefer `useTranslation` from react-i18next directly:
 *
 *   import { useTranslation } from "react-i18next";
 *   const { t } = useTranslation();
 *   t("admin.dashboard.title")
 */

import { useTranslation } from "react-i18next";

import type { Locale } from "./index";

export function useI18n() {
  const { t: rawT, i18n } = useTranslation();

  // Map flat keys used in Phase 2 SuperAdmin pages onto the new nested JSON
  // namespaces. New code should use rawT() with full dotted paths.
  const FLAT_TO_NESTED: Record<string, string> = {
    loading: "loading",
    "sa-access-denied": "sa.access_denied",
    "sa-access-denied-hint": "sa.access_denied_hint",
    "sa-nav-dashboard": "sa.nav.dashboard",
    "sa-nav-roles": "sa.nav.roles",
    "sa-nav-players": "sa.nav.players",
    "sa-nav-groups": "sa.nav.groups",
    "sa-nav-system": "sa.nav.system",
    "dashboard-title": "sa.dashboard.title",
    "users-block": "sa.dashboard.users_block",
    "groups-block": "sa.dashboard.groups_block",
    "games-block": "sa.dashboard.games_block",
    "winrates-block": "sa.dashboard.winrates_block",
    "users-total": "sa.dashboard.users_total",
    "users-premium": "sa.dashboard.users_premium",
    "users-banned": "sa.dashboard.users_banned",
    "users-active-24h": "sa.dashboard.users_active_24h",
    "users-active-7d": "sa.dashboard.users_active_7d",
    "users-active-30d": "sa.dashboard.users_active_30d",
    "groups-total-active": "sa.dashboard.groups_total_active",
    "groups-blocked": "sa.dashboard.groups_blocked",
    "groups-onboarded": "sa.dashboard.groups_onboarded",
    "games-total": "sa.dashboard.games_total",
    "games-finished": "sa.dashboard.games_finished",
    "games-running": "sa.dashboard.games_running",
    "games-cancelled": "sa.dashboard.games_cancelled",
    "games-last-24h": "sa.dashboard.games_last_24h",
    "games-last-7d": "sa.dashboard.games_last_7d",
    "winrates-citizen": "sa.dashboard.winrates_citizen",
    "winrates-mafia": "sa.dashboard.winrates_mafia",
    "winrates-singleton": "sa.dashboard.winrates_singleton",
    "total-player-games": "sa.dashboard.total_player_games",
    "roles-title": "sa.roles.title",
    "roles-col-role": "sa.roles.col_role",
    "roles-col-games": "sa.roles.col_games",
    "roles-col-wins": "sa.roles.col_wins",
    "roles-col-winrate": "sa.roles.col_winrate",
    "roles-col-elo": "sa.roles.col_elo",
    "roles-col-xp": "sa.roles.col_xp",
    "players-title": "sa.players.title",
    "players-sort-elo": "sa.players.sort_elo",
    "players-sort-games-won": "sa.players.sort_games_won",
    "players-sort-games-total": "sa.players.sort_games_total",
    "players-sort-streak": "sa.players.sort_streak",
    "players-sort-level": "sa.players.sort_level",
    "players-col-rank": "sa.players.col_rank",
    "players-col-name": "sa.players.col_name",
    "players-col-level": "sa.players.col_level",
    "players-col-elo": "sa.players.col_elo",
    "players-col-games": "sa.players.col_games",
    "players-col-wins": "sa.players.col_wins",
    "players-col-winrate": "sa.players.col_winrate",
    "players-col-streak": "sa.players.col_streak",
    "groups-title": "sa.groups.title",
    "groups-col-id": "sa.groups.col_id",
    "groups-col-title": "sa.groups.col_title",
    "groups-col-status": "sa.groups.col_status",
    "groups-col-games": "sa.groups.col_games",
    "groups-col-last-game": "sa.groups.col_last_game",
    "group-status-active": "sa.groups.status_active",
    "group-status-blocked": "sa.groups.status_blocked",
    "group-status-not-onboarded": "sa.groups.status_not_onboarded",
    "group-back": "sa.group_detail.back",
    "group-tab-games": "sa.group_detail.tab_games",
    "group-tab-leaderboard": "sa.group_detail.tab_leaderboard",
    "group-tab-settings": "sa.group_detail.tab_settings",
    "group-games-title": "sa.group_detail.games_title",
    "group-leaderboard-title": "sa.group_detail.leaderboard_title",
    "group-settings-title": "sa.group_detail.settings_title",
    "system-title": "sa.system.title",
    "system-prices": "sa.system.prices",
    "system-rewards": "sa.system.rewards",
    "system-exchange": "sa.system.exchange",
    "system-premium": "sa.system.premium",
    "system-save": "save",
  };

  const t = (key: string, fallback?: string): string => {
    const mappedKey = FLAT_TO_NESTED[key] ?? key;
    const result = rawT(mappedKey);
    // If react-i18next returned the key itself, treat as missing → fallback
    if (result === mappedKey && fallback) return fallback;
    return result;
  };

  const setLocale = (next: Locale) => {
    i18n.changeLanguage(next);
  };

  return {
    t,
    locale: (i18n.language as Locale) ?? "uz",
    setLocale,
  };
}
