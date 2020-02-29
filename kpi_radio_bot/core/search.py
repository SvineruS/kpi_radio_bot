"""Поиск песен"""

import logging

from aiogram import types, exceptions
from aiogram.types import InlineQuery, Message

import consts
import core
from config import BOT
from consts import keyboards
from utils import music


async def search_audio(message: Message):
    await BOT.send_chat_action(message.chat.id, 'upload_audio')
    audio = await music.search(message.text)

    if not audio:
        return await BOT.send_message(message.chat.id, consts.texts.SEARCH_FAILED, reply_markup=keyboards.START)

    audio = audio[0]
    try:
        await core.users.send_audio(message.chat.id, api_audio=audio)
    except Exception as ex:
        logging.error(f'send audio: {ex} {audio["url"]}')
        logging.warning(f"pls pls add exception {type(ex)}{ex}in except")
        await BOT.send_message(message.chat.id, consts.texts.ERROR, reply_markup=keyboards.START)


async def inline_search(inline_query: InlineQuery):
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
