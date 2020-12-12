from typing import List

from music.search.searcher import Searcher, AudioResult

import youtubeless


class YouTube(Searcher):
    @classmethod
    def is_for_me(cls, query: str) -> bool:
        return any((
            'youtube.com' in query,
            'youtu.be' in query
        ))

    @classmethod
    async def search(cls, url: str) -> List[AudioResult]:
        try:
            res = await youtubeless.search_async(url)
        except youtubeless.exceptions.MusiclessException:
            return []

        only_audio = (
            AudioResult(
                id=res.video_id,
                artist=res.author,
                title=res.title,
                url=format_.url,
                duration=res.length,
            )
            for format_ in res.formats
            if format_.audio is not None and format_.video is None
        )
        return [next(only_audio)]  # типа lazy только первое, лучшее аудио
