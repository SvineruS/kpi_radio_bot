import consts
import keyboards
from config import *
from utils import other, radioboss, broadcast, db


async def menu(message):
    await bot.send_message(message.chat.id, consts.TextConstants.MENU, reply_markup=keyboards.start)


async def song_now(message):
    playback = await radioboss.get_now()
    if not broadcast.is_broadcast_right_now() or not playback:
        return await bot.send_message(message.chat.id, consts.TextConstants.SONG_NO_NOW,
                                      reply_markup=keyboards.what_playing)
    await bot.send_message(message.chat.id, consts.TextConstants.WHAT_PLAYING.format(*playback),
                           reply_markup=keyboards.what_playing)


async def song_next(query):
    playback = await radioboss.get_next()
    if not playback:
        return await bot.send_message(query.message.chat.id, consts.TextConstants.SONG_NO_NEXT)
    await bot.send_message(query.message.chat.id, other.song_format(playback[:5]))


async def timetable(message):
    t = ''
    for day_num, day_name in {0: 'Будни', 6: 'Воскресенье'}.items():
        t += f"{day_name} \n"
        for break_num, (start, stop) in consts.broadcast_times[day_num].items():
            t += f"   {start} - {stop}   {broadcast.get_broadcast_name(break_num)} \n"

    # todo
    # t += "До ближайшего эфира ..."

    await bot.send_message(message.chat.id, t)


async def help_change(query, key):
    try:
        await bot.edit_message_text(consts.TextConstants.HELP[key], query.message.chat.id,
                                    query.message.message_id, reply_markup=keyboards.choice_help)
    except:
        pass


async def notify_switch(message):
    status = await db.notification_get(message.from_user.id)
    await db.notification_set(message.from_user.id, not status)
    text = "Уведомления <b>включены</b> \n /notify - выключить" if status else \
        "Уведомления <b>выключены</b> \n /notify - включить"
    await bot.send_message(message.chat.id, text)