from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(64),
    "first_name" VARCHAR(128) NOT NULL,
    "last_name" VARCHAR(128),
    "language_code" VARCHAR(8) NOT NULL,
    "diamonds" INT NOT NULL,
    "dollars" INT NOT NULL,
    "xp" INT NOT NULL,
    "level" INT NOT NULL,
    "is_premium" INT NOT NULL,
    "premium_expires_at" TIMESTAMP,
    "is_banned" INT NOT NULL,
    "banned_until" TIMESTAMP,
    "ban_reason" VARCHAR(256),
    "afk_warnings" INT NOT NULL,
    "active_game_id" CHAR(36),
    "joined_at" TIMESTAMP NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
) /* Telegram user. */;
CREATE TABLE IF NOT EXISTS "user_inventories" (
    "shield" INT NOT NULL,
    "killer_shield" INT NOT NULL,
    "vote_shield" INT NOT NULL,
    "rifle" INT NOT NULL,
    "mask" INT NOT NULL,
    "fake_document" INT NOT NULL,
    "special_role" INT NOT NULL,
    "settings" JSON NOT NULL,
    "user_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "users" ("id") ON DELETE CASCADE
) /* Foydalanuvchining qurol va himoyalari. */;
CREATE TABLE IF NOT EXISTS "groups" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(256) NOT NULL,
    "is_active" INT NOT NULL,
    "is_blocked" INT NOT NULL,
    "onboarding_completed" INT NOT NULL,
    "bot_admin_perms" JSON NOT NULL,
    "invite_link" VARCHAR(256),
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
) /* Telegram group\\/supergroup. */;
CREATE TABLE IF NOT EXISTS "group_settings" (
    "language" VARCHAR(8) NOT NULL,
    "roles" JSON NOT NULL,
    "timings" JSON NOT NULL,
    "silence" JSON NOT NULL,
    "items_allowed" JSON NOT NULL,
    "role_distribution" JSON NOT NULL,
    "afk" JSON NOT NULL,
    "permissions" JSON NOT NULL,
    "gameplay" JSON NOT NULL,
    "display" JSON NOT NULL,
    "messages" JSON NOT NULL,
    "group_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "groups" ("id") ON DELETE CASCADE
) /* Guruh sozlamalari — har turi alohida JSONField. */;
CREATE TABLE IF NOT EXISTS "games" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "status" VARCHAR(9) NOT NULL /* WAITING: waiting\nRUNNING: running\nFINISHED: finished\nCANCELLED: cancelled */,
    "started_at" TIMESTAMP NOT NULL,
    "finished_at" TIMESTAMP,
    "winner_team" VARCHAR(9) /* CITIZENS: citizens\nMAFIA: mafia\nSINGLETON: singleton */,
    "bounty_per_winner" INT,
    "bounty_pool" INT,
    "settings_snapshot" JSON NOT NULL,
    "history" JSON NOT NULL,
    "bounty_initiator_id" BIGINT REFERENCES "users" ("id") ON DELETE SET NULL,
    "group_id" BIGINT NOT NULL REFERENCES "groups" ("id") ON DELETE CASCADE
) /* A single Mafia game session. */;
CREATE INDEX IF NOT EXISTS "idx_games_group_i_24f813" ON "games" ("group_id", "started_at");
CREATE TABLE IF NOT EXISTS "game_results" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "role" VARCHAR(32) NOT NULL,
    "team" VARCHAR(16) NOT NULL,
    "won" INT NOT NULL,
    "survived" INT NOT NULL,
    "death_round" INT,
    "death_phase" VARCHAR(16),
    "death_reason" VARCHAR(64),
    "actions_count" INT NOT NULL,
    "successful_actions" INT NOT NULL,
    "received_votes" INT NOT NULL,
    "cast_votes" INT NOT NULL,
    "afk_turns" INT NOT NULL,
    "elo_before" INT NOT NULL,
    "elo_after" INT NOT NULL,
    "elo_change" INT NOT NULL,
    "xp_earned" INT NOT NULL,
    "dollars_earned" INT NOT NULL,
    "game_duration_seconds" INT NOT NULL,
    "game_player_count" INT NOT NULL,
    "played_at" TIMESTAMP NOT NULL,
    "game_id" CHAR(36) NOT NULL REFERENCES "games" ("id") ON DELETE CASCADE,
    "group_id" BIGINT REFERENCES "groups" ("id") ON DELETE SET NULL,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* ★ Data warehouse: 1 row per (game, user). Source of truth for all analytics. */;
CREATE INDEX IF NOT EXISTS "idx_game_result_user_id_c337d6" ON "game_results" ("user_id", "played_at");
CREATE INDEX IF NOT EXISTS "idx_game_result_user_id_8a3d88" ON "game_results" ("user_id", "role");
CREATE INDEX IF NOT EXISTS "idx_game_result_group_i_d91de8" ON "game_results" ("group_id", "played_at");
CREATE INDEX IF NOT EXISTS "idx_game_result_user_id_acb0f1" ON "game_results" ("user_id", "group_id", "played_at");
CREATE TABLE IF NOT EXISTS "group_stats" (
    "total_games" INT NOT NULL,
    "total_unique_players" INT NOT NULL,
    "active_players_30d" INT NOT NULL,
    "avg_game_duration_seconds" REAL NOT NULL,
    "avg_player_count" REAL NOT NULL,
    "citizens_winrate" REAL NOT NULL,
    "mafia_winrate" REAL NOT NULL,
    "singleton_winrate" REAL NOT NULL,
    "most_played_role" VARCHAR(32),
    "last_game_at" TIMESTAMP,
    "group_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "groups" ("id") ON DELETE CASCADE
) /* Group-level aggregate (balance, retention, activity). */;
CREATE TABLE IF NOT EXISTS "group_user_stats" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "games_total" INT NOT NULL,
    "games_won" INT NOT NULL,
    "role_stats" JSON NOT NULL,
    "elo" INT NOT NULL,
    "xp" INT NOT NULL,
    "rank" INT,
    "last_played_at" TIMESTAMP,
    "group_id" BIGINT NOT NULL REFERENCES "groups" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_group_user__user_id_cae9b7" UNIQUE ("user_id", "group_id")
) /* User stats within a specific group — for per-group leaderboard. */;
CREATE INDEX IF NOT EXISTS "idx_group_user__group_i_0fca22" ON "group_user_stats" ("group_id", "elo");
CREATE INDEX IF NOT EXISTS "idx_group_user__group_i_5e5672" ON "group_user_stats" ("group_id", "xp");
CREATE INDEX IF NOT EXISTS "idx_group_user__group_i_bb04c2" ON "group_user_stats" ("group_id", "games_won");
CREATE TABLE IF NOT EXISTS "stats_period_snapshots" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "period" VARCHAR(8) NOT NULL,
    "period_start" DATE NOT NULL,
    "period_end" DATE NOT NULL,
    "games_total" INT NOT NULL,
    "games_won" INT NOT NULL,
    "role_stats" JSON NOT NULL,
    "elo_change" INT NOT NULL,
    "xp_earned" INT NOT NULL,
    "group_id" BIGINT REFERENCES "groups" ("id") ON DELETE SET NULL,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_stats_perio_user_id_856eba" UNIQUE ("user_id", "group_id", "period", "period_start")
) /* Daily\\/weekly\\/monthly snapshot — populated by cron from GameResult. */;
CREATE INDEX IF NOT EXISTS "idx_stats_perio_group_i_516e94" ON "stats_period_snapshots" ("group_id", "period", "period_start");
CREATE TABLE IF NOT EXISTS "user_stats" (
    "games_total" INT NOT NULL,
    "games_won" INT NOT NULL,
    "games_lost" INT NOT NULL,
    "citizen_games" INT NOT NULL,
    "citizen_wins" INT NOT NULL,
    "mafia_games" INT NOT NULL,
    "mafia_wins" INT NOT NULL,
    "singleton_games" INT NOT NULL,
    "singleton_wins" INT NOT NULL,
    "role_stats" JSON NOT NULL,
    "elo" INT NOT NULL,
    "xp" INT NOT NULL,
    "level" INT NOT NULL,
    "times_survived" INT NOT NULL,
    "times_killed_at_night" INT NOT NULL,
    "times_voted_out" INT NOT NULL,
    "current_win_streak" INT NOT NULL,
    "longest_win_streak" INT NOT NULL,
    "current_loss_streak" INT NOT NULL,
    "afk_count" INT NOT NULL,
    "leave_count" INT NOT NULL,
    "average_game_duration" REAL NOT NULL,
    "last_played_at" TIMESTAMP,
    "last_reset_at" TIMESTAMP,
    "user_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "users" ("id") ON DELETE CASCADE
) /* Denormalized global aggregate per user — fast lookup for \\/stats. */;
CREATE TABLE IF NOT EXISTS "giveaways" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "chat_id" BIGINT NOT NULL,
    "message_id" BIGINT NOT NULL,
    "total_diamonds" INT NOT NULL,
    "expires_at" TIMESTAMP NOT NULL,
    "max_clicks" INT NOT NULL,
    "status" VARCHAR(9) NOT NULL /* ACTIVE: active\nFINISHED: finished\nCANCELLED: cancelled */,
    "created_at" TIMESTAMP NOT NULL,
    "group_id" BIGINT REFERENCES "groups" ("id") ON DELETE SET NULL,
    "sender_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* `\\/give 50` (group giveaway with inline button). */;
CREATE TABLE IF NOT EXISTS "giveaway_clicks" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "click_order" INT NOT NULL,
    "diamonds_received" INT NOT NULL,
    "clicked_at" TIMESTAMP NOT NULL,
    "giveaway_id" CHAR(36) NOT NULL REFERENCES "giveaways" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_giveaway_cl_giveawa_908849" UNIQUE ("giveaway_id", "user_id")
) /* Each click on a giveaway button — harmonic distribution. */;
CREATE TABLE IF NOT EXISTS "transactions" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "type" VARCHAR(18) NOT NULL /* BUY_DIAMONDS: buy_diamonds\nSPEND_DIAMONDS: spend_diamonds\nSPEND_DOLLARS: spend_dollars\nGIFT_SEND: gift_send\nGIFT_RECEIVE: gift_receive\nADMIN_GRANT: admin_grant\nGAME_BOUNTY_ESCROW: game_bounty_escrow\nGAME_BOUNTY_PAYOUT: game_bounty_payout\nGAME_BOUNTY_REFUND: game_bounty_refund\nGIVEAWAY_PAYOUT: giveaway_payout */,
    "stars_amount" INT,
    "diamonds_amount" INT,
    "dollars_amount" INT,
    "item" VARCHAR(64),
    "telegram_payment_charge_id" VARCHAR(128),
    "status" VARCHAR(9) NOT NULL /* PENDING: pending\nCOMPLETED: completed\nFAILED: failed\nREFUNDED: refunded */,
    "note" VARCHAR(256),
    "created_at" TIMESTAMP NOT NULL,
    "counterparty_id" BIGINT REFERENCES "users" ("id") ON DELETE SET NULL,
    "related_game_id" CHAR(36) REFERENCES "games" ("id") ON DELETE SET NULL,
    "related_giveaway_id" CHAR(36) REFERENCES "giveaways" ("id") ON DELETE SET NULL,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* All currency movements (Telegram Stars, diamonds, dollars). */;
CREATE INDEX IF NOT EXISTS "idx_transaction_user_id_6566ad" ON "transactions" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_transaction_type_fc7f9f" ON "transactions" ("type", "created_at");
CREATE TABLE IF NOT EXISTS "achievements" (
    "code" VARCHAR(64) NOT NULL PRIMARY KEY,
    "name_i18n" JSON NOT NULL,
    "description_i18n" JSON NOT NULL,
    "icon" VARCHAR(8) NOT NULL,
    "diamonds_reward" INT NOT NULL,
    "xp_reward" INT NOT NULL
) /* Static achievement catalog. */;
CREATE TABLE IF NOT EXISTS "admin_accounts" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "username" VARCHAR(64) NOT NULL UNIQUE,
    "password_hash" VARCHAR(256) NOT NULL,
    "telegram_id" BIGINT UNIQUE,
    "role" VARCHAR(32) NOT NULL,
    "is_active" INT NOT NULL,
    "last_login_at" TIMESTAMP,
    "created_at" TIMESTAMP NOT NULL
) /* Super admin accounts (login + password OR Telegram-linked). */;
CREATE TABLE IF NOT EXISTS "audit_logs" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "action" VARCHAR(64) NOT NULL,
    "target_type" VARCHAR(32),
    "target_id" VARCHAR(64),
    "payload" JSON NOT NULL,
    "ip_address" VARCHAR(64),
    "user_agent" VARCHAR(256),
    "created_at" TIMESTAMP NOT NULL,
    "actor_id" BIGINT REFERENCES "users" ("id") ON DELETE SET NULL,
    "actor_admin_id" CHAR(36) REFERENCES "admin_accounts" ("id") ON DELETE SET NULL
) /* Super admin actions audit trail. */;
CREATE INDEX IF NOT EXISTS "idx_audit_logs_action_358af3" ON "audit_logs" ("action", "created_at");
CREATE INDEX IF NOT EXISTS "idx_audit_logs_actor_i_6fa712" ON "audit_logs" ("actor_id", "created_at");
CREATE TABLE IF NOT EXISTS "one_time_tokens" (
    "token" VARCHAR(64) NOT NULL PRIMARY KEY,
    "expires_at" TIMESTAMP NOT NULL,
    "used" INT NOT NULL,
    "used_ip" VARCHAR(64),
    "created_at" TIMESTAMP NOT NULL,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* 1-time login token (Telegram bot → admin panel). */;
CREATE TABLE IF NOT EXISTS "user_achievements" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "unlocked_at" TIMESTAMP NOT NULL,
    "achievement_id" VARCHAR(64) NOT NULL REFERENCES "achievements" ("code") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_achiev_user_id_da78ea" UNIQUE ("user_id", "achievement_id")
) /* Which user unlocked which achievement. */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
