from abc import abstractmethod, ABCMeta
from functools import cached_property
from typing import Literal

from . import filters
from . import mappings


class BaseSearch(metaclass=ABCMeta):
    @property
    @abstractmethod
    def filters(self) -> list:
        ...

    def prepare_input(self, _s: str, /) -> list:
        return _s.lower().split()

    def __call__(self, _s: str, /) -> dict:
        result = {}
        s = self.prepare_input(_s)

        for f in self.filters:
            found_params = f(s)
            for param, value in found_params.items():
                if value is not None:
                    result.setdefault(param, value)

        return result


class FlightNumberSearch(BaseSearch):
    @cached_property
    def filters(self) -> list:
        return [
            filters.DateFilter(to_none=False),
            filters.DateWordFilter(to_none=False),
            filters.CompanyFlightFilter(to_none=False),
            filters.CompanyIataFilter(to_none=False),
            filters.FlightNumberFilter(to_none=False)
        ]

    def prepare_input(self, _s: str, /) -> list:
        return [_s.lower()]


class ParamsSearch(BaseSearch):
    @cached_property
    def filters(self) -> list:
        return [
            filters.DirectionFilter(to_none=True),
            filters.DateFilter(to_none=True),
            filters.DateWordFilter(to_none=True),
            filters.AirportIataFilter(to_none=True),
            filters.CompanyIataFilter(to_none=True),
            filters.CountryNameFilter(to_none=True),
            filters.AirportNameFilter(to_none=True),
            filters.CompanyNameFilter(to_none=True),
        ]


def get_airport_city(iata: str, lang: Literal['ru', 'en'] = 'ru') -> str | None:
    if not isinstance(iata, str):
        return
    index = {'ru': 0, 'en': 1}.get(lang)
    if index is None:
        return

    names = mappings.compare_mapping.ap_mapping.get(iata.upper())
    if not names:
        return

    return names[index]


def get_company_name(iata: str) -> str | None:
    if not isinstance(iata, str):
        return
    return mappings.compare_mapping.co_mapping.get(iata.upper(), [None])[0]
