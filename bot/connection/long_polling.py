import asyncio
from typing import Callable, Any

from aiogram import Dispatcher, Bot


def long_polling(bot: Bot, dispatcher: Dispatcher, bot_setup: Callable[[Bot], Any]) -> None:
    async def _long_polling() -> None:
        await bot_setup(bot)
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)

    asyncio.run(_long_polling())
