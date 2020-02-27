import logging

from aiogram import types, exceptions

import consts
import core
import keyboards
from config import BOT
from utils import music


async def search_audio(message):
    await BOT.send_chat_action(message.chat.id, 'upload_audio')
    audio = await music.search(message.text)

    if not audio:
        return await BOT.send_message(message.chat.id, consts.TextConstants.SEARCH_FAILED, reply_markup=keyboards.START)

    audio = audio[0]
    try:
        await core.users.send_audio(message.chat.id, api_audio=audio)
    except Exception as ex:
        logging.error(f'send audio: {ex} {audio["url"]}')
        await BOT.send_message(message.chat.id, consts.TextConstants.ERROR, reply_markup=keyboards.START)


async def inline_search(inline_query):
    name = inline_query.query
    audios = await music.search(name)
    if not audios:
        return await BOT.answer_inline_query(inline_query.id, [])  # todo что то писать

    articles = []
    for i in range(min(50, len(audios))):
        audio = audios[i]
        if not audio or not audio['url']:
            continue
        articles.append(types.InlineQueryResultAudio(
            id=str(hash(audio['url'])),
            audio_url=music.get_download_url(audio['url'], audio['artist'], audio['title']),
            performer=audio['artist'],
            title=audio['title']
        ))
    try:
        await BOT.answer_inline_query(inline_query.id, articles)
    except exceptions.NetworkError as ex:
        logging.warning(f"inline_search file too large {ex}")
        await BOT.answer_inline_query(inline_query.id, [])


