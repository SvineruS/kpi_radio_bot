from typing import List

from music.search.searcher import Searcher, AudioResult

import youtube_dl


class YouTube(Searcher):

    # telegram doesn't want download from youtube url, so inline doesn't support
    SUPPORT_INLINE = False
    URL_MATCHING = ('youtube.com', 'youtu.be')

    @classmethod
    async def search(cls, url: str) -> List[AudioResult]:

        try:
            with youtube_dl.YoutubeDL({"noplaylist": True, "quiet": True, 'format': 'bestaudio'}) as ydl:
                res = ydl.extract_info(url, download=False)
        except (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError):
            return []

        audio = next((f for f in res['formats']
                      if 'audio only' in f['format'] and f['ext'] in ('mp3', 'm4a')))

        return [
            AudioResult(
                id=res['id'],
                url=audio['url'],
                artist=res['uploader'],
                title=res['title'],
                duration=res['duration'],

                is_url_downloadable=False,
                paste_id3_tags=True
            )
        ]
