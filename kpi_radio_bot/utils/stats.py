import csv
from collections import Counter
from datetime import datetime

from matplotlib import pyplot as plt

from config import PATH_STUFF

PATH_STATS_CSV = PATH_STUFF / 'stats.csv'
PATH_STATS_PNG = PATH_STUFF / 'stats.png'


def add(*data):
    with open(PATH_STATS_CSV, "a", newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)


def parse_stats(n_days=None):
    with open(PATH_STATS_CSV, encoding='utf-8-sig') as file:
        records = list(csv.reader(file, delimiter=','))

    start_date = datetime.today()
    stats = {}

    for r in reversed(records):
        moder = r[1]
        if moder == r[2]:  # свои заказы не считаем
            continue
        date = datetime.strptime(r[4][:10], "%Y-%m-%d")
        if n_days and (start_date - date).days >= n_days:
            break

        if moder not in stats:
            stats[moder] = Counter()

        stats[moder][date.strftime("%d.%m")] += 1  # модерации по дням
        stats[moder]['all'] += 1  # всего модераций

    return stats


def line_plot(moder_name):
    stats = parse_stats()
    if moder_name not in stats:
        return False
    moder = stats[moder_name]
    del moder['all']  # нужны только дни: заказы

    plt.figure(figsize=(12, 10))
    plt.plot(list(moder.values()), list(moder.keys()), marker='o')
    plt.savefig(PATH_STATS_PNG, dpi=300)
    return len(moder)


def bars_plot(days):
    stats = parse_stats(days)
    stats = {moder_name: moder['all'] for moder_name, moder in stats.items()}
    stats = dict(sorted(stats.items(), key=lambda i: i[1]))  # sort by value

    plt.figure(figsize=(12, 10))
    plt.barh(list(stats.keys()), list(stats.values()), height=0.8)
    plt.savefig(PATH_STATS_PNG, dpi=300)
