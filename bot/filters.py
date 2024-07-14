from datetime import datetime, timezone, timedelta

from aiogram import types
from aiogram.filters import BaseFilter

from .search_engine import co_number_search, param_search


class SearchFlightFilter(BaseFilter):
    def _prepare_search_result(self, search_result: dict) -> None:
        search_result['company'] = search_result.pop('company_iata', None)
        search_result['destination'] = search_result.pop('airport_iata', None) or ','.join(search_result.pop('country_airport_iata', None) or []) or None

        search_result['date_start'] = (search_result.pop('date', None) or datetime.now(tz=timezone(timedelta(hours=3)))
                                       .replace(hour=0, minute=0, second=0, microsecond=0))
        search_result['date_end'] = ((search_result['date_start'] + timedelta(days=1))
                                     .replace(hour=0, minute=0, second=0, microsecond=0))
        if search_result.get('number') is not None:
            search_result['number'] = f'{search_result["number"]:0>3}'

    def _search(self, text: str) -> dict:
        search_result = co_number_search(text)
        if search_result.get('number') is None:
            search_result = param_search(text)

        return search_result

    async def __call__(self, update: types.Message | types.InlineQuery) -> dict | None:
        text = update.text if isinstance(update, types.Message) else update.query
        search_result = self._search(text)
        if not any(search_result.values()):
            return

        self._prepare_search_result(search_result)
        return dict(search_params=search_result)
