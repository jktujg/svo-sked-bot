from enum import IntEnum, auto

from aiogram.filters.callback_data import CallbackData


################ Flight ################

class FlightAction(IntEnum):
    show = auto()
    update = auto()
    toggle_favorite = auto()
    toggle_changelog = auto()


class FlightCD(CallbackData, prefix='flight', sep='^'):
    id: int
    changelog: bool
    action: FlightAction


################ SearchFlight ################

class SearchFlightAction(IntEnum):
    toggle_direction = auto()
    pick_date = auto()


class SearchFlightCD(CallbackData, prefix='search_flight', sep='^'):
    action: SearchFlightAction
