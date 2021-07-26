"""Поиск песен"""

import logging
from typing import Union

from aiogram import types, exceptions

import music
from bot.bot_utils import kb
from consts import texts
from utils import utils


async def search_audio(message: types.Message):
    await message.chat.do('upload_audio')
    if not (audios := await music.search(message.text)):
        return await message.answer(texts.SEARCH_FAILED, reply_markup=kb.START)

    audio = audios[0]

    try:
        await sent_audio(message, audio)
    except (exceptions.InvalidHTTPUrlContent, exceptions.WrongFileIdentifier) as ex:
        logging.error(f'send audio: {ex} {audio.url}')
        await message.answer(texts.ERROR, reply_markup=kb.START)
    except Exception as ex:
        logging.exception(ex)
        await message.answer(texts.ERROR, reply_markup=kb.START)


async def inline_search(inline_query: types.InlineQuery):
    name = inline_query.query
    if not name or not (audios := await music.search(name, inline=True)):
        return await inline_query.answer([])

    # noinspection PyUnboundLocalVariable
    articles = [
        types.InlineQueryResultAudio(
            id=audio.id,
            audio_url=audio.url,
            performer=audio.performer,
            title=audio.title,
            audio_duration=audio.duration
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


async def sent_audio(message: types.Message, audio: Union[types.Audio, music.AudioResult]):
    if isinstance(audio, types.Audio):  # скинутое юзером аудио (через инлайн или от другого бота)
        file = audio.file_id
    elif isinstance(audio, music.AudioResult):  # аудио найденное ботом по названию
        file = await audio.download()
    else:
        raise TypeError("шо ты мне передал блядь ебаный рот")
    name = utils.get_audio_name(audio)

    bad_list = (
        (texts.BAD_ORDER_SHORT, audio.duration < 60),
        (texts.BAD_ORDER_LONG, audio.duration > 60 * 6),
        (texts.BAD_ORDER_BADWORDS, await music.check.is_contain_bad_words(name)),
        (texts.BAD_ORDER_ANIME, await music.check.is_anime(name)),
        (texts.BAD_ORDER_PERFORMER, music.check.is_bad_name(name)),
    )

    warnings = [text for text, b in bad_list if b]

    if warnings:
        text = texts.SOMETHING_BAD_IN_ORDER.format('\n'.join(warnings))
        _args = dict(caption=text, reply_markup=kb.BAD_ORDER_BUT_OK)
    else:
        _args = dict(caption=texts.CHOOSE_DAY, reply_markup=await kb.order_choose_day())

    await message.answer_audio(file, performer=audio.performer, title=audio.title, duration=audio.duration, **_args)
