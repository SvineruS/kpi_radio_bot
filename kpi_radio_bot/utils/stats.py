import csv
from collections import Counter
from datetime import datetime, timedelta
from functools import lru_cache

from matplotlib import pyplot as plt

from config import PATH_STUFF, bot, ADMINS_CHAT_ID

PATH_STATS_CSV = PATH_STUFF / 'stats.csv'
PATH_STATS_PNG = PATH_STUFF / 'stats.png'


def add(*data):
    with open(PATH_STATS_CSV, "a", newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)


def parse_stats(n_days=float('nan')):
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
        song_name, moder_id, user_id, status, date, msg_id = rec
        date = datetime.strptime(date[:10], "%Y-%m-%d")
        date_how_old = (date_now - date).days

        if date_how_old >= n_days:
            continue
        if msg_id in moderated_msgs:
            continue

        moderated_msgs.add(msg_id)

        if moder_id not in stats:
            stats[moder_id] = set_all_days(date_how_old)

        stats[moder_id]['all'][date_now.strftime("%d.%m")] += 1
        if moder_id == user_id:
            stats[moder_id]['own'][date_now.strftime("%d.%m")] += 1

    return stats


async def line_plot(moder_id):
    stats = parse_stats(60)
    if isinstance(moder_id, str):
        moder_id = await get_moder_by_username(moder_id).id
    if moder_id not in stats:
        return False
    moder = stats[moder_id]

    moderation_all, moderation_own = moder['all'], moder['own']
    moderation_not_own = {date: moderation_all[date] - moderation_own[date] for date in moderation_all}

    plt.figure(figsize=(12, 10))

    plt.plot(list(moderation_not_own.values()), list(moderation_not_own.keys()), label="Не свои заказы")
    plt.plot(list(moderation_own.values()), list(moderation_own.keys()), 'r', label="Свои заказы")

    plt.legend(loc="upper right")
    plt.savefig(PATH_STATS_PNG)

    moderation_per_day = sum(moderation_all.values()) / len(moder)
    return moderation_per_day


async def bars_plot(days):
    stats = parse_stats(days)
    moder_names = await get_moders()

    stats = [
        (moder_names[moder_id], sum(moder['all'].values()), sum(moder['own'].values()))
        for moder_id, moder in stats.items()
        # if moder_name not in STATS_BLACKLIST
    ]
    stats = tuple(sorted(stats, key=lambda i: i[1]))  # sort all by value
    names, alls, owns = zip(*stats)

    plt.figure(figsize=(12, 10))

    plt.barh(names, alls, height=0.8, label="Не свои заказы")
    plt.barh(names, owns, height=0.8, color='orange', label="Свои заказы")

    plt.legend(loc="lower right")
    plt.savefig(PATH_STATS_PNG)


async def get_moders():
    @lru_cache(maxsize=1)
    async def get_moders_(_):
        admins = await bot.get_chat_administrators(ADMINS_CHAT_ID)
        return {
            admin.id: admin
            for admin in admins
            if 'Модер' in admin.custom_title
        }

    return await get_moders_(datetime.today().day)


async def get_moder_by_username(username):
    return [moder for moder in await get_moders() if moder.username == username][0]