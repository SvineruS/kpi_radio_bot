import csv
from collections import Counter
from datetime import datetime, timedelta

from matplotlib import pyplot as plt

from config import PATH_STUFF
from consts import stats_blacklist

PATH_STATS_CSV = PATH_STUFF / 'stats.csv'
PATH_STATS_PNG = PATH_STUFF / 'stats.png'


def add(*data):
    with open(PATH_STATS_CSV, "a", newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)


def parse_stats(n_days=60):
    with open(PATH_STATS_CSV, encoding='utf-8-sig') as file:
        records = list(csv.reader(file, delimiter=','))

    date_now = datetime.today()
    stats = {}
    moderated_msgs = set()

    for r in records:
        moder = r[1]
        date = datetime.strptime(r[4][:10], "%Y-%m-%d")

        if moder == r[2]:  # свои заказы не считаем
            continue
        if (date_now - date).days >= n_days:
            continue
        if r[5] in moderated_msgs:
            continue

        if moder not in stats:
            stats[moder] = Counter()
            for i in range((date_now - date).days):  # здесь date - самая первая модерация за n_days от сегодня
                date_iter = date_now - timedelta(days=i)  # если делать date + timedelta график отзеркалится
                stats[moder][date_iter.strftime("%d.%m")] += 0  # добавить все даты от начала модерации до сегодня

        stats[moder][date.strftime("%d.%m")] += 1  # модерации по дням
        stats[moder]['all'] += 1  # всего модераций
        moderated_msgs.add(r[5])  # айдишники сообщений шоб не накручивали

    return stats


def line_plot(moder_name):
    stats = parse_stats()
    if moder_name not in stats:
        return False
    moder = stats[moder_name]
    moderation_per_day = moder.pop('all') / len(moder)

    plt.figure(figsize=(12, 10))
    plt.plot(list(moder.values()), list(moder.keys()))
    plt.savefig(PATH_STATS_PNG)
    return moderation_per_day


def bars_plot(days):
    stats = parse_stats(days)
    stats = {moder_name: moder['all'] for moder_name, moder in stats.items() if moder_name not in stats_blacklist}
    stats = dict(sorted(stats.items(), key=lambda i: i[1]))  # sort by value

    plt.figure(figsize=(12, 10))
    plt.barh(list(stats.keys()), list(stats.values()), height=0.8)
    plt.savefig(PATH_STATS_PNG)
