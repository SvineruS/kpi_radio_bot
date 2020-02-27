import csv
from collections import Counter
from datetime import datetime, timedelta

from matplotlib import pyplot as plt

from config import PATH_STUFF
from utils.user_utils import get_admins

PATH_STATS_CSV = PATH_STUFF / 'stats.csv'
PATH_STATS_PNG = PATH_STUFF / 'stats.png'


def add(*data):
    with open(PATH_STATS_CSV, "a", newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)


def TEMP_change_username_to_id(changes):  # todo remove
    with open(PATH_STATS_CSV, "r") as file:
        content = file.read()
    for username, id_ in changes.items():
        content = content.replace(username, str(id_))
    with open(PATH_STATS_CSV, "w") as file:
        file.write(content)


async def line_plot(moder_id):
    stats = _parse_stats(60)
    moder_id = str(moder_id)  # todo remove

    if moder_id not in stats:
        return False
    moder = stats[moder_id]

    moderation_all, moderation_own = moder['all'], moder['own']

    plt.figure(figsize=(12, 10))

    plt.plot(list(moderation_all.values()), list(moderation_all.keys()), label="Все заказы")
    plt.plot(list(moderation_own.values()), list(moderation_own.keys()), 'r', label="Свои заказы")

    plt.legend(loc="upper right")
    plt.savefig(PATH_STATS_PNG)

    moderation_per_day = sum(moderation_all.values()) / len(moder)
    return moderation_per_day


async def bars_plot(days):
    stats = _parse_stats(days)
    moders = await get_admins()

    stats = {int(moder_id): moder for moder_id, moder in stats.items() if moder_id.isdigit()}  # todo remove

    stats = [
        (
            moders[moder_id].user.first_name,
            sum(moder['all'].values()),
            sum(moder['own'].values())
        )
        for moder_id, moder in stats.items()
        if moder_id in moders and 'Модер' in moders[moder_id].custom_title
    ]
    stats = tuple(sorted(stats, key=lambda i: i[1]))  # sort by 'all' value
    names, alls, owns = zip(*stats)

    plt.figure(figsize=(12, 10))

    plt.barh(names, alls, height=0.8, label="Не свои заказы")
    plt.barh(names, owns, height=0.8, color='orange', label="Свои заказы")

    plt.legend(loc="lower right")
    plt.savefig(PATH_STATS_PNG)


def _parse_stats(n_days=float('nan')):
    def set_all_days(date_how_old_):  # добавить все даты от начала модерации до сегодня
        counter = Counter()
        for days in range(date_how_old_):
            date_iter = date_now - timedelta(days=days)
            counter[date_iter.strftime("%d.%m")] = 0
        return {
            'all': counter,
            'own': counter.copy(),
        }

    with open(PATH_STATS_CSV, encoding='utf-8-sig') as file:
        records = list(csv.reader(file, delimiter=','))
    # song_name, moder_id, user_id, status, date, msg_id

    date_now = datetime.today()
    stats = {}
    moderated_msgs = set()

    for rec in records:
        _song_name, moder_id, user_id, _status, date, msg_id = rec
        date = datetime.strptime(date[:10], "%Y-%m-%d")
        date_how_old = (date_now - date).days

        if date_how_old >= n_days:
            continue
        if msg_id in moderated_msgs:
            continue

        moderated_msgs.add(msg_id)

        if moder_id not in stats:
            stats[moder_id] = set_all_days(date_how_old)

        stats[moder_id]['all'][date.strftime("%d.%m")] += 1
        if moder_id == user_id:
            stats[moder_id]['own'][date.strftime("%d.%m")] += 1

    return stats
