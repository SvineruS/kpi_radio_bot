from time import time
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'Stuff/banned.db')


def ban_user(id, ban_time_min):
    ban_time = int(ban_time_min * 60 + time())
    banned = read_ban()
    banned[id] = ban_time
    write_ban(banned)
    return int(ban_time_min)


def chek_ban(id):
    banned = read_ban()
    if id not in banned:
        return False
    if banned[id] < time():
        del banned[id]
        write_ban(banned)
        return False
    return banned[id]


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
