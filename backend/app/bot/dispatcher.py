"""Bot dispatcher setup — register routers and middlewares."""

from aiogram import Dispatcher
from loguru import logger


def setup_routers(dp: Dispatcher) -> None:
    """Register all bot routers."""
    from app.bot.handlers.common import help as common_help
    from app.bot.handlers.group import atmosphere as group_atmosphere
    from app.bot.handlers.group import game as group_game
    from app.bot.handlers.group import giveaway as group_giveaway
    from app.bot.handlers.group import onboarding as group_onboarding
    from app.bot.handlers.group import settings as group_settings
    from app.bot.handlers.group import stats as group_stats
    from app.bot.handlers.group import voting as group_voting
    from app.bot.handlers.private import group_settings as private_group_settings
    from app.bot.handlers.private import inventory as private_inventory
    from app.bot.handlers.private import last_words as private_last_words
    from app.bot.handlers.private import mafia_chat as private_mafia_chat
    from app.bot.handlers.private import menu as private_menu
    from app.bot.handlers.private import payment as private_payment
    from app.bot.handlers.private import role_actions as private_role_actions
    from app.bot.handlers.private import special_actions as private_special
    from app.bot.handlers.private import start as private_start
    from app.bot.handlers.private import super_admin as private_super_admin

    # Middlewares
    from app.bot.middlewares.command_cleanup import CommandCleanupMiddleware
    from app.bot.middlewares.i18n import I18nMiddleware
    from app.bot.middlewares.user_loader import UserLoaderMiddleware

    dp.update.outer_middleware(UserLoaderMiddleware())
    dp.update.outer_middleware(I18nMiddleware())
    # Inner: runs around individual message handlers, so it can delete
    # the /command message AFTER the handler completes.
    dp.message.middleware(CommandCleanupMiddleware())

    # Routers (order matters: more specific first)
    dp.include_router(private_super_admin.router)  # before other private handlers
    dp.include_router(private_group_settings.router)  # settings:* callbacks
    dp.include_router(private_menu.router)  # main menu callbacks (menu:*)
    dp.include_router(common_help.router)
    dp.include_router(group_onboarding.router)
    dp.include_router(group_stats.router)
    dp.include_router(group_giveaway.router)
    dp.include_router(group_voting.router)
    dp.include_router(group_atmosphere.router)
    dp.include_router(group_settings.router)  # /settings group command
    dp.include_router(group_game.router)
    dp.include_router(private_inventory.router)
    dp.include_router(private_payment.router)
    dp.include_router(private_special.router)
    dp.include_router(private_role_actions.router)
    dp.include_router(private_start.router)
    dp.include_router(private_mafia_chat.router)  # before last_words
    dp.include_router(private_last_words.router)  # catch-all text

    logger.info("Bot routers registered")
