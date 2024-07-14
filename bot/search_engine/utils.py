import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


def date_from_input(day: int | None = None,
                    month: int | None = None,
                    year: int | None = None,
                    inc_days: int | None = None,
                    **kw
                    ) -> datetime | None:

    if not any([day, month, year, inc_days]):
        return None

    date = datetime.now(tz=timezone(timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0)
    if inc_days:
        date += timedelta(days=inc_days)
    else:
        try:
            date = date.replace(
                year=int(('20' + str(year or date.year))[-4:]),
                month=int(month or date.month),
                day=int(day or date.day),
            )
        except ValueError:
            return

    return date


class JsonFileLoader:
    def __init__(self, **file_paths: str | Path):
        self._data = {}
        self.load_files(**file_paths)

    def __getattr__(self, attr: str) -> Any:
        try:
            return self._data[attr]
        except KeyError:
            raise AttributeError(f'"{self.__class__.__name__}" object has not attribute "{attr}"')

    def load_files(self, **file_paths: str | Path) -> None:
        for attr, file_path in file_paths.items():
            with open(file_path, 'r') as file:
                self._data[attr] = json.load(file)
