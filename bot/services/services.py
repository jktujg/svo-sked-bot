import math
from datetime import datetime, timezone
from itertools import islice
from typing import Any, Type

from bot.api import (
    SvologEndpoint,
    FlightEndpoint,
    schemas as api_schemas,
)
from . import quieries
from ..api.quieries import BaseQuery
from ..database import storage


class QueryService:
    storage: storage.SearchQueryStorage
    api: SvologEndpoint
    query_schema: Type[BaseQuery]
    save_query_schema: Type[BaseQuery]
    paged_response: Type[api_schemas.PagedResponse] = api_schemas.PagedResponse

    @classmethod
    async def get_one_by_id(cls, id: Any) -> api_schemas.FlightSchema | None:
        try:
            item = await cls.api.get_one_by_id(id=id)
        except Exception:
            # todo log `not found flight`
            item = None

        return item

    @classmethod
    async def get_many(cls, **params) -> paged_response:
        query = cls.query_schema(**params)
        response = await cls.api.get_many(query=query)
        return response

    @classmethod
    async def store_query(cls, query_dict: dict, message_id: int) -> None:
        query = cls.save_query_schema.model_validate(query_dict)
        await cls.storage.upsert_one(
            message_id=message_id,
            update=query.model_dump(by_alias=True),
        )

    @classmethod
    async def get_query(cls, message_id: int) -> dict | None:
        query_dict = await cls.storage.get_one(message_id=message_id)
        if query_dict is None:
            return
        query = quieries.SaveFlightServiceQuery(**query_dict)
        return query.model_dump()


class FlightQueryService(QueryService):
    api = FlightEndpoint()
    storage = storage.SearchQueryStorage(query_type='flight')
    query_schema = quieries.FlightServiceQuery
    save_query_schema = quieries.SaveFlightServiceQuery
    paged_response = api_schemas.PagedFlightResponse


class FavoriteService:
    api: SvologEndpoint
    storage: storage.FavoriteStorage
    paged_response: api_schemas.PagedResponse = api_schemas.PagedResponse

    @classmethod
    async def remove_one(cls, user_id, favorite_id: Any) -> None:
        await cls.storage.remove_favorite_one(user_id=user_id, favorite_id=favorite_id)

    @classmethod
    async def add_one(cls, user_id, favorite_id: Any, **data) -> None:
        await cls.storage.add_favorite_one(
            user_id=user_id,
            favorite_id=favorite_id,
            favorite_obj=cls._obj_data(**data)
        )

    @classmethod
    async def is_favorite(cls, user_id, favorite_id: Any) -> bool:
        return await cls.storage.is_favorite(user_id=user_id, favorite_id=favorite_id)

    @classmethod
    async def get_paged_ids(cls, user_id, page: int = 0, per_page: int = 7, sort_by: str | None = None) -> dict:
        start = page * per_page
        end = start + per_page
        favorites_all = await cls.storage.get_favorites_all(user_id=user_id)

        if sort_by is not None:
            favorites_all = {k: favorites_all[k]
                             for k in sorted(favorites_all, key=lambda f: favorites_all[f].get(sort_by))}

        ids = list(islice(favorites_all, start, end))
        result = dict(
            items=ids,
            count=len(ids),
            total=len(favorites_all),
            page=page,
            total_pages=math.ceil(len(favorites_all) / max(per_page, 1)),
        )
        return result

    @classmethod
    async def get_many(cls, user_id: int, page: int = 0, per_page: int = 5, sort_by: str | None = None,
                       **kwargs) -> paged_response:
        data = await cls.get_paged_ids(user_id=user_id, page=page, per_page=per_page, sort_by=sort_by)
        data['items'] = await cls.api.get_many_by_id(ids=data['items'])

        paged_response = cls.paged_response.model_validate(data)
        return paged_response

    @classmethod
    def _obj_data(cls, **data) -> dict:
        obj = data | dict(
            _created_at=datetime.now(tz=timezone.utc),
        )
        return obj


class FlightFavoriteService(FavoriteService):
    api = FlightEndpoint()
    storage = storage.FavoriteStorage(favorite_type='flight')
    paged_response = api_schemas.PagedFlightResponse
