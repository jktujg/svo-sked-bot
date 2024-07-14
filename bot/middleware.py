from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, logger):
        self.logger = logger

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        try:
            return await handler(event, data)
        except Exception:
            self.logger.exception(msg='Uncaught exception', extra={'data': data})
