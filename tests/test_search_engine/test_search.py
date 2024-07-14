from datetime import datetime, timezone, timedelta
from unittest import TestCase
from itertools import permutations

from bot.search_engine import search


class TestFlightNumberSearch(TestCase):
    def setUp(self):
        self.search = search.FlightNumberSearch()

    def test_all_filters(self):
        words = ['завтра', '20.12', 'su', 'nordwind', '1720', 'not filtered']
        result_dict = dict(
            date=datetime.now(tz=timezone(timedelta(hours=3))).replace(day=20, month=12, hour=0, minute=0, second=0, microsecond=0),
            company_iata='SU',
            number='1720',
            date_word='завтра'
        )

        for word_list in permutations(words):
            input_text = ' '.join(word_list)
            with self.subTest(input_text=input_text):
                self.assertDictEqual(self.search(input_text), result_dict)


class TestParamSearch(TestCase):
    def setUp(self):
        self.search = search.ParamsSearch()

    def test_all_filters(self):
        words = ['not_filtered', '1720', 'Армения', 'вылет', 'завтра', '20.12', 'Калининград', 'led', 'nordwind', 'su']
        result_dict = dict(
            direction='departure',
            airport_iata='LED',
            company_iata='SU',
            country_name='Армения',
            country_airport_iata=['EVN'],
            date=datetime.now(tz=timezone(timedelta(hours=3))).replace(day=20, month=12, hour=0, minute=0, second=0, microsecond=0),
            date_word='завтра',
        )

        self.assertDictEqual(self.search(' '.join(words)), result_dict)


class TestSearchFunc(TestCase):
    def test_get_company_name(self):
        self.assertEqual(search.get_company_name('SU'), 'Аэрофлот')
        self.assertIsNone(search.get_company_name('UU'))

    def test_get_airport_city(self):
        self.assertEqual(search.get_airport_city('CSY', lang='ru'), 'Чебоксары')
        self.assertEqual(search.get_airport_city('CSY', lang='en'), "Cheboksary")

        self.assertIsNone(search.get_airport_city('CSY', lang='??'))
        self.assertIsNone(search.get_airport_city('111'))

    def test_get_company_name_non_stirng_return_none(self):
        self.assertIsNone(search.get_company_name(None))
    def test_get_airport_city_non_string_return_none(self):
        self.assertIsNone(search.get_airport_city(None))
