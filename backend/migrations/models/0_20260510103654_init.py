from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(64),
    "first_name" VARCHAR(128) NOT NULL,
    "last_name" VARCHAR(128),
    "language_code" VARCHAR(8) NOT NULL,
    "diamonds" INT NOT NULL,
    "dollars" INT NOT NULL,
    "xp" INT NOT NULL,
    "level" INT NOT NULL,
    "is_premium" BOOL NOT NULL,
    "premium_expires_at" TIMESTAMPTZ,
    "is_banned" BOOL NOT NULL,
    "banned_until" TIMESTAMPTZ,
    "ban_reason" VARCHAR(256),
    "afk_warnings" INT NOT NULL,
    "active_game_id" UUID,
    "joined_at" TIMESTAMPTZ NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS "user_inventories" (
    "shield" INT NOT NULL,
    "killer_shield" INT NOT NULL,
    "vote_shield" INT NOT NULL,
    "rifle" INT NOT NULL,
    "mask" INT NOT NULL,
    "fake_document" INT NOT NULL,
    "special_role" INT NOT NULL,
    "settings" JSONB NOT NULL,
    "user_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "groups" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(256) NOT NULL,
    "is_active" BOOL NOT NULL,
    "is_blocked" BOOL NOT NULL,
    "onboarding_completed" BOOL NOT NULL,
    "bot_admin_perms" JSONB NOT NULL,
    "invite_link" VARCHAR(256),
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS "group_settings" (
    "language" VARCHAR(8) NOT NULL,
    "roles" JSONB NOT NULL,
    "timings" JSONB NOT NULL,
    "silence" JSONB NOT NULL,
    "items_allowed" JSONB NOT NULL,
    "role_distribution" JSONB NOT NULL,
    "afk" JSONB NOT NULL,
    "permissions" JSONB NOT NULL,
    "gameplay" JSONB NOT NULL,
    "display" JSONB NOT NULL,
    "messages" JSONB NOT NULL,
    "group_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "groups" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "games" (
    "id" UUID NOT NULL PRIMARY KEY,
    "status" VARCHAR(9) NOT NULL,
    "started_at" TIMESTAMPTZ NOT NULL,
    "finished_at" TIMESTAMPTZ,
    "winner_team" VARCHAR(9),
    "bounty_per_winner" INT,
    "bounty_pool" INT,
    "settings_snapshot" JSONB NOT NULL,
    "history" JSONB NOT NULL,
    "bounty_initiator_id" BIGINT REFERENCES "users" ("id") ON DELETE SET NULL,
    "group_id" BIGINT NOT NULL REFERENCES "groups" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_games_group_i_24f813" ON "games" ("group_id", "started_at");
CREATE TABLE IF NOT EXISTS "game_results" (
    "id" UUID NOT NULL PRIMARY KEY,
    "role" VARCHAR(32) NOT NULL,
    "team" VARCHAR(16) NOT NULL,
    "won" BOOL NOT NULL,
    "survived" BOOL NOT NULL,
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
    "played_at" TIMESTAMPTZ NOT NULL,
    "game_id" UUID NOT NULL REFERENCES "games" ("id") ON DELETE CASCADE,
    "group_id" BIGINT REFERENCES "groups" ("id") ON DELETE SET NULL,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_game_result_user_id_c337d6" ON "game_results" ("user_id", "played_at");
CREATE INDEX IF NOT EXISTS "idx_game_result_user_id_8a3d88" ON "game_results" ("user_id", "role");
CREATE INDEX IF NOT EXISTS "idx_game_result_group_i_d91de8" ON "game_results" ("group_id", "played_at");
CREATE INDEX IF NOT EXISTS "idx_game_result_user_id_acb0f1" ON "game_results" ("user_id", "group_id", "played_at");
CREATE TABLE IF NOT EXISTS "group_stats" (
    "total_games" INT NOT NULL,
    "total_unique_players" INT NOT NULL,
    "active_players_30d" INT NOT NULL,
    "avg_game_duration_seconds" DOUBLE PRECISION NOT NULL,
    "avg_player_count" DOUBLE PRECISION NOT NULL,
    "citizens_winrate" DOUBLE PRECISION NOT NULL,
    "mafia_winrate" DOUBLE PRECISION NOT NULL,
    "singleton_winrate" DOUBLE PRECISION NOT NULL,
    "most_played_role" VARCHAR(32),
    "last_game_at" TIMESTAMPTZ,
    "group_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "groups" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "group_user_stats" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "games_total" INT NOT NULL,
    "games_won" INT NOT NULL,
    "role_stats" JSONB NOT NULL,
    "elo" INT NOT NULL,
    "xp" INT NOT NULL,
    "rank" INT,
    "last_played_at" TIMESTAMPTZ,
    "group_id" BIGINT NOT NULL REFERENCES "groups" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_group_user__user_id_cae9b7" UNIQUE ("user_id", "group_id")
);
CREATE INDEX IF NOT EXISTS "idx_group_user__group_i_0fca22" ON "group_user_stats" ("group_id", "elo");
CREATE INDEX IF NOT EXISTS "idx_group_user__group_i_5e5672" ON "group_user_stats" ("group_id", "xp");
CREATE INDEX IF NOT EXISTS "idx_group_user__group_i_bb04c2" ON "group_user_stats" ("group_id", "games_won");
CREATE TABLE IF NOT EXISTS "stats_period_snapshots" (
    "id" UUID NOT NULL PRIMARY KEY,
    "period" VARCHAR(8) NOT NULL,
    "period_start" DATE NOT NULL,
    "period_end" DATE NOT NULL,
    "games_total" INT NOT NULL,
    "games_won" INT NOT NULL,
    "role_stats" JSONB NOT NULL,
    "elo_change" INT NOT NULL,
    "xp_earned" INT NOT NULL,
    "group_id" BIGINT REFERENCES "groups" ("id") ON DELETE SET NULL,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_stats_perio_user_id_856eba" UNIQUE ("user_id", "group_id", "period", "period_start")
);
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
    "role_stats" JSONB NOT NULL,
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
    "average_game_duration" DOUBLE PRECISION NOT NULL,
    "last_played_at" TIMESTAMPTZ,
    "last_reset_at" TIMESTAMPTZ,
    "user_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "giveaways" (
    "id" UUID NOT NULL PRIMARY KEY,
    "chat_id" BIGINT NOT NULL,
    "message_id" BIGINT NOT NULL,
    "total_diamonds" INT NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "max_clicks" INT NOT NULL,
    "status" VARCHAR(9) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "group_id" BIGINT REFERENCES "groups" ("id") ON DELETE SET NULL,
    "sender_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "giveaway_clicks" (
    "id" UUID NOT NULL PRIMARY KEY,
    "click_order" INT NOT NULL,
    "diamonds_received" INT NOT NULL,
    "clicked_at" TIMESTAMPTZ NOT NULL,
    "giveaway_id" UUID NOT NULL REFERENCES "giveaways" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_giveaway_cl_giveawa_908849" UNIQUE ("giveaway_id", "user_id")
);
CREATE TABLE IF NOT EXISTS "transactions" (
    "id" UUID NOT NULL PRIMARY KEY,
    "type" VARCHAR(18) NOT NULL,
    "stars_amount" INT,
    "diamonds_amount" INT,
    "dollars_amount" INT,
    "item" VARCHAR(64),
    "telegram_payment_charge_id" VARCHAR(128),
    "status" VARCHAR(9) NOT NULL,
    "note" VARCHAR(256),
    "created_at" TIMESTAMPTZ NOT NULL,
    "counterparty_id" BIGINT REFERENCES "users" ("id") ON DELETE SET NULL,
    "related_game_id" UUID REFERENCES "games" ("id") ON DELETE SET NULL,
    "related_giveaway_id" UUID REFERENCES "giveaways" ("id") ON DELETE SET NULL,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_transaction_user_id_6566ad" ON "transactions" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_transaction_type_fc7f9f" ON "transactions" ("type", "created_at");
CREATE TABLE IF NOT EXISTS "achievements" (
    "code" VARCHAR(64) NOT NULL PRIMARY KEY,
    "name_i18n" JSONB NOT NULL,
    "description_i18n" JSONB NOT NULL,
    "icon" VARCHAR(8) NOT NULL,
    "diamonds_reward" INT NOT NULL,
    "xp_reward" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "admin_accounts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "username" VARCHAR(64) NOT NULL UNIQUE,
    "password_hash" VARCHAR(256) NOT NULL,
    "telegram_id" BIGINT UNIQUE,
    "role" VARCHAR(32) NOT NULL,
    "is_active" BOOL NOT NULL,
    "last_login_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS "audit_logs" (
    "id" UUID NOT NULL PRIMARY KEY,
    "action" VARCHAR(64) NOT NULL,
    "target_type" VARCHAR(32),
    "target_id" VARCHAR(64),
    "payload" JSONB NOT NULL,
    "ip_address" VARCHAR(64),
    "user_agent" VARCHAR(256),
    "created_at" TIMESTAMPTZ NOT NULL,
    "actor_id" BIGINT REFERENCES "users" ("id") ON DELETE SET NULL,
    "actor_admin_id" UUID REFERENCES "admin_accounts" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_audit_logs_action_358af3" ON "audit_logs" ("action", "created_at");
CREATE INDEX IF NOT EXISTS "idx_audit_logs_actor_i_6fa712" ON "audit_logs" ("actor_id", "created_at");
CREATE TABLE IF NOT EXISTS "one_time_tokens" (
    "token" VARCHAR(64) NOT NULL PRIMARY KEY,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "used" BOOL NOT NULL,
    "used_ip" VARCHAR(64),
    "created_at" TIMESTAMPTZ NOT NULL,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "user_achievements" (
    "id" UUID NOT NULL PRIMARY KEY,
    "unlocked_at" TIMESTAMPTZ NOT NULL,
    "achievement_id" VARCHAR(64) NOT NULL REFERENCES "achievements" ("code") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_achiev_user_id_da78ea" UNIQUE ("user_id", "achievement_id")
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
