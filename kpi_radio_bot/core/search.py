import logging

from aiogram import types

import consts
import keyboards
from config import *
from utils import music


async def search_audio(message):
    await bot.send_chat_action(message.chat.id, 'upload_audio')
    audio = await music.search(message.text)

    if not audio:
        return await bot.send_message(message.chat.id, consts.TextConstants.SEARCH_FAILED, reply_markup=keyboards.start)

    audio = audio[0]
    try:
        await bot.send_audio(
            message.chat.id,
            music.get_download_url(audio['url'], audio['artist'], audio['title']),
            consts.TextConstants.ORDER_CHOOSE_DAY, reply_markup=await keyboards.choice_day()
        )
    except Exception as ex:
        logging.error(f'send audio: {ex} {audio["url"]}')
        await bot.send_message(message.chat.id, consts.TextConstants.ERROR, reply_markup=keyboards.start)


async def inline_search(inline_query):
    name = inline_query.query
    audios = await music.search(name)
    if not audios:
        return await bot.answer_inline_query(inline_query.id, [])  # todo что то писать

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
    await bot.answer_inline_query(inline_query.id, articles)