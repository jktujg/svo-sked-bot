from datetime import datetime

from aiogram.utils.deep_linking import create_deep_link

from .settings import settings


def ftime(time: datetime | None, placeholder='...') -> str:
    if time is None:
        return placeholder
    return time.strftime('%H:%M')


def ftimezone(time: datetime | None, placeholder='...'):
    if time is None:
        return placeholder

    tz = time.strftime('%z')
    hours, minutes = map(int, [tz[:3], tz[3:]])
    result = 'UTC'
    if hours != 0 or minutes != 0:
        result += f' {hours:+}'
    if minutes !=0:
        result += f':{minutes:0>2}'
    return result


def fdate(date: datetime | None, placeholder='...') -> str:
    if date is None:
        return placeholder
    return date.strftime('%d.%m.%Y')


def create_flight_link(flight_id: int) -> str:
    payload = f'flight-{flight_id}'
    url = create_deep_link(settings.BOT_NAME, link_type='start', payload=payload, encode=True)
    return url
