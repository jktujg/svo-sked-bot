import re
from enum import Enum


class Regex(Enum):
    company_iata = re.compile(r'(^|\s+)(?P<company_iata>\d[a-z]|[a-z]\d|[a-z]{2})(\s+|$)', re.I)
    airport_iata = re.compile(r'(^|\s+)(?P<airport_iata>[a-z]{3})(\s+|$)', re.I)
    date = re.compile(r'(^|\s+)((?P<day>\d{1,2})\.)(?P<month>\d{1,2})?(?(month)\.(?P<year>\d{4}|\d{2}))?(\s+|$)')
    date_word = re.compile(r'(^|\s+)(?P<date_word>вчера|сегодня|завтра)(\s+|$)', re.I)
    company_flight = re.compile(r'(^|\s+)((?P<company_iata>[a-z]\d|\d[a-z]|[a-z]{2})\s*((?P<number>\d{1,4}|\d{3}[a-z]|\d{2}[a-z]\d|\d[a-z]\d{2}|[a-z]\d{3})(\s+|$)))', re.I)
    flight = re.compile(r'(^|\s+)(?P<number>\d{1,4}|\d{3}[a-z]|\d{2}[a-z]\d|\d[a-z]\d{2}|[a-z]\d{3})(\s+|$)', re.I)

    def search(self, string: str) -> re.Match | None:
        return self.value.search(string)
