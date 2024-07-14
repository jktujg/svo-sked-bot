from asyncio import to_thread
from datetime import datetime, timezone
from typing import Literal

import pymongo

from .db import db


class SearchQueryStorage:
    collection = db.search_queries

    def __init__(self, query_type: Literal['flight']):
        self._query_type = query_type

    async def get_one(self, message_id: int) -> dict | None:
        projection = {self._query_type: 1}
        filter = {'message_id': message_id}

        query_data = await to_thread(
            self.collection.find_one,
            filter,
            projection,
        )
        if query_data is not None:
            query_data = query_data.get(self._query_type)

        return query_data

    async def upsert_one(self, message_id: int, update: dict) -> None:
        filter = {f'message_id': message_id}
        query = {'$set': {self._query_type: update | {'_updated_at': datetime.now(tz=timezone.utc)}}}

        await to_thread(
            self.collection.update_one,
            filter,
            query,
            upsert=True,
        )


class FavoriteStorage:
    collection = db.favorites
    collection.create_index([('user_id', pymongo.ASCENDING)], unique=True)

    def __init__(self, favorite_type: Literal['flight']):
        self._favorite_type = favorite_type

    async def add_favorite_one(self, user_id: int, favorite_id: int, favorite_obj: dict) -> None:
        field = f'{self._favorite_type}.{favorite_id}'
        filter = {'user_id': user_id}
        query = [{
            '$set': {
                field: {
                    '$cond': {
                        'if': {'$not': [f'${field}']},
                        'then': favorite_obj,
                        'else': f'${field}'
                    }}}}]
        options = {'upsert': True}

        await to_thread(
            self.collection.update_one,
            filter,
            query,
            **options,
        )

    async def remove_favorite_one(self, user_id: int, favorite_id: int) -> None:
        filter = {'user_id': user_id}
        query = {'$unset': {f'{self._favorite_type}.{favorite_id}': ''}}

        await to_thread(
            self.collection.update_one,
            filter,
            query,
        )

    async def get_favorites_all(self, user_id: int) -> dict:
        filter = {'user_id': user_id}
        projection = {self._favorite_type: 1}

        favorites = (await to_thread(
            self.collection.find_one,
            filter,
            projection
        ))

        favorites = (favorites or {}).get(self._favorite_type, {})
        return favorites

    async def is_favorite(self, user_id: int, favorite_id: int) -> bool:
        filter = {'user_id': user_id, f'{self._favorite_type}.{favorite_id}': {'$exists': True}}
        projection = {'_id': 1}

        favorite = await to_thread(
            self.collection.find_one,
            filter,
            projection,
        )
        return bool(favorite)
