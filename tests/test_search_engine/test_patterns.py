from unittest import TestCase

from bot.search_engine.patterns import Regex


class TestRegex(TestCase):
    def test_company_iata_match(self):
        self.assertDictEqual(Regex.company_iata.search('n4').groupdict(), dict(company_iata='n4'))
        self.assertDictEqual(Regex.company_iata.search('some N4 value').groupdict(), dict(company_iata='N4'))

    def test_airport_iata_match(self):
        self.assertDictEqual(Regex.airport_iata.search('led').groupdict(), dict(airport_iata='led'))
        self.assertDictEqual(Regex.airport_iata.search('other LED value').groupdict(), dict(airport_iata='LED'))

    def test_date_match(self):
        self.assertDictEqual(Regex.date.search('10.').groupdict(), dict(day='10', month=None, year=None))
        self.assertDictEqual(Regex.date.search('10.09').groupdict(), dict(day='10', month='09', year=None))
        self.assertDictEqual(Regex.date.search('10.09.2024').groupdict(), dict(day='10', month='09', year='2024'))

    def test_date_not_match(self):
        self.assertIsNone(Regex.date.search('10'))

    def test_date_word_match(self):
        for word in ('Сегодня', 'Завтра', 'Вчера'):
            with self.subTest(word=word):
                self.assertDictEqual(Regex.date_word.search(word).groupdict(), dict(date_word=word))

    def test_company_flight_match(self):
        self.assertDictEqual(Regex.company_flight.search('N41512').groupdict(), dict(company_iata='N4', number='1512'))
        self.assertDictEqual(Regex.company_flight.search('N4 1').groupdict(), dict(company_iata='N4', number='1'))
        self.assertDictEqual(Regex.company_flight.search('N4 B172').groupdict(), dict(company_iata='N4', number='B172'))

    def test_flight_match(self):
        number = '1234B'
        for i in range(4):
            number = number[1:] + number[0]
            test_num = number[:-1]
            with self.subTest(test_num=test_num):
                self.assertEqual(Regex.flight.search(test_num).groupdict()['number'], test_num)
