import binascii
import re
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from aiogram import types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.payload import decode_payload
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from . import (
    callback_data as cd,
    templates,
    constants,
)
from .services import services


class Processor(metaclass=ABCMeta):
    @abstractmethod
    def init_template(self, *a, **kw) -> templates.BaseTemplate:
        ...

    @abstractmethod
    async def get_query(self, *a, **kw) -> dict:
        ...

    @abstractmethod
    async def get_response(self, *a, **kw) -> Any:
        ...

    @abstractmethod
    async def process_message(self, *a, **kw) -> None:
        ...

    async def process_callback(self, callback: types.CallbackQuery, callback_data: cd.CallbackData, *a, **kw) -> None:
        method = getattr(self, callback_data.action.name + '_cb')
        await method(callback=callback, callback_data=callback_data)


class SearchFlightProcessor(Processor):
    def init_template(self, response: Any, query: dict, *a, **kw) -> templates.SearchFlightTemplate:
        return templates.SearchFlightTemplate(response, query)

    async def get_query(self, message_id: int, *a, **kw) -> dict | None:
        return await services.FlightQueryService.get_query(message_id)

    async def get_response(self, query: dict, *a, **kw) -> Any:
        response = await services.FlightQueryService.get_many(**query)
        return response

    async def process_message(self, message, search_params: dict, *a, **kw) -> None:
        if search_params.get('number') is None:
            search_params.setdefault('direction', 'departure')
        response = await self.get_response(query=search_params)
        template = self.init_template(response=response, query=search_params)

        sent_message = await message.answer(**template.as_kwargs())
        await services.FlightQueryService.store_query(query_dict=search_params, message_id=sent_message.message_id)

    async def process_inline(self, inline_query: types.InlineQuery, search_params: dict, *a, **kw):
        offset = int(inline_query.offset or 0)
        search_params['page'] = offset
        search_params['limit'] = 50
        response = await self.get_response(search_params)
        if response.count == 0:
            return []

        results = []

        if response.items:
            paged_favorites = await services.FlightFavoriteService.get_paged_ids(
                user_id=inline_query.from_user.id,
                page=0,
                per_page=1000
            )
            favorites = set(map(int, paged_favorites['items']))
        else:
            favorites = set()

        for flight in response.items:
            template = FlightProcessor().init_template(
                flight=flight,
                is_favorite=flight.id in favorites,
                changelog=False
            )

            if inline_query.chat_type == 'sender':
                message = f'/flight {flight.id}'
                reply_markup = None
            else:
                message = template.get_inline_query_message()
                reply_markup = template.get_inline_query_keyboard()

            results.append(InlineQueryResultArticle(
                id=str(flight.id),
                title=template.get_inline_query_title(),
                description=template.get_inline_query_description(),
                input_message_content=InputTextMessageContent(message_text=message),
                reply_markup=reply_markup,
                thumbnail_url=constants.INLINE_PLANE_IMAGE[flight.direction],
            ))

        await inline_query.answer(results, is_personal=True, cache_time=0, next_offset=str(offset + 1))

    async def toggle_direction_cb(self, callback: types.CallbackQuery, callback_data: cd.SearchFlightCD):
        query = await self.get_query(message_id=callback.message.message_id)
        query['direction'] = constants.COUNTER_DIRECTION[query['direction']].value

        template = self.init_template(
            response=await self.get_response(query),
            query=query
        )

        sent_message = await callback.message.edit_text(**template.as_kwargs())
        await services.FlightQueryService.store_query(query_dict=query, message_id=sent_message.message_id)
        await callback.answer()

    async def pick_date_cb(self, callback: types.CallbackQuery, callback_data: cd.SearchFlightCD):
        query = await self.get_query(message_id=callback.message.message_id)
        if query.get('number') is None:
            query.setdefault('direction', 'departure')

        calendar = SimpleCalendar()
        today = datetime.now(tz=constants.SVO_TIMEZONE)
        await callback.message.edit_reply_markup(
            reply_markup=await calendar.start_calendar(year=today.year, month=today.month))

        await callback.answer()

    async def process_calendar(self, callback: types.CallbackQuery, callback_data: SimpleCalendarCallback):
        calendar = SimpleCalendar()
        selected, date = await calendar.process_selection(callback, callback_data)

        if selected:
            query = await self.get_query(message_id=callback.message.message_id)
            if date is not None:
                query['date_start'] = date.astimezone(constants.SVO_TIMEZONE)
                query['date_end'] = query['date_start'] + timedelta(days=1)

            template = self.init_template(
                response=await self.get_response(query),
                query=query,
            )

            sent_message = await callback.message.edit_text(**template.as_kwargs())
            await services.FlightQueryService.store_query(query_dict=query, message_id=sent_message.message_id)
            await callback.answer()


class FavoriteFlightProcessor(Processor):
    def init_template(self, response: Any, query: dict, *a, **kw) -> templates.BaseTemplate:
        return templates.FavoriteFlightTemplate(response=response, query=query)

    async def get_query(self, user_id: int, page: int, per_page: int, *a, **kw) -> dict:
        return dict(user_id=user_id, page=page, per_page=per_page)

    async def get_response(self, query, *a, **kw) -> Any:
        return await services.FlightFavoriteService.get_many(**query, sort_by='sked_local')

    async def process_message(self, message: types.Message, *a, **kw) -> None:
        query = await self.get_query(user_id=message.from_user.id, page=0, per_page=0)  # skip fetch favorite flights as far as only `total` paremter is needed
        template = self.init_template(
            response=await self.get_response(query),
            query=query
        )

        await message.answer(**template.as_kwargs())

    async def process_inline(self, inline_query: types.InlineQuery, *a, **kw):
        offset = int(inline_query.offset or 0)
        query = await self.get_query(user_id=inline_query.from_user.id, page=offset, per_page=50)
        response = await self.get_response(query)

        if response.count == 0:
            return []

        results = []
        for flight in response.items:
            template = FlightProcessor().init_template(flight=flight, is_favorite=True, changelog=False)

            if inline_query.chat_type == 'sender':
                message = f'/flight {flight.id}'
                reply_markup = None
            else:
                message = template.get_inline_query_message()
                reply_markup = template.get_inline_query_keyboard()

            results.append(InlineQueryResultArticle(
                id=str(flight.id),
                title=template.get_inline_query_title(),
                description=template.get_inline_query_description(),
                input_message_content=InputTextMessageContent(message_text=message),
                reply_markup=reply_markup,
                thumbnail_url=constants.INLINE_PLANE_IMAGE[flight.direction],
            ))

        await inline_query.answer(results, is_personal=True, cache_time=0, next_offset=str(offset + 1))


class FlightProcessor(Processor):
    def init_template(self, flight, is_favorite: bool, changelog: bool, *a, **kw) -> templates.BaseTemplate:
        template = dict(
            arrival=templates.FlightArrivalTemplate,
            departure=templates.FlightDepartureTemplate
        )[flight.direction]

        return template(flight, is_favorite=is_favorite, changelog=changelog)

    async def get_query(self, flight_id: int, *a, **kw) -> dict:
        return dict(id=flight_id)

    async def get_response(self, query, *a, **kw) -> Any:
        flight = await services.FlightQueryService.get_one_by_id(**query)
        return flight

    async def is_favorite(self, user_id: int, flight_id: int) -> bool:
        return await services.FlightFavoriteService.is_favorite(user_id=user_id, favorite_id=flight_id)

    async def process_message(self, message: types.Message, command: types.BotCommand, *a, **kw) -> None:
        flight_id = command.args
        query = await self.get_query(flight_id=flight_id)

        flight = await self.get_response(query)
        if flight is None:
            await message.answer(text='Рейс не найден')
            return

        template = self.init_template(
            flight,
            is_favorite=await self.is_favorite(user_id=message.from_user.id, flight_id=flight_id),
            changelog=False
        )

        await message.answer(**template.as_kwargs())

    async def process_deeplink(self, message: types.Message, command: types.BotCommand, *a, **kw) -> None:
        try:
            args = decode_payload(command.args)
            match = re.match(r'flight-(?P<flight>\d+)?', args)
            flight_id = match.groupdict().get('flight')
        except (binascii.Error, AttributeError):
            await message.answer('Неверная ссылка')
            return

        query = await self.get_query(flight_id=flight_id)
        flight = await self.get_response(query)
        if flight is None:
            await message.answer('Рейс не найден')
            return

        is_favorite = await self.is_favorite(user_id=message.from_user.id, flight_id=int(flight_id))
        template = self.init_template(flight=flight, is_favorite=is_favorite, changelog=False)
        await message.answer(**template.as_kwargs())

    async def process_inline(self, inline_query: types.InlineQuery, flight_id: str, *a, **kw):
        query = await self.get_query(flight_id=int(flight_id))
        flight = await self.get_response(query)
        if flight is None:
            return

        is_favorite = await self.is_favorite(user_id=inline_query.from_user.id, flight_id=int(flight_id))
        template = self.init_template(flight, is_favorite=is_favorite, changelog=False)

        if inline_query.chat_type == 'sender':
            message = f'/flight {flight.id}'
            reply_markup = None
        else:
            message = template.get_inline_query_message()
            reply_markup = template.get_inline_query_keyboard()

        results = [InlineQueryResultArticle(
            id=flight_id,
            title=template.get_inline_query_title(),
            description=template.get_inline_query_description(),
            input_message_content=InputTextMessageContent(message_text=message),
            reply_markup=reply_markup,
            thumbnail_url=constants.INLINE_PLANE_IMAGE[flight.direction],
        )]

        await inline_query.answer(results, is_personal=True, cache_time=0)

    async def show_cb(self, callback: types.CallbackQuery, callback_data: cd.FlightCD) -> None:
        query = await self.get_query(flight_id=callback_data.id)
        template = self.init_template(
            flight=await self.get_response(query),
            is_favorite=await self.is_favorite(user_id=callback.from_user.id, flight_id=callback_data.id),
            changelog=callback_data.changelog
        )

        await callback.message.answer(**template.as_kwargs())
        await callback.answer()

    async def update_cb(self, callback: types.CallbackQuery, callback_data: cd.FlightCD) -> None:
        query = await self.get_query(flight_id=callback_data.id)
        template = self.init_template(
            flight=await self.get_response(query),
            is_favorite=await self.is_favorite(user_id=callback.from_user.id, flight_id=callback_data.id),
            changelog=callback_data.changelog
        )

        if not template.has_same_text(callback.message.text):
            await callback.message.edit_text(**template.as_kwargs())
        elif not template.has_same_markup(callback.message.reply_markup):
            await callback.message.edit_reply_markup(reply_markup=template.get_keyboard())
        await callback.answer('Обновлено')

    async def toggle_favorite_cb(self, callback: types.CallbackQuery, callback_data: cd.FlightCD) -> None:
        query = await self.get_query(flight_id=callback_data.id)
        flight = await self.get_response(query)

        is_favorite = await self.is_favorite(user_id=callback.from_user.id, flight_id=callback_data.id)
        if is_favorite is False:
            await services.FlightFavoriteService.add_one(user_id=callback.from_user.id, favorite_id=callback_data.id,
                                                         sked_local=flight.sked_local.timestamp())  # sked_local use as sort field
            answer = 'Добавлено в избранное'
            is_favorite = True
        else:
            await services.FlightFavoriteService.remove_one(user_id=callback.from_user.id, favorite_id=callback_data.id)
            answer = 'Удалено из избранного'
            is_favorite = False

        template = self.init_template(flight, is_favorite=is_favorite, changelog=callback_data.changelog)

        if not template.has_same_text(callback.message.text):
            await callback.message.edit_text(**template.as_kwargs())
        elif not template.has_same_markup(callback.message.reply_markup):
            await callback.message.edit_reply_markup(reply_markup=template.get_keyboard())

        await callback.answer(answer)

    async def toggle_changelog_cb(self, callback: types.CallbackQuery, callback_data: cd.FlightCD) -> None:
        query = await self.get_query(flight_id=callback_data.id)
        template = self.init_template(
            flight=await self.get_response(query),
            is_favorite=await self.is_favorite(user_id=callback.from_user.id, flight_id=callback_data.id),
            changelog=callback_data.changelog
        )

        await callback.message.edit_text(**template.as_kwargs())
        await callback.answer()
