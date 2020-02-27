import consts
import keyboards
from config import BOT
from utils import other, radioboss, broadcast, db, music


async def menu(message):
    await BOT.send_message(message.chat.id, consts.TextConstants.MENU, reply_markup=keyboards.START)


async def song_now(message):
    playback = await radioboss.get_now()
    if not broadcast.is_broadcast_right_now() or not playback:
        return await BOT.send_message(message.chat.id, consts.TextConstants.SONG_NO_NOW,
                                      reply_markup=keyboards.WHAT_PLAYING)
    await BOT.send_message(message.chat.id, consts.TextConstants.WHAT_PLAYING.format(*playback),
                           reply_markup=keyboards.WHAT_PLAYING)


async def song_next(query):
    playback = await radioboss.get_next()
    if not playback:
        return await BOT.send_message(query.message.chat.id, consts.TextConstants.SONG_NO_NEXT)
    await BOT.send_message(query.message.chat.id, other.song_format(playback[:5]))


async def timetable(message):
    text = ''
    for day_num, day_name in {0: 'Будни', 6: 'Воскресенье'}.items():
        text += f"{day_name} \n"
        for break_num, (start, stop) in consts.BROADCAST_TIMES[day_num].items():
            text += f"   {start} - {stop}   {broadcast.get_broadcast_name(break_num)} \n"

    # todo
    # text += "До ближайшего эфира ..."

    await BOT.send_message(message.chat.id, text)


async def help_change(query, key):
    try:
        await BOT.edit_message_text(consts.TextConstants.HELP[key], query.message.chat.id,
                                    query.message.message_id, reply_markup=keyboards.CHOICE_HELP)
    except:
        pass


async def notify_switch(message):
    status = await db.notification_get(message.from_user.id)
    await db.notification_set(message.from_user.id, not status)
    text = "Уведомления <b>включены</b> \n /notify - выключить" if status else \
        "Уведомления <b>выключены</b> \n /notify - включить"
    await BOT.send_message(message.chat.id, text)


async def send_audio(chat, tg_audio=None, api_audio=None):
    if tg_audio:
        file = tg_audio.file_id
        name = other.get_audio_name(tg_audio)
        duration = tg_audio.duration
    elif api_audio:
        file = music.get_download_url(api_audio['url'], api_audio['artist'], api_audio['title'])
        name = other.get_audio_name_(api_audio['artist'], api_audio['title'])
        duration = int(api_audio['duration'])
    else:
        raise Exception("шо ты мне передал блядь ебаный рот")

    bad_list = (
        (consts.TextConstants.BAD_ORDER_SHORT, duration < 60),
        (consts.TextConstants.BAD_ORDER_LONG, duration > 60 * 6),
        (consts.TextConstants.BAD_ORDER_BADWORDS, await music.is_contain_bad_words(name)),
        (consts.TextConstants.BAD_ORDER_ANIME, await music.is_anime(name)),
        (consts.TextConstants.BAD_ORDER_PERFORMER, music.is_bad_name(name)),
    )

    warnings = list(text for text, b in bad_list if b)

    if warnings:
        text = consts.TextConstants.SOMETHING_BAD_IN_ORDER.format('\n'.join(warnings))
        await BOT.send_audio(chat, file, text, reply_markup=keyboards.BAD_ORDER_BUT_OK)
    else:
        await BOT.send_audio(chat, file, consts.TextConstants.ORDER_CHOOSE_DAY,
                             reply_markup=await keyboards.choice_day())
