from datetime import datetime, timezone, timedelta
from unittest import TestCase

from bot.search_engine import filters


class TestFilters(TestCase):
    def test_date_filter_valid(self):
        self.assertIsNotNone(filters.DateFilter()(['10.12.24'])['date'])
        self.assertDictEqual(
            filters.DateFilter()(['10.12.24']),
            dict(date=datetime.now(tz=timezone(timedelta(hours=3))).replace(day=10, month=12, year=2024,
                                                                            hour=0, minute=0, second=0, microsecond=0))
        )

    def test_company_flight_filter_valid(self):
        self.assertDictEqual(
            filters.CompanyFlightFilter()(['su1712']),
            dict(company_iata='SU', number='1712')
        )

    def test_flight_number_filter_valid(self):
        self.assertDictEqual(
            filters.FlightNumberFilter()(['1712']),
            dict(number='1712')
        )

    def test_direction_filter_valid(self):
        self.assertDictEqual(
            filters.DirectionFilter()(['Прилет']),
            dict(direction='arrival')
        )

    def test_date_word_filter_valid(self):
        self.assertDictEqual(
            filters.DateWordFilter()(['Сегодня']),
            dict(
                date_word='сегодня',
                date=datetime.now(tz=timezone(timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0),
            )
        )

    def test_company_iata_filter_valid(self):
        self.assertDictEqual(
            filters.CompanyIataFilter()(['n4']),
            dict(company_iata='N4')
        )

    def test_airport_iata_filter_valid(self):
        self.assertDictEqual(
            filters.AirportIataFilter()(['Led']),
            dict(airport_iata='LED'),
        )

    def test_country_name_filter_valid(self):
        self.assertDictEqual(
            filters.CountryNameFilter()(['армения']),
            dict(country_name='Армения', country_airport_iata=['EVN']),
        )

    def test_company_name_filter_valid(self):
        self.assertDictEqual(
            filters.CompanyNameFilter()(['аэрофлот']),
            dict(company_iata='SU'),
        )

    def test_airport_name_filter_valid(self):
        self.assertDictEqual(
            filters.AirportNameFilter()(['пулково']),
            dict(airport_iata='LED'),
        )
