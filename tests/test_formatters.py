from unittest import TestCase
from datetime import datetime, timezone, timedelta

from bot import formatters


class TestFormatters(TestCase):
    def test_ftime(self):
        date = datetime.now().replace(hour=10, minute=5)
        self.assertEqual(formatters.ftime(date), '10:05')

    def test_ftimezone_hour_only(self):
        date = datetime.now(tz=timezone(timedelta(hours=7)))
        self.assertEqual(formatters.ftimezone(date), 'UTC +7')

    def test_ftimezone_with_minutes(self):
        date = datetime.now(tz=timezone(timedelta(hours=-5, minutes=-30)))
        self.assertEqual(formatters.ftimezone(date), 'UTC -5:30')

    def test_ftimezone_zero_hour_with_minute(self):
        date = datetime.now(tz=timezone(timedelta(hours=0, minutes=-30)))
        self.assertEqual(formatters.ftimezone(date), 'UTC +0:30')

    def test_ftimezone_utc(self):
        date=datetime.now(tz=timezone.utc)
        self.assertEqual(formatters.ftimezone(date), 'UTC')

    def test_fdate(self):
        date = datetime(year=2024, month=7, day=3)
        self.assertEqual(formatters.fdate(date), '03.07.2024')
