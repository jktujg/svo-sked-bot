from abc import ABCMeta, abstractmethod
from asyncio import to_thread
from enum import StrEnum
from functools import cached_property
from typing import Sequence, Any
from urllib.parse import urljoin

from requests import Session

from . import schemas, quieries


class URL(StrEnum):
    BASE_URL = 'https://svolog.ru/api/v1/'
    FLIGHTS_URL = urljoin(BASE_URL, 'flights/')


class SvologEndpoint(metaclass=ABCMeta):
    @abstractmethod
    def get_one_by_id(self, id: Any) -> schemas.BaseSchema:
        ...

    @abstractmethod
    def get_many(self, query: quieries.BaseQuery) -> schemas.PagedResponse:
        ...

    @abstractmethod
    def get_many_by_id(self, ids: list[Any]) -> list[schemas.BaseSchema]:
        ...


class FlightEndpoint:
    @cached_property
    def session(self):
        return Session()

    async def get_one_by_id(self, id: str, **kw) -> schemas.FlightSchema:
        response = await to_thread(
            self.session.get,
            urljoin(URL.FLIGHTS_URL, str(id))
        )
        response.raise_for_status()

        flight = await to_thread(response.json)
        flight = schemas.FlightSchema.model_validate(flight)
        return flight

    async def get_many(self, query: quieries.FlightsQuery, **kw) -> schemas.PagedFlightResponse:
        response = await to_thread(
            self.session.get,
            URL.FLIGHTS_URL,
            params=query.model_dump(exclude_none=True)
        )
        response.raise_for_status()

        data = await to_thread(response.json)
        data = schemas.PagedFlightResponse.model_validate(data)
        return data

    async def get_many_by_id(self, ids: Sequence) -> list[schemas.FlightSchema]:
        response = await to_thread(
            self.session.post,
            URL.FLIGHTS_URL,
            json=list(ids),
        )
        response.raise_for_status()

        data = await to_thread(response.json)
        data = [schemas.FlightSchema.model_validate(flight) for flight in data]
        return data
