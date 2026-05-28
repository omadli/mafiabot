/**
 * Sandbox API client — typed wrappers around `/api/sa/sandbox/*`.
 *
 * Backed by `backend/app/api/routers/sandbox.py`. Authentication: JWT
 * (Bearer) attached automatically by the shared axios interceptor —
 * the backend additionally requires the `superadmin` role.
 *
 * The shapes mirror the Pydantic models in the backend router. Keep
 * them in sync — any drift between this file and the backend schema
 * will manifest as runtime undefined-field errors in the dashboard.
 */

import { api } from "./client";
import type { LiveGameState } from "./liveGame";

// === Enums (string-literal mirrors of the backend) =========================

export type SandboxStatus =
  | "created"
  | "running"
  | "finished"
  | "destroyed"
  | "errored";

export type SandboxAutoPlayMode = "paused" | "auto" | "random_actions";

export type SandboxTimingPreset = "fast" | "normal" | "slow" | "manual";

export type TranscriptEntryType =
  | "send"
  | "edit"
  | "delete"
  | "toast"
  | "pin"
  | "unpin";

export type TranscriptScope = "group" | "dm" | "mafia_chat" | "dead_chat";

// === Request shapes =========================================================

export interface SandboxCreateRequest {
  n_players: number; // 4..30
  language?: "uz" | "ru" | "en";
  mafia_ratio?: "low" | "high";
  auto_play_mode?: SandboxAutoPlayMode;
  timing_preset?: SandboxTimingPreset;
  roles_enabled?: Record<string, boolean>;
  timings?: Record<string, number>;
  custom_names?: string[];
  seed?: number;
  /** Create + start in a single call — saves a round-trip from the dashboard. */
  start_immediately?: boolean;
}

export interface SandboxCallbackRequest {
  user_id: number;
  callback_data: string;
  message_id: number;
  /** Default: same as `user_id` (DM scope). Pass explicitly for group buttons. */
  chat_id?: number;
}

// === Response shapes =======================================================

export interface SandboxPlayer {
  user_id: number;
  first_name: string;
  username: string | null;
  language_code: string;
  /** Populated once `start_sandbox` distributes roles. */
  role: string | null;
  team: string | null;
}

export interface SandboxSummary {
  sandbox_id: string;
  fake_group_id: number;
  status: SandboxStatus;
  n_players: number;
  auto_play_mode: SandboxAutoPlayMode;
  timing_preset: SandboxTimingPreset;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  winner_team: string | null;
  transcript_summary: {
    n_entries: number;
    group_msg_count: number;
    dm_msg_count: number;
    mafia_chat_count: number;
    dead_chat_count: number;
  } | null;
}

export interface SandboxDetail extends SandboxSummary {
  settings_snapshot: Record<string, unknown>;
  fake_users_snapshot: SandboxPlayer[];
  final_state: Record<string, unknown> | null;
}

export interface InlineKeyboardButton {
  text: string;
  callback_data?: string;
  url?: string;
}

export interface InlineKeyboardMarkup {
  inline_keyboard: InlineKeyboardButton[][];
}

export interface TranscriptEntry {
  seq: number;
  ts: number; // unix seconds (float — sub-second precision)
  type: TranscriptEntryType;
  scope: TranscriptScope;
  chat_id: number;
  target_user_id: number | null;
  message_id: number;
  ref_message_id: number | null;
  text: string | null;
  parse_mode: string | null;
  reply_markup: InlineKeyboardMarkup | null;
  media: {
    type: "photo" | "animation" | "video" | "invoice";
    ref?: string;
    caption?: string | null;
    [k: string]: unknown;
  } | null;
  extra?: Record<string, unknown>;
}

export interface TranscriptPage {
  entries: TranscriptEntry[];
  /** Pass back as `since` on the next call to continue the stream. */
  next_since: number;
}

// === Client ================================================================

const BASE = "/sa/sandbox/games";

export const sandboxApi = {
  /** Create a fresh sandbox; optionally start it in the same call. */
  create: async (payload: SandboxCreateRequest): Promise<SandboxDetail> =>
    (await api.post(BASE, payload)).data,

  /** List existing sandboxes — newest first. */
  list: async (
    statusFilter: "active" | "all" | "finished" = "all",
    limit = 50,
  ): Promise<SandboxSummary[]> =>
    (
      await api.get(BASE, {
        params: { status: statusFilter, limit },
      })
    ).data,

  /** Fetch one sandbox row with full settings + (post-mortem) `final_state`. */
  get: async (sandboxId: string): Promise<SandboxDetail> =>
    (await api.get(`${BASE}/${sandboxId}`)).data,

  /** Start a CREATED session — assigns roles, kicks off the phase loop. */
  start: async (sandboxId: string): Promise<SandboxDetail> =>
    (await api.post(`${BASE}/${sandboxId}/start`)).data,

  /** Stop the session (keeps the row + transcript for post-mortem). */
  stop: async (sandboxId: string): Promise<SandboxDetail> =>
    (await api.post(`${BASE}/${sandboxId}/stop`)).data,

  /** Permanently remove the row + transcript. No-op if already gone. */
  destroy: async (sandboxId: string): Promise<{ ok: boolean }> =>
    (await api.delete(`${BASE}/${sandboxId}`)).data,

  /** Stop + create-fresh with the same config; returns the NEW session. */
  restart: async (sandboxId: string): Promise<SandboxDetail> =>
    (await api.post(`${BASE}/${sandboxId}/restart`)).data,

  /** Manually advance one phase (manual-mode or operator click). */
  advance: async (sandboxId: string): Promise<{ phase: string | null }> =>
    (await api.post(`${BASE}/${sandboxId}/advance`)).data,

  /** Dashboard button click → synthetic CallbackQuery → engine handler. */
  callback: async (
    sandboxId: string,
    payload: SandboxCallbackRequest,
  ): Promise<{ ok: boolean }> =>
    (await api.post(`${BASE}/${sandboxId}/callback`, payload)).data,

  /** Live GameState shape (same schema as `/admin/groups/{gid}/live`). */
  state: async (sandboxId: string): Promise<LiveGameState> =>
    (await api.get(`${BASE}/${sandboxId}/state`)).data,

  /** Paginated transcript fetch. Use the returned `next_since` for the
   *  next page. Live updates should come from the `transcript_append`
   *  WS event; this endpoint is for initial fill + reconnect gap-fill. */
  transcript: async (
    sandboxId: string,
    since = 0,
    limit = 200,
  ): Promise<TranscriptPage> =>
    (
      await api.get(`${BASE}/${sandboxId}/transcript`, {
        params: { since, limit },
      })
    ).data,
};

// Re-export key types so consumers can import everything from one place.
export type {
  LiveGameState,
  LiveNightAction,
  LivePlayer,
  LiveRoundLog,
  LiveVote,
} from "./liveGame";
