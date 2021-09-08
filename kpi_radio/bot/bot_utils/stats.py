"""Запись и отображение статистики
Столбцы статистики:
- Название трека
- id модера
- id заказчика
- статус модерации
- дата модерации
- id сообщение модерации
"""

import functools
from collections import Counter
from datetime import timedelta, datetime
from typing import Dict, Optional, List, Iterator

from matplotlib import pyplot as plt

from consts.config import PATH_STUFF
from utils import db, DateTime
from .small_utils import get_moders

PATH_STATS_PNG = PATH_STUFF / 'stats.png'


add = db.Stats.add


async def moder_stats(moder_id: int) -> Optional[float]:
    stats = _parse_stats(60)
    if moder_id not in stats:
        return None
    moder = stats[moder_id]

    dates = list(map(lambda date: date.strftime("%d.%m"), moder['all'].keys()))
    moderation_all = list(moder['all'].values())
    moderation_own = list(moder['own'].values())

    _draw_line_plot(dates, moderation_all, moderation_own)

    moderation_per_day = sum(moderation_all) / len(moderation_all)
    return moderation_per_day


async def all_moders_stats(days: int):
    stats = _parse_stats(days)
    moders = await get_moders()

    stats = [
        (moders[moder_id].first_name, sum(stat['all'].values()), sum(stat['own'].values()))
        for moder_id, stat in stats.items() if moder_id in moders
    ]

    stats = tuple(sorted(stats, key=lambda i: i[1]))  # sort by 'all' value
    if stats:
        names, moderations_all, moderations_own = zip(*stats)
    else:
        names, moderations_all, moderations_own = [], [], []
    _draw_bars_plot(names, moderations_all, moderations_own)


#


def _parse_stats(n_days: float = float('inf')) -> Dict[int, Dict[str, Counter]]:
    stats = {}

    for rec in db.Stats.get_last_n_days(n_days):
        if rec.moderator_id not in stats:
            stats[rec.moderator_id] = _get_counters(rec.date)

        stats[rec.moderator_id]['own'][rec.date.date()] += 1 if rec.is_own() else 0
        stats[rec.moderator_id]['all'][rec.date.date()] += 1

    return stats


def _draw(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        plt.figure(figsize=(12, 10))
        func(*args, **kwargs)
        plt.legend(loc="lower right")
        plt.savefig(PATH_STATS_PNG)

    return wrapper


@_draw
def _draw_line_plot(dates: List[str], moderation_all: List[int], moderation_own: List[int]):
    plt.plot(moderation_all, dates, label="Все заказы")
    plt.plot(moderation_own, dates, label="Свои заказы", color='red')


@_draw
def _draw_bars_plot(names: List[str], moderations_all: List[int], moderations_own: List[int]):
    plt.barh(names, moderations_all, height=0.8, label="Не свои заказы")
    plt.barh(names, moderations_own, height=0.8, label="Свои заказы", color='orange')


def _get_counters(start_date):
    counter = Counter()
    for day in _get_all_days_to_today(start_date):
        counter[day.date()] = 0
    return {'all': counter, 'own': counter.copy()}


def _get_all_days_to_today(date_from: datetime) -> Iterator[datetime]:
    date_to = DateTime.today()
    day_delta = timedelta(days=1)
    while date_from < date_to:
        yield date_from
        date_from += day_delta
