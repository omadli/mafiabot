/**
 * Shared types for the live Mafia game state shape exposed by both:
 *   - GET /admin/groups/{group_id}/live   (real-time spectator)
 *   - GET /api/sa/sandbox/games/{id}/state (sandbox)
 *
 * Schema mirrors `backend/app/core/state.py::GameState`. Any drift
 * between the two would break the dashboard, so this file is the
 * single source of truth on the frontend side — both
 * `useLiveGame` and the new `useSandboxGame` import from here.
 */

export interface LivePlayer {
  user_id: number;
  username: string | null;
  first_name: string;
  join_order: number;
  role: string;
  team: string;
  alive: boolean;
  items_active: string[];
  died_at_round: number | null;
  died_at_phase: string | null;
  died_reason: string | null;
  extra?: Record<string, unknown>;
}

export interface LiveNightAction {
  actor_id: number;
  role: string;
  action_type: string;
  target_id: number | null;
  used_item: string | null;
}

export interface LiveVote {
  voter_id: number;
  target_id: number;
  weight: number;
}

export interface LiveRoundLog {
  round_num: number;
  night_actions: LiveNightAction[];
  night_deaths: number[];
  day_votes: LiveVote[];
  hanged: number | null;
  last_words: Record<string, string>;
  extra: {
    hanging_confirm?: {
      target_id?: number;
      yes?: Record<string, number>;
      no?: Record<string, number>;
    };
    pending_hang_target?: number;
    hang_yes_total?: number;
    hang_no_total?: number;
    hang_cancelled?: boolean;
    lawyer_protected?: number[];
    [key: string]: unknown;
  };
}

export interface LiveGameState {
  id: string;
  group_id: number;
  chat_id: number;
  phase: string;
  round_num: number;
  phase_ends_at: number | null;
  players: LivePlayer[];
  current_actions: Record<string, LiveNightAction>;
  current_votes: Record<string, LiveVote>;
  rounds: LiveRoundLog[];
  winner_team: string | null;
  winner_user_ids: number[];
  started_at: number | null;
  finished_at: number | null;
  bounty_per_winner: number | null;
  bounty_pool: number | null;
}
