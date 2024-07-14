from typing import Callable, Any

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from ..settings import settings


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        url=settings.WEBHOOK_URL,
        secret_token=settings.WEBHOOK_SECRET.get_secret_value() if settings.WEBHOOK_SECRET else None,
        drop_pending_updates=True,
    )


def webhook(bot: Bot, dispatcher: Dispatcher, bot_setup: Callable[[Bot], Any]) -> None:
    dispatcher.startup.register(bot_setup)
    dispatcher.startup.register(on_startup)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET.get_secret_value() if settings.WEBHOOK_SECRET else None,
    )
    webhook_requests_handler.register(app, path=settings.WEBHOOK_ENDPOINT)
    setup_application(app, dispatcher, bot=bot)

    web.run_app(app, host=settings.WEB_SERVER_HOST, port=settings.WEB_SERVER_PORT)
