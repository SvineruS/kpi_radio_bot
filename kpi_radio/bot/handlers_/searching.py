"""Поиск песен"""

import logging
from typing import Union

from aiogram import types, exceptions

from music import search, Audio
from music import check
from consts import texts
from bot.bot_utils import keyboards
from utils import get_by


async def search_audio(message: types.Message):
    await message.chat.do('upload_audio')
    if not (audio := await search(message.text)):
        return await message.answer(texts.SEARCH_FAILED, reply_markup=keyboards.START)

    audio = audio[0]

    try:
        await sent_audio(message, audio)
    except Exception as ex:
        logging.error(f'send audio: {ex} {audio.download_url}')
        logging.warning(f"pls add exception {type(ex)}{ex} in except")
        await message.answer(texts.ERROR, reply_markup=keyboards.START)


async def inline_search(inline_query: types.InlineQuery):
    name = inline_query.query
    if not name or not (audios := await search(name)):
        return await inline_query.answer([])

    articles = [
        types.InlineQueryResultAudio(
            id=audio.id,
            audio_url=audio.download_url,
            performer=audio.artist,
            title=audio.title,
        )
        for audio in audios[:50]
    ]

    try:
        return await inline_query.answer(articles)
    except exceptions.NetworkError as ex:
        logging.warning(f"inline_search file too large {ex}")
        return await inline_query.answer([], cache_time=0)
    except exceptions.BadRequest as ex:
        logging.warning(f"inline_search error {ex}")
        return await inline_query.answer([], cache_time=0)


async def sent_audio(message: types.Message, audio: Union[types.Audio, Audio]):
    if isinstance(audio, types.Audio):  # скинутое юзером аудио (через инлайн или от другого бота)
        file = audio.file_id
        name = get_by.get_audio_name(audio)
        duration = audio.duration
    elif isinstance(audio, Audio):  # аудио найденное ботом по названию
        file = audio.download_url
        name = get_by.get_audio_name_(audio.artist, audio.title)
        duration = audio.duration
    else:
        raise Exception("шо ты мне передал блядь ебаный рот")

    bad_list = (
        (texts.BAD_ORDER_SHORT, duration < 60),
        (texts.BAD_ORDER_LONG, duration > 60 * 6),
        (texts.BAD_ORDER_BADWORDS, await check.is_contain_bad_words(name)),
        (texts.BAD_ORDER_ANIME, await check.is_anime(name)),
        (texts.BAD_ORDER_PERFORMER, check.is_bad_name(name)),
    )

    warnings = [text for text, b in bad_list if b]

    if warnings:
        text = texts.SOMETHING_BAD_IN_ORDER.format('\n'.join(warnings))
        await message.answer_audio(file, text, reply_markup=keyboards.BAD_ORDER_BUT_OK)
    else:
        await message.answer_audio(file, texts.CHOOSE_DAY, reply_markup=await keyboards.order_choose_day())
