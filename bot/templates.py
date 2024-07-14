import re
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Type

from aiogram.enums.parse_mode import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.utils.markdown import hide_link

from . import (
    callback_data as cd,
    formatters,
)
from .api import schemas
from .constants import (
    EMOJI,
    SVO_TIMEZONE,
    DIRECTION,
    GREETING
)
from .search_engine import get_company_name, get_airport_city


class BaseTemplate(metaclass=ABCMeta):
    parse_mode: Type[ParseMode] | None = ParseMode.HTML

    @abstractmethod
    def get_keyboard(self, resize_keyboard=True, **kwargs) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
        ...

    @abstractmethod
    def get_message(self) -> str:
        ...

    def as_kwargs(self, exclude: set = None, keyboard_kw: dict | None = None) -> dict:
        d = dict(
           text=self.get_message(),
           reply_markup=self.get_keyboard(**(keyboard_kw or {})),
           parse_mode=self.parse_mode,
        )
        for field in exclude or set():
            d.pop(field, None)
        return d

    def has_same_text(self, text: str) -> bool:
        return text == re.sub(r'<.*?>', '', self.get_message()).strip()

    def has_same_markup(self, markup: InlineKeyboardMarkup) -> bool:
        new_kb = self.get_keyboard().inline_keyboard

        try:
            for x, line in enumerate(markup.inline_keyboard):
                for y, btn in enumerate(line):
                    if new_kb[x][y].text != btn.text:
                        return False
        except IndexError:
            return False
        else:
            return True


class StartCMDTemplate(BaseTemplate):
    def get_message(self) -> str:
        return GREETING.format(today=datetime.now(tz=SVO_TIMEZONE).strftime('%d.%m'))

    def get_keyboard(self, resize_keyboard=True, **kwargs) -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()
        kb.button(text="Избранное")
        return kb.as_markup(resize_keyboard=resize_keyboard, **kwargs)


class SearchFlightTemplate(BaseTemplate):
    def __init__(self, response: schemas.PagedFlightResponse, query: dict):
        self.response = response
        self.query = query

    def get_message(self) -> str:
        lines = [
            self._message_flight_num_line,
            self._message_company_line,
            self._message_destination_line,
            self._message_flight_count_line,
        ]

        line = '\n'.join(line for line in lines if line is not None).strip()
        return line

    def get_keyboard(self, resize_keyboard=True, **kwargs) -> InlineKeyboardMarkup:
        buttons = [
            self._keyboard_date_btn,
            self._keyboard_direction_btn,
            self._keyboard_show_btn,
        ]

        kb = InlineKeyboardBuilder()
        kb.add(*(btn for btn in buttons if btn is not None))

        return kb.as_markup(resize_keyboard=resize_keyboard, **kwargs)

    @staticmethod
    def get_message_not_found() -> str:
        line = '{marker} По вашему запросу ничего не найдено'.format(
            marker=EMOJI.idk,
        )
        return line

    @property
    def _message_flight_num_line(self) -> str | None:
        line = 'Номер рейса: <b>{number}</b>'.format(
            number=(self.query.get('company') or '') + self.query.get('number')
        ) if self.query.get('number') is not None else None

        return line

    @property
    def _message_company_line(self) -> str:
        line =  'Авиакомпания: <b>{company_name}</b>'.format(
            company_name=get_company_name(self.query.get('company')) or '-'
        )

        return line

    @property
    def _message_destination_line(self) -> str | None:
        line = 'Направление: <b>{airport_city}</b>'.format(
            airport_city=self.query.get('country_name') or get_airport_city(self.query.get('destination')) or '-'
        ) if self.query.get('number') is None else None

        return line

    @property
    def _message_flight_count_line(self) -> str | None:
        line = 'Найдено рейсов: <b>{total_flights}</b>'.format(
            total_flights=str(self.response.total) + 'ㅤ' * 8
        ) if self.response.total is not None else None

        return line

    @property
    def _keyboard_date_btn(self) -> InlineKeyboardButton:
        btn = InlineKeyboardButton(
            text=formatters.fdate(self.query['date_start']),
            callback_data=cd.SearchFlightCD(action=cd.SearchFlightAction.pick_date).pack(),
        )
        return btn

    @property
    def _keyboard_direction_btn(self) -> InlineKeyboardButton | None:
        btn = None

        if (direction := self.query.get('direction')) is not None:
            btn = InlineKeyboardButton(
                text=DIRECTION[direction].capitalize(),
                callback_data=cd.SearchFlightCD(action=cd.SearchFlightAction.toggle_direction).pack(),
            )

        return btn

    @property
    def _keyboard_show_btn(self) -> InlineKeyboardButton | None:
        btn = None

        if self.response.total > 1:
            btn = InlineKeyboardButton(
                text='Показать',
                switch_inline_query_current_chat=self._inline_query_text,
            )
        elif self.response.total == 1:
            btn = InlineKeyboardButton(
                text='Показать',
                callback_data=cd.FlightCD(action=cd.FlightAction.show, changelog=False, id=self.response.items[0].id).pack(),
            )

        return btn

    @property
    def _inline_query_text(self) -> str:
        if number := self.query.get('number'):
            query_text = ' '.join(filter(bool, (
                self.query.get('company'),
                number,
                formatters.fdate(date=self.query.get('date_start'), placeholder=None),
            ))
                                  )
        else:
            query_text = ' '.join(filter(bool, (
                self.query.get('country_name') or get_airport_city(self.query.get('destination')),
                get_company_name(self.query.get('company') or ''),
                formatters.fdate(date=self.query.get('date_start'), placeholder=None),
                DIRECTION[direction] if (direction := self.query.get('direction')) else None,
            )))
        return query_text


class FavoriteFlightTemplate(BaseTemplate):
    def __init__(self, response: schemas.PagedFlightResponse, query: dict):
        self.response = response
        self.query = query

    def get_message(self) -> str:
        if self.response.total == 0:
            msg = 'У Вас нет избранных рейсов'
        else:
            msg = 'Найдено избранных рейсов: {total}'.format(
                total=self.response.total,
            )
        return msg

    def get_keyboard(self, resize_keyboard=True, **kwargs) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        if self.response.total > 0:
            kb.button(text='Показать', switch_inline_query_current_chat='favorite')
        return kb.as_markup(resize_keyboard=resize_keyboard, **kwargs)


class FlightTemplate(BaseTemplate):
    def __init__(self, flight: schemas.FlightSchema, changelog: bool = False, is_favorite: bool = False):
        self._changelog = changelog
        self._flight = flight
        self._is_favorite = is_favorite

    @property
    def _keyboard_update_btn(self) -> InlineKeyboardButton:
        btn = InlineKeyboardButton(
            text='Обновить',
            callback_data=cd.FlightCD(id=self._flight.id, changelog=self._changelog, action=cd.FlightAction.update).pack(),
        )
        return btn

    @property
    def _keyboard_favorite_btn(self) -> InlineKeyboardButton:
        btn = InlineKeyboardButton(
            text=EMOJI.white_heart if self._is_favorite is False else EMOJI.red_heart,
            callback_data=cd.FlightCD(id=self._flight.id, changelog=self._changelog, action=cd.FlightAction.toggle_favorite).pack(),
        )
        return btn

    @property
    def _keyboard_change_btn(self) -> InlineKeyboardButton:
        btn = InlineKeyboardButton(
            text='Изменения',
            callback_data=cd.FlightCD(id=self._flight.id, changelog=not self._changelog, action=cd.FlightAction.toggle_changelog).pack(),
        )
        return btn

    @property
    def _keyboard_share_btn(self) -> InlineKeyboardButton:
        btn = InlineKeyboardButton(
            text='Поделиться',
            switch_inline_query=f'id_{self._flight.id}',
        )
        return btn

    def get_keyboard(self, resize_keyboard=True, **kwargs) -> InlineKeyboardMarkup:
        buttons = [
            self._keyboard_update_btn,
            self._keyboard_favorite_btn,
            self._keyboard_change_btn,
            self._keyboard_share_btn
        ]
        kb = InlineKeyboardBuilder()
        kb.add(*buttons)
        kb.adjust(3, 1)
        return kb.as_markup(resize_keyboard=resize_keyboard, **kwargs)

    def get_message(self) -> str:
        raise NotImplemented

    @property
    def url(self) -> str:
        return formatters.create_flight_link(flight_id=self._flight.id)

    def get_inline_query_message(self) -> str:
        return self.get_message() + '\n' + hide_link(self.url)

    def get_inline_query_title(self) -> str:
        f = self._flight
        description = '{time}  {city} {mar_iata}{favorite_mark}'.format(
            favorite_mark=' ' + EMOJI.red_heart if self._is_favorite else '',
            time=formatters.ftime(f.sked_local),
            city=f.other_mar.city.name_ru,
            mar_iata=f.other_mar.iata,
        )
        return description

    def get_inline_query_description(self) -> str:
        f = self._flight
        title = '{date}    {co_iata}{number}\n{status}'.format(
            date=f.date.strftime('%d.%m') if f.date is not None else '...',
            co_iata=f.company.iata,
            number=f.number,
            status=f.status,
        )
        return title

    def get_inline_query_keyboard(self, resize_keyboard=True, **kwargs) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        kb.button(text='Поделиться', switch_inline_query=f'id_{self._flight.id}')
        kb.button(text='Перейти в Бот', url=self.url)
        kb.adjust(2)

        return kb.as_markup(resize_keyboard=resize_keyboard, **kwargs)


class FlightArrivalTemplate(FlightTemplate):
    def get_message(self) -> str:
        lines = [
            self._message_flight_num_line + '\n',
            self._message_destination_line,
            self._message_status_line + '\n' if self._message_status_line else None,
            self._message_terminal_line,
            self._message_belt_line + '\n',
            self._message_aircraft_line,
            self._message_other_airport_line,
            self._message_local_airport_line,
            self._message_prb_line + '\n',
            ]

        if self._changelog:
            lines.extend(self._message_changelog_lines)

        content = '\n'.join(line for line in lines if line is not None).strip()
        return content

    @property
    def _message_flight_num_line(self) -> str:
        line = '<b>{direction}  <u>{iata}{number} {date}</u></b>'.format(
            direction=EMOJI.airplane_arrival,
            iata=self._flight.company.iata,
            number=self._flight.number,
            date=formatters.fdate(self._flight.date),
        )
        return line

    @property
    def _message_destination_line(self) -> str:
        line = '<b>{time} {city} <i>{iata}</i></b>'.format(
            time=formatters.ftime(self._flight.sked_local),
            city=self._flight.mar1.city.name_ru,
            iata=self._flight.mar1.iata,
        )
        return line

    @property
    def _message_status_line(self) -> str | None:
        line = '<i>{status}</i>'.format(
            status=self._flight.status,
        ) if self._flight.status else None

        return line

    @property
    def _message_terminal_line(self) -> str:
        line = 'Терминал: <b>{term}</b>'.format(
            term=self._flight.term_local
        )
        return line

    @property
    def _message_belt_line(self) -> str:
        line = '{marker} Выдача багажа: <b>{belt} {start} - {end}</b>'.format(
            marker=EMOJI.time_end if self._flight.bbel_end else (EMOJI.time_start if self._flight.bbel_start else EMOJI.time_et),
            belt=f'№{self._flight.bbel_id or "..."}',
            start=formatters.ftime(self._flight.bbel_start or self._flight.bbel_start_et),
            end=formatters.ftime(self._flight.bbel_end),
        )
        return line

    @property
    def _message_aircraft_line(self) -> str:
        line = 'Борт: <b>{aircraft}</b>'.format(
            aircraft=self._flight.aircraft.name
        )
        return line

    @property
    def _message_other_airport_line(self) -> str:
        line = '{marker} Взлёт: <b>{airport} <i>({timezone})</i> {takeoff}</b>'.format(
            marker=EMOJI.time_start if self._flight.at_other else EMOJI.time_et,
            takeoff=formatters.ftime(self._flight.at_other or self._flight.at_other_et or self._flight.sked_other),
            timezone=formatters.ftimezone(self._flight.at_other or self._flight.at_other_et or self._flight.sked_other),
            airport=self._flight.mar1.name_ru,
        )
        return line

    @property
    def _message_local_airport_line(self) -> str:
        line = '{marker} Приземление: <b>{airport} <i>({timezone})</i> {landing}</b>'.format(
            marker=EMOJI.time_start if self._flight.at_local else EMOJI.time_et,
            landing=formatters.ftime(self._flight.at_local or self._flight.at_local_et or self._flight.sked_local),
            timezone=formatters.ftimezone(self._flight.at_local or self._flight.at_local_et or self._flight.sked_local),
            airport=self._flight.mar2.name_ru,
        )
        return line

    @property
    def _message_prb_line(self) -> str:
        line = '{marker} Прибытие на стоянку: <b>{prb}</b>'.format(
            marker=EMOJI.time_start if self._flight.prb else EMOJI.time_et,
            prb=formatters.ftime(self._flight.prb, placeholder='-'),
        )
        return line

    @property
    def _message_changelog_lines(self) -> list[str]:
        changelog = [
            '<b><u>Изменения:</u></b>',
            '  <u>Терминал:</u>',
            *self._changelog_terminal_changes,
            '  <u>Багажная лента:</u>',
            *self._changelog_belt_changes,
        ]
        return changelog

    @property
    def _changelog_terminal_changes(self) -> list[str]:
        changes = []
        for e, (term, time) in enumerate(self._flight.term_local_log):
            if not (not len(self._flight.term_local_log) != 1 and (
                    e == 0 or e == len(self._flight.term_local_log) - 1) and term is None):
               changes.append(
                   '  <i>{time}</i>    <b>{term}</b>'.format(
                       time=formatters.ftime(time.astimezone(self._flight.local_mar.city.timezone)),
                       term=term if term else '...',
                   )
               )
        return changes

    @property
    def _changelog_belt_changes(self) -> list[str]:
        changes = []
        for e, (belt, time) in enumerate(self._flight.bbel_id_log):
            if not (len(self._flight.bbel_id_log) != 1 and (
                    e == 0 or e == len(self._flight.bbel_id_log) - 1) and belt is None):
                changes.append(
                    '  <i>{time}</i>    <b>{belt}</b>'.format(
                        time=formatters.ftime(time.astimezone(self._flight.local_mar.city.timezone)),
                        belt=belt if belt else '...',
                    )
                )
        return changes


class FlightDepartureTemplate(FlightTemplate):
    def get_message(self) -> str:
        lines = [
            self._message_flight_num_line + '\n',
            self._message_destination_line,
            self._message_status_line + '\n' if self._message_status_line else None,
            self._message_terminal_line,
            self._message_gate_line,
            self._message_checkin_desk_line,
            self._message_checkin_status_line + '\n',
            self._message_aircraft_line,
            self._message_otpr_line,
            self._message_local_airport_line,
            self._message_other_airport_line + '\n',
            ]

        if self._changelog:
            lines.extend(self._message_changelog_lines)

        content = '\n'.join(line for line in lines if line is not None).strip()
        return content

    @property
    def _message_flight_num_line(self) -> str:
        line = '<b>{direction}  <u>{iata}{number} {date} </u></b>'.format(
            direction=EMOJI.airplane_departure,
            iata=self._flight.company.iata,
            number=self._flight.number,
            date=formatters.fdate(self._flight.date),
        )
        return line

    @property
    def _message_destination_line(self) -> str:
        line = '<b>{time} {city} <i>{iata}</i></b>{delayed}'.format(
            time=formatters.ftime(self._flight.sked_local),
            city=self._flight.mar2.city.name_ru,
            iata=self._flight.mar2.iata,
            delayed=f'\n<i>Задержан до {formatters.ftime(self._flight.at_local_et)}</i>' if self._flight.is_delayed else ''
        )
        return line

    @property
    def _message_status_line(self) -> str | None:
        line = '<i>{status}</i>'.format(
            status=self._flight.status,
        ) if self._flight.status else None
        return line

    @property
    def _message_terminal_line(self) -> str:
        line = 'Терминал: <b>{term}</b>'.format(
            term=self._flight.term_local
        )
        return line

    @property
    def _message_gate_line(self) -> str:
        line = 'Выход на посадку: <b>{gate}</b>{line}{marker}{boarding}<b>{start}{end}</b>'.format(
            gate=self._flight.gate_id if self._flight.gate_id is not None else '-',
            line='\n' if self._flight.boarding_start or self._flight.boarding_end or self._flight.otpr else '',
            marker=EMOJI.time_close if self._flight.boarding_end or self._flight.otpr else (EMOJI.time_start if self._flight.boarding_start else ''),
            boarding='Посадка: ' if self._flight.boarding_start else '',
            start=formatters.ftime(self._flight.boarding_start, placeholder=''),
            end=' - ' + formatters.ftime(self._flight.boarding_end) if self._flight.boarding_end else (' - ...' if self._flight.boarding_start else ''),
        )
        return line

    @property
    def _message_checkin_desk_line(self) -> str:
        line = 'Cтойки регистрации: <b>{check_in}</b>'.format(
            check_in=self._flight.chin_id or '-',
        )
        return line

    @property
    def _message_checkin_status_line(self) -> str:
        line = '{marker} Регистрация: <b>{start} - {end}</b>'.format(
            marker=EMOJI.time_close if self._flight.chin_end else (EMOJI.time_start if self._flight.chin_start else EMOJI.time_et),
            start=formatters.ftime(self._flight.chin_start or self._flight.chin_start_et),
            end=formatters.ftime(self._flight.chin_end or self._flight.chin_end_et),
        )
        return line

    @property
    def _message_aircraft_line(self) -> str:
        line = 'Борт: <b>{aircraft}</b>'.format(
            aircraft=self._flight.aircraft.name
        )
        return line

    @property
    def _message_otpr_line(self) -> str:
        line = '{marker} Отправление: <b>{otpr}</b>'.format(
            marker=EMOJI.time_start if self._flight.otpr else EMOJI.time_et,
            otpr=formatters.ftime(self._flight.otpr) if self._flight.otpr else '-',
        )
        return line

    @property
    def _message_local_airport_line(self) -> str:
        line = '{marker} Взлёт: <b>{airport} <i>({timezone})</i> {takeoff}</b>'.format(
            marker=EMOJI.time_start if self._flight.at_local else EMOJI.time_et,
            timezone=formatters.ftimezone(self._flight.at_local or self._flight.at_local_et or self._flight.sked_local),
            takeoff=formatters.ftime(self._flight.at_local or self._flight.at_local_et or self._flight.sked_local),
            airport=self._flight.mar1.name_ru,
        )
        return line

    @property
    def _message_other_airport_line(self) -> str:
        line = '{marker} Приземление: <b>{airport} <i>({timezone})</i> {landing}</b>'.format(
            marker=EMOJI.time_start if self._flight.at_other else EMOJI.time_et,
            airport=self._flight.mar2.name_ru,
            timezone=formatters.ftimezone(self._flight.at_other or self._flight.at_other_et or self._flight.sked_other),
            landing=formatters.ftime(self._flight.at_other or self._flight.at_other_et or self._flight.sked_other),
        )
        return line

    @property
    def _message_changelog_lines(self) -> list[str]:
        changelog = [
                '<b><u>Изменения:</u></b>',
                '  <u>Терминал:</u>',
                *self._changelog_terminal_changes,
                '  <u>Выход на посадку:</u>',
                *self._changelog_gate_changes,
                '  <u>Стойки регистрации:</u>',
                *self._changelog_checkin_changes,
        ]
        return changelog

    @property
    def _changelog_terminal_changes(self) -> list[str]:
        changes = []
        for e, (term, time) in enumerate(self._flight.term_local_log):
            if not (len(self._flight.term_local_log) != 1 and (e == 0 or e == len(self._flight.term_local_log) - 1) and term is None):
                changes.append(
                    '  <i>{time}</i>    <b>{term}</b>'.format(
                        time=formatters.ftime(time.astimezone(self._flight.local_mar.city.timezone)),
                        term=term if term else '...'
                    )
                )
        return changes

    @property
    def _changelog_gate_changes(self) -> list[str]:
        changes = []
        for e, (gate, time) in enumerate(self._flight.gate_id_log):
            if not (len(self._flight.gate_id_log) != 1 and ( e == 0 or e == len(self._flight.gate_id_log) - 1) and gate is None):
                changes.append(
                    '  <i>{time}</i>    <b>{gate}</b>'.format(
                        time=formatters.ftime(time.astimezone(self._flight.local_mar.city.timezone)),
                        gate=gate if gate else '...'
                    )
                )
        return changes

    @property
    def _changelog_checkin_changes(self) -> list[str]:
        changes = []
        for e, (chin, time) in enumerate(self._flight.chin_id_log):
            if not (len(self._flight.chin_id_log) != 1 and (e == 0 or e == len(self._flight.chin_id_log) - 1) and chin is None):
                changes.append(
                    '  <i>{time}</i>    <b>{chin}</b>'.format(
                        time=formatters.ftime(time.astimezone(self._flight.local_mar.city.timezone)),
                        chin=chin if chin else '...'
                    )
                )
        return changes
