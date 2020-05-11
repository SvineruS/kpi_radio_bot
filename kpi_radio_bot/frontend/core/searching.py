"""Поиск песен"""

import logging
from typing import List, Union

from aiogram import types, exceptions

from backend.music import search, check, get_download_url_by_id, Audio
from consts import texts, config, BOT
from frontend.frontend_utils import keyboards
from utils import db, get_by


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

    articles = await _get_inline_results(audios[:50])

    try:
        return await inline_query.answer(articles)
    except exceptions.NetworkError as ex:
        logging.warning(f"inline_search file too large {ex}")
        return await inline_query.answer([], cache_time=0)
    except exceptions.BadRequest as ex:
        logging.warning(f"inline_search error {ex}")
        await _delete_broken_cache(articles)
        return await inline_query.answer([], cache_time=0)


async def sent_audio(message: types.Message, audio: Union[types.Audio, Audio]):
    if isinstance(audio, types.Audio):
        file = audio.file_id
        name = get_by.get_audio_name(audio)
        duration = audio.duration
    elif isinstance(audio, Audio):
        if not (file := db.audio_cache.get_one(audio.id)):
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
        msg = await message.answer_audio(file, text, reply_markup=keyboards.BAD_ORDER_BUT_OK)
    else:
        msg = await message.answer_audio(file, texts.CHOOSE_DAY, reply_markup=await keyboards.order_choose_day())

    if isinstance(audio, Audio) and file == audio.download_url:
        await db.audio_cache.update(audio.id, msg.audio.file_id)


async def inline_chosen(chosen_inline: types.ChosenInlineResult):
    if config.IS_TEST_ENV:
        return
    api_id = chosen_inline.result_id
    if await db.audio_cache.get_one(api_id):
        return
    msg = await BOT.send_audio(config.CACHE_CHAT_ID, get_download_url_by_id(api_id))
    tg_id = msg.audio.file_id
    await db.audio_cache.update(api_id, tg_id)


#


async def _get_inline_results(audios: List[Audio]) -> List[types.InlineQueryResult]:
    ids = [audio.id for audio in audios]
    cache = await db.audio_cache.get(ids)
    audios = sorted(audios, key=lambda audio: audio.id in cache, reverse=True)  # cached first
    return [
        _get_inline_result(audio, cache.get(audio.id, None))
        for audio in audios
    ]


def _get_inline_result(audio: Audio, tg_id: str = None) -> types.InlineQueryResult:
    if tg_id:
        return types.InlineQueryResultCachedAudio(
            id=audio.id,
            audio_file_id=tg_id,
        )
    return types.InlineQueryResultAudio(
        id=audio.id,
        audio_url=audio.download_url,
        performer=audio.artist,
        title=audio.title,
    )


async def _delete_broken_cache(articles: List[types.InlineQueryResult]):
    ids = [
        res.id
        for res in articles
        if isinstance(res, types.InlineQueryResultCachedAudio)
    ]
    await db.audio_cache.delete_many(ids)
