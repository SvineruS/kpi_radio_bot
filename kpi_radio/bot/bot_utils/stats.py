"""Запись и отображение статистики
Столбцы статистики:
- Название трека
- id модера
- id заказчика
- статус модерации
- дата модерации
- id сообщение модерации
"""

import csv
import functools
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Iterator

from matplotlib import pyplot as plt

from consts.config import PATH_STUFF
from utils.user_utils import get_moders

PATH_STATS_CSV = PATH_STUFF / 'stats.csv'
PATH_STATS_PNG = PATH_STUFF / 'stats.png'


def add(*data):
    with open(PATH_STATS_CSV, "a", newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)


def change_username_to_id(changes):  # todo remove
    with open(PATH_STATS_CSV, "r", encoding='utf-8-sig') as file:
        content = file.read()
    for username, id_ in changes.items():
        if username:
            content = content.replace(username, str(id_))
    with open(PATH_STATS_CSV, "w", encoding='utf-8-sig') as file:
        file.write(content)


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
    names, moderations_all, moderations_own = zip(*stats)
    _draw_bars_plot(names, moderations_all, moderations_own)


#


def _parse_stats(n_days: int = float('inf')) -> Dict[int, Dict[str, Counter]]:
    with open(PATH_STATS_CSV, encoding='utf-8-sig') as file:
        records = list(csv.reader(file, delimiter=','))
    # song_name, moder_id, user_id, status, date, msg_id

    date_now = datetime.today()
    stats = {}
    moderated_msgs = set()

    for rec in records:
        _song_name, moder_id, user_id, _status, date, msg_id = rec
        date = datetime.strptime(date[:10], "%Y-%m-%d")

        if (date_now - date).days >= n_days:
            continue
        if msg_id in moderated_msgs:
            continue
        if moder_id not in stats:
            stats[moder_id] = _get_counters(date)

        moderated_msgs.add(msg_id)
        stats[moder_id]['all'][date] += 1
        if moder_id == user_id:
            stats[moder_id]['own'][date] += 1

    stats = {int(moder_id): moder for moder_id, moder in stats.items() if moder_id.isdigit()}  # todo remove
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
        counter[day] = 0
    return {'all': counter, 'own': counter.copy()}


def _get_all_days_to_today(date_from: datetime) -> Iterator[datetime]:
    date_to = datetime.today()
    day_delta = timedelta(days=1)
    while date_from < date_to:
        yield date_from
        date_from += day_delta
