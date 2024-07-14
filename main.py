from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot import handlers
from bot.connection import long_polling, webhook
from bot.logger import logger
from bot.middleware import LoggingMiddleware
from bot.settings import settings


async def bot_setup(bot: Bot) -> None:
    commands = [
        types.BotCommand(command='/start', description='Основное меню'),
        types.BotCommand(command='/favorite', description='Избранное'),
    ]
    await bot.set_my_commands(commands)


def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()
    dp.update.middleware(LoggingMiddleware(logger=logger))
    dp.include_routers(
        handlers.router,
    )
    if settings.UPDATE_METHOD == 'long-polling':
        long_polling(bot=bot, dispatcher=dp, bot_setup=bot_setup)
    elif settings.UPDATE_METHOD == 'webhook':
        webhook(bot=bot, dispatcher=dp, bot_setup=bot_setup)


if __name__ == '__main__':
    main()
