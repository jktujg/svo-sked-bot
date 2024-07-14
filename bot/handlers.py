from aiogram import Router, types, F
from aiogram.filters import Command, or_f, CommandStart
from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram_calendar import SimpleCalendarCallback

from . import (
    templates,
    filters,
    callback_data as cd,
    processors,
)

router = Router()
router.message.middleware(ChatActionMiddleware())


#####  Message  ######
@router.message(CommandStart(deep_link=True))
async def flight_deeplink(message: types.Message, command: types.BotCommand):
    await processors.FlightProcessor().process_deeplink(message=message, command=command)


@router.message(CommandStart(deep_link=False))
async def start_cmd(message: types.Message):
    await message.answer(**templates.StartCMDTemplate().as_kwargs(keyboard_kw=dict(input_field_placeholder='Поиск')))


@router.message(Command('flight'))
async def flight_message(message: types.Message, command: types.BotCommand):
    await processors.FlightProcessor().process_message(message, command)


@router.message(or_f(Command('favorite'), F.text.lower() == 'избранное'))
async def favorite_flight_message(message: types.Message):
    await processors.FavoriteFlightProcessor().process_message(message=message)


@router.message(filters.SearchFlightFilter())
async def search_flight_message(message: types.Message, search_params: dict):
    await processors.SearchFlightProcessor().process_message(message, search_params=search_params)


@router.message()
async def search_flight_not_found(message: types.Message):
    await message.answer(templates.SearchFlightTemplate.get_message_not_found())


#####  CallbackQuery  #####
@router.callback_query(cd.SearchFlightCD.filter())
async def search_flight_cb(callback: types.CallbackQuery, callback_data: cd.SearchFlightCD):
    await processors.SearchFlightProcessor().process_callback(callback, callback_data)



@router.callback_query(cd.FlightCD.filter())
async def flight_cb(callback: types.callback_query, callback_data: cd.FlightCD):
    await processors.FlightProcessor().process_callback(callback=callback, callback_data=callback_data)


@router.callback_query(SimpleCalendarCallback.filter())
async def search_flight_calendar(callback: types.CallbackQuery, callback_data: SimpleCalendarCallback):
    await processors.SearchFlightProcessor().process_calendar(callback=callback, callback_data=callback_data)


#####  InlineQuery  #####
@router.inline_query(F.query.lower() == 'favorite')
async def favorite_flight_inline(inline_query: types.InlineQuery):
    await processors.FavoriteFlightProcessor().process_inline(inline_query=inline_query)


@router.inline_query(F.query.regexp(r'id_(?P<flight_id>\d+)').groupdict().get('flight_id').as_('flight_id'))
async def flight_inline(inline_query: types.InlineQuery, flight_id: str):
    await processors.FlightProcessor().process_inline(inline_query=inline_query, flight_id=flight_id)


@router.inline_query(filters.SearchFlightFilter())
async def search_flight_inline(inline_query: types.InlineQuery, search_params: dict):
    await processors.SearchFlightProcessor().process_inline(inline_query=inline_query, search_params=search_params)

