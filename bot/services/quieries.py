from datetime import timezone, timedelta

from pydantic import field_validator, Field, AliasChoices, AwareDatetime

from bot.api import quieries as api_quieries


class FlightServiceQuery(api_quieries.FlightsQuery):
    destination: str | None = Field(None, pattern=api_quieries.FieldPattern.airport_iata_many,
                                    validation_alias=AliasChoices('destination', 'airport_iata'))
    company: str | None = Field(None, pattern=api_quieries.FieldPattern.company_iata_many,
                                validation_alias=AliasChoices('company'))

    @field_validator('company', 'destination', mode='before')
    @classmethod
    def _iata_from(cls, data) -> str:
        if not isinstance(data, None | str):
            return data.iata
        else:
            return data

    @field_validator('date_start', 'date_end', mode='after')
    @classmethod
    def _as_timezone(cls, date: AwareDatetime) -> AwareDatetime:
        return date.astimezone(tz=timezone(timedelta(hours=3)))


class SaveFlightServiceQuery(FlightServiceQuery):
    """ Используется для сохранения параметров, которые не должны передаваться в запросе """
    country_name: str | None = None
