from time import time
from config import STUFF_PATH

DB_PATH = STUFF_PATH / 'banned.db'


def ban_user(user_id, ban_time_min):
    ban_time = int(ban_time_min * 60 + time())
    banned = read_ban()
    banned[user_id] = ban_time
    write_ban(banned)
    return int(ban_time_min)


def chek_ban(user_id):
    banned = read_ban()
    if user_id not in banned:
        return False
    if banned[user_id] < time():
        del banned[user_id]
        write_ban(banned)
        return False
    return banned[user_id]


def write_ban(banned):
    f = open(DB_PATH, 'w')
    banned = [str(b) + ' ' + str(banned[b]) for b in banned]
    f.write('\n'.join(banned))
    f.close()


def read_ban():
    try:
        f = open(DB_PATH, 'r')
    except:
        write_ban({})
        return {}
    banned = {}
    for b in f.readlines():
        b = b.split(' ')
        banned[int(b[0])] = int(b[1])
    f.close()
    return banned


# todo переделайте это ну ебта
