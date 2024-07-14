from collections import defaultdict
from datetime import datetime
from enum import StrEnum
from typing import Literal, Annotated, Any
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    AnyHttpUrl,
    AwareDatetime,
    model_validator,
    computed_field,
    field_validator,
)


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )


class AircraftSchema(BaseSchema):
    name: str
    orig_id: int


class CountrySchema(BaseSchema):
    name: str
    region: str | None = None


class CitySchema(BaseSchema):
    name: str
    name_ru: str
    timezone: ZoneInfo
    country: CountrySchema

    @field_validator('timezone', mode='before')
    @classmethod
    def validate_timezone(cls, timezone: str) -> ZoneInfo:
        return ZoneInfo(timezone)


class AirportSchema(BaseSchema):
    iata: str
    icao: str | None
    code_ru: str | None
    orig_id: int | None
    name: str
    name_ru: str
    lat: float | None = None
    long: float | None = None
    city: CitySchema


class CompanySchema(BaseSchema):
    iata: str
    name: str | None = None
    url_buy: Annotated[str, AnyHttpUrl] | None = None
    url_register: Annotated[str, AnyHttpUrl] | None = None


class ChangelogFlightSchema(BaseModel):
    field: str
    old_value: str | None
    created_at: AwareDatetime


class FlightSchema(BaseSchema):
    id: int
    orig_id: int
    company: CompanySchema
    mar1: AirportSchema | None = None
    mar2: AirportSchema | None = None
    mar3: AirportSchema | None = None
    mar4: AirportSchema | None = None
    mar5: AirportSchema | None = None
    aircraft: AircraftSchema
    direction: Literal['arrival', 'departure']
    number: str
    date: AwareDatetime
    main_orig_id: int | None = None
    way_time: int | None = None
    # check-in
    chin_start: AwareDatetime | None = None
    chin_end: AwareDatetime | None = None
    chin_start_et: AwareDatetime | None = None
    chin_end_et: AwareDatetime | None = None
    chin_id: str | None = None
    # boarding
    boarding_start: AwareDatetime | None = None
    boarding_end: AwareDatetime | None = None
    gate_id: str | None = None
    gate_id_prev: str | None = None
    # terminal
    term_local: str | None = None
    term_local_prev: str | None = None
    # bag belt
    bbel_id: str | None = None
    bbel_id_prev: str | None = None
    bbel_start: AwareDatetime | None = None
    bbel_start_et: AwareDatetime | None = None
    bbel_end: AwareDatetime | None = None
    # schedule
    sked_local: AwareDatetime | None = None
    sked_other: AwareDatetime | None = None
    # landing / takeoff
    at_local: AwareDatetime | None = None
    at_local_et: AwareDatetime | None = None
    at_other: AwareDatetime | None = None
    at_other_et: AwareDatetime | None = None
    takeoff_et: AwareDatetime | None = None
    # departure / arrival to pk
    otpr: AwareDatetime | None = None
    prb: AwareDatetime | None = None
    # status
    status_id: int | None = None
    status_code: int | None = None
    # changelog
    chin_id_log: list[tuple[str | None, AwareDatetime]] = Field(default_factory=list)
    gate_id_log: list[tuple[str | None, AwareDatetime]] = Field(default_factory=list)
    term_local_log: list[tuple[str | None, AwareDatetime]] = Field(default_factory=list)
    bbel_id_log: list[tuple[str | None, AwareDatetime]] = Field(default_factory=list)

    @property
    def local_mar(self) -> AirportSchema:
        return getattr(self, 'mar1' if self.direction == 'departure' else 'mar2')

    @property
    def other_mar(self) -> AirportSchema:
        return getattr(self, 'mar1' if self.direction == 'arrival' else 'mar2')

    @property
    def is_delayed(self) -> bool:
        if self.direction == 'departure':
            try:
                if self.sked_local < self.at_local_et:
                    return True
            except TypeError:
                return False

    @model_validator(mode='before')
    @classmethod
    def validate_logs(cls, data: Any):
        if isinstance(data, dict):
            suffix = '_log'
            log_data = defaultdict(list)
            log_fields = {field for field in cls.model_fields if field.endswith(suffix)}

            for log in data.get('changelog', []):
                log_field = log["field"] + "_log"
                value = log['old_value']
                date = log['created_at']
                try:
                    value = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    pass
                log_data[log_field].append((value, date))

            for field in log_fields:
                log_data[field] = list(zip(
                    [data[field.removesuffix(suffix)]] + [d[0] for d in log_data.get(field, [])],
                    [d[1] for d in log_data.get(field, [])] + [data['created_at']]
                ))

            return {**data, **log_data}

    @model_validator(mode='after')
    def timezonify(self):
        dep_times = ['chin_start', 'chin_end', 'chin_start_et', 'chin_end_et', 'boarding_start', 'boarding_end', 'otpr',
                     'takeoff_et']
        arr_times = ['bbel_start', 'bbel_start_et', 'bbel_end', 'prb']

        local_times = ['sked_local', 'at_local', 'at_local_et']
        other_times = ['sked_other', 'at_other', 'at_other_et']

        local_times.extend(dep_times if self.direction == 'departure' else arr_times)
        other_times.extend(dep_times if self.direction == 'arrival' else arr_times)

        for fields, tz in [(local_times, self.local_mar.city.timezone), (other_times, self.other_mar.city.timezone)]:
            for field in fields:
                value = getattr(self, field, None)
                if value is not None:
                    setattr(self, field, value.astimezone(tz))

        self.date = self.date.astimezone(self.local_mar.city.timezone)

        return self

    @computed_field
    @property
    def status(self) -> str:
        status_enum = dict(arrival=ArrivalStatus, departure=DepartureStatus)[self.direction]
        for stage in status_enum:
            if getattr(self, stage.name, None) is not None:
                return stage.value
        else:
            return status_enum.base_status


class ArrivalStatus(StrEnum):
    bbel_end = 'Выдача багажа закончена'
    bbel_start = 'Идет выдача багажа'
    prb = 'Прибыл на стоянку'
    at_local = 'Совершил посадку'
    at_other = 'Летит'
    base_status = ''


class DepartureStatus(StrEnum):
    at_other = 'Совершил посадку'
    at_local = 'Летит'
    otpr = 'Отправлен'
    boarding_end = 'Посадка закончена'
    boarding_start = 'Посадка идет'
    chin_end = 'Регистрация закончена'
    chin_start = 'Регистрация идет'
    base_status ='Ожидание начала регистрации'


class PagedResponse(BaseSchema):
    items: list = Field(default_factory=list)
    count: int = 0
    total: int = 0
    page: int = 0
    total_pages: int = 0


class PagedFlightResponse(PagedResponse):
    items: list[FlightSchema] = Field(default_factory=list)
