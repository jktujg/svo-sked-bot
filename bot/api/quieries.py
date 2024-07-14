from datetime import datetime, timezone, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    AwareDatetime,
    field_serializer,
)


class FieldPattern(StrEnum):
    company_iata = r'^[A-Za-z0-9]{2}$'
    airport_iata = r'^[A-Za-z0-9]{3}$'
    flight_number = r'^[A-Za-z0-9]{1,4}$'
    airport_iata_many = r'^[A-Z]{3}(,[A-Z]{3})*$'
    company_iata_many = r'^[A-Z0-9]{2}(,[A-Z0-9]{2})*$'


class BaseQuery(BaseModel):
    page: int = 0
    limit: int = Field(5, ge=1, le=100)


class FlightsQuery(BaseQuery):
    direction: Literal['arrival', 'departure'] | None = None
    date_start: AwareDatetime = Field(..., default_factory=lambda: datetime.now(tz=timezone.utc)
                                      .replace(hour=0, minute=0, second=0, microsecond=0))
    date_end: AwareDatetime = Field(..., default_factory=lambda: datetime.now(tz=timezone.utc)
                                    .replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
    destination: str | None = Field(None, pattern=FieldPattern.airport_iata_many)
    company: str | None = Field(None, pattern=FieldPattern.company_iata_many)
    number: str | None = Field(None, pattern=FieldPattern.flight_number)
    gate_id: str | None = Field(None)
    term_local: str | None = Field(None)
    order: Literal['asc', 'desc'] = 'asc'
    page: int = 0
    limit: int = Field(5, ge=1, le=100)

    @field_serializer('destination', 'company', 'number', 'gate_id', 'term_local')
    def to_upper(self, field: str) -> str:
        if field is not None:
            return field.upper()
