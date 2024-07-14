from enum import StrEnum
from datetime import timezone, timedelta

import emoji


SVO_TIMEZONE = timezone(timedelta(hours=3))


class DIRECTION(StrEnum):
    arrival = 'прилет'
    departure = 'вылет'


class COUNTER_DIRECTION(StrEnum):
    arrival = 'departure'
    departure = 'arrival'


class EMOJI(StrEnum):
    airplane_arrival = emoji.emojize(':airplane_arrival:', language='alias')
    airplane_departure = emoji.emojize(':airplane_departure:', language='alias')
    time_et = emoji.emojize(':check_box_with_check:', language='alias')
    time_start = emoji.emojize(':white_check_mark:', language='alias')
    time_end = emoji.emojize(':negative_squared_cross_mark:', language='alias')
    time_close = emoji.emojize(':no_entry:', language='alias')
    idk = emoji.emojize(':man_shrugging:', language='alias')
    no = emoji.emojize(':man_gesturing_no:', language='alias')
    arrow_left = emoji.emojize(':arrow_left:', language='alias')
    arrow_right = emoji.emojize(':arrow_right:', language='alias')
    red_heart = emoji.emojize(':heart:', language='alias')
    white_heart = emoji.emojize(':white_heart:', language='alias')


class INLINE_PLANE_IMAGE(StrEnum):
    arrival = 'https://i.postimg.cc/sg1TsdL4/plane-arrival-icon.png'
    departure = 'https://i.postimg.cc/02VVT2VN/plane-departure-icon.png'


GREETING = """👋 Приветствую Вас!\n
Чтобы найти рейс, отправьте мне его номер или укажите параметры для поиска.\n
<i>Например:</i>
<blockquote><code>SU1152 {today}</code></blockquote>
<i>или</i>
<blockquote><code>Вылет Сочи сегодня Аэрофлот</code></blockquote>
<i>или</i>
<blockquote><code>AER SU</code></blockquote>
"""

