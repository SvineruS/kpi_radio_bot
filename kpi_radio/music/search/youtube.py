from typing import List

import youtube_dl

from music.search.searcher import Searcher, AudioResult


class YouTube(Searcher):

    # telegram doesn't want download from youtube url, so inline doesn't support
    SUPPORT_INLINE = False
    URL_MATCHING = ('youtube.com', 'youtu.be')

    @classmethod
    async def search(cls, query: str) -> List[AudioResult]:

        try:
            with youtube_dl.YoutubeDL({"noplaylist": True, "quiet": True, 'format': 'bestaudio'}) as ydl:
                res = ydl.extract_info(query, download=False)
        except (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError):
            return []

        audio = next((f for f in res['formats'] if 'audio only' in f['format']))

        return [
            AudioResult(
                id=res['id'],
                url=audio['url'],
                performer=res['uploader'],
                title=res['title'],
                duration=res['duration'],

                is_url_downloadable=False,
                paste_metadata=True
            )
        ]
