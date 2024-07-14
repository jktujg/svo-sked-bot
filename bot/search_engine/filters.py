import re
from abc import ABCMeta, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Any

from .mappings import compare_mapping
from .patterns import Regex
from .utils import date_from_input


class SearchFilter(metaclass=ABCMeta):

    def __init__(self, to_none: bool = True):
        self.to_none = to_none

    @abstractmethod
    def result_factory(self) -> dict:
        ...

    @abstractmethod
    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        ...

    def update_result(self, result_dict: dict, match_dict: dict) -> None:
        result_dict.update(match_dict)

    def pre_search(self, result: dict):
        pass

    def post_search(self, result: dict):
        pass

    def __call__(self, s: list[str, None]) -> dict[str, Any]:
        result = self.result_factory()
        self.pre_search(result)

        for index, string in enumerate(s):
            if string is None:
                continue

            _match = self.match(string)
            if _match is None:
                continue

            self.update_result(result, _match)
            if self.to_none is True:
                s[index] = None
            break

        self.post_search(result)

        return result


class DateFilter(SearchFilter):
    def result_factory(self) -> dict:
        return dict(date=None)

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        match = Regex.date.search(string)
        if match is None:
            return
        return match.groupdict()

    def update_result(self, result_dict: dict, match_dict: dict) -> None:
        result_dict['date'] = date_from_input(**match_dict)


class CompanyFlightFilter(SearchFilter):
    def result_factory(self) -> dict:
        return dict(
            number=None,
            company_iata=None,
        )

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        match = Regex.company_flight.search(string)
        if match is None:
            return
        return {key: val.upper() for key, val in match.groupdict().items()}


class FlightNumberFilter(SearchFilter):
    def result_factory(self) -> dict:
        return dict(number=None)

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        match = Regex.flight.search(string)
        if match is None:
            return
        return match.groupdict()


class DirectionFilter(SearchFilter):
    direction_map = {
        'прилет': 'arrival',
        'прилёт': 'arrival',
        'вылет': 'departure',
    }

    def result_factory(self) -> dict:
        return dict(direction=None)

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        match = self.direction_map.get(string.lower())
        if match is None:
            return
        return dict(direction=match)


class DateWordFilter(SearchFilter):
    delta_map = {
        'вчера': timedelta(days=-1),
        'сегодня': timedelta(days=0),
        'завтра': timedelta(days=1),
    }

    def result_factory(self) -> dict:
        return dict(
            date=None,
            date_word=None,
        )

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        match = Regex.date_word.search(string.lower())
        if match is None:
            return

        date_word = match.groupdict().get('date_word')
        delta = self.delta_map.get(date_word)
        if delta is None:
            return

        date = datetime.now(tz=timezone(timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0)
        date += delta
        return dict(
            date=date,
            date_word=date_word,
        )


class CompanyIataFilter(SearchFilter):
    def result_factory(self) -> dict:
        return dict(
            company_iata=None,
        )

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        match = Regex.company_iata.search(string)
        if match is None:
            return

        return dict(
            company_iata=match.groupdict()['company_iata'].upper(),
        )


class AirportIataFilter(SearchFilter):
    def result_factory(self) -> dict:
        return dict(
            airport_iata=None,
        )

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        match = Regex.airport_iata.search(string)
        if match is None:
            return

        return dict(
            airport_iata=match.groupdict().get('airport_iata').upper(),
        )


class CountryNameFilter(SearchFilter):
    def result_factory(self) -> dict:
        return dict(
            country_name=None,
            country_airport_iata=None
        )

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        if len(string) < 3:
            return
        for country_name, airport_iatas in compare_mapping.ct_mapping.items():
            if string in country_name.lower():
                return dict(
                    country_name=country_name,
                    country_airport_iata=airport_iatas
                )
        return None


class CompanyNameFilter(SearchFilter):
    def result_factory(self) -> dict:
        return dict(
            company_iata=None,
        )

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        if len(string) < 3:
            return
        for company_iata, company_names in compare_mapping.co_mapping.items():
            if any(True if string in name.lower() else False for name in company_names):
                return dict(
                    company_iata=company_iata,
                )

        return None


class AirportNameFilter(SearchFilter):
    def result_factory(self) -> dict:
        return dict(
            airport_iata=None,
        )

    def match(self, string: str | None, *args, **kwargs) -> dict | None:
        if len(string) < 2:
            return
        airport_iata = None
        for ap_iata, ap_cities in compare_mapping.ap_mapping.items():
            for city_name in ap_cities:
                city_name = city_name.lower()
                if string == city_name:
                    return dict(
                        airport_iata=ap_iata,
                    )
                elif string in city_name and airport_iata is None:
                    airport_iata = ap_iata

        if airport_iata is not None:
            return dict(
                airport_iata=airport_iata,
            )

        return None
