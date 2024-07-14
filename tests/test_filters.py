import asyncio
from datetime import datetime, timezone, timedelta
from unittest import TestCase
from unittest.mock import Mock, patch

from bot.filters import SearchFlightFilter


class TestSearchFlightFilter(TestCase):
    def setUp(self):
        self.filter = SearchFlightFilter()

    @patch('bot.filters.param_search')
    @patch('bot.filters.co_number_search')
    def test_search_text_with_number(self, co_number_search, param_search):
        self.filter._search('su1712')
        self.assertTrue(co_number_search.called)
        self.assertFalse(param_search.called)

    @patch('bot.filters.param_search')
    def test_search_text_without_number(self, param_search):
        self.filter._search('Аэрофлот завтра')
        self.assertTrue(param_search.called)

    def test_prepare_search_result(self):
        search_result = dict(
            company_iata='SU',
            airport_iata='LED',
            number='10',
        )
        self.filter._prepare_search_result(search_result)
        today = datetime.now(tz=timezone(timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0)

        self.assertDictEqual(
            search_result,
            dict(
                company='SU',
                destination='LED',
                date_start=today,
                date_end=today + timedelta(days=1),
                number='010'
            ))

    def test_prepare_search_result_multiple_destination(self):
        search_result = dict(country_airport_iata=['LED', 'KHV', 'EVN'])
        self.filter._prepare_search_result(search_result)

        self.assertEqual(search_result['destination'], 'LED,KHV,EVN')

    def test_dunder_call_return_params(self):
        update = Mock(query='SU 1712')
        search_result = asyncio.run(self.filter(update))['search_params']

        self.assertEqual(search_result['company'], 'SU')
        self.assertEqual(search_result['number'], '1712')

    def test_dunder_call_return_none(self):
        search_result = asyncio.run(self.filter(Mock(query='')))

        self.assertIsNone(search_result)
