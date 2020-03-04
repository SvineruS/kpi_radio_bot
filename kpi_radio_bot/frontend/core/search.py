"""Поиск песен"""

import logging

from aiogram import types, exceptions

import consts
from backend.music import search
from frontend import core
from frontend.frontend_utils import keyboards


async def search_audio(message: types.Message):
    await message.chat.do('upload_audio')
    if not (audio := await search(message.text)):
        return await message.answer(consts.texts.SEARCH_FAILED, reply_markup=keyboards.START)

    audio = audio[0]
    try:
        await core.users.send_audio(message.chat.id, audio)
    except Exception as ex:
        logging.error(f'send audio: {ex} {audio.url}')
        logging.warning(f"pls pls add exception {type(ex)}{ex}in except")
        await message.answer(consts.texts.ERROR, reply_markup=keyboards.START)


async def inline_search(inline_query: types.InlineQuery):
    name = inline_query.query
    if not (audios := await search(name)):
        return await inline_query.answer([])

    articles = [
        types.InlineQueryResultAudio(
            id=str(audio.id),
            audio_url=audio.download_url,
            performer=audio.artist,
            title=audio.title
        )
        for audio in audios[:50]
    ]

    try:
        return await inline_query.answer(articles)
    except exceptions.NetworkError as ex:
        logging.warning(f"inline_search file too large {ex}")
        return await inline_query.answer([])
