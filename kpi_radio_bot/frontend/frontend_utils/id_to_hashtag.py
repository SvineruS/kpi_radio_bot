_HASHTAG_CHARS = "0-9,a-z," \
                 "\u00c0-\u00d6,\u00d8-\u00f6,\u00f8-\u00ff,\u0100-\u024f," \
                 "\u1e00-\u1eff,\u0400-\u0481,\u0500-\u0527,\ua640-\ua66f," \
                 "\u0e01-\u0e31,\u1100-\u11ff,\u3130-\u3185,\uA960-\uA97d," \
                 "\uAC00-\uD7A0,\uff41-\uff5a,\uff66-\uff9f,\uffa1-\uffbc"

_HASHTAG_CHARS = ''.join(sorted(set(
    chr(ch_id).lower()
    for from_ch, to_ch in
    [
        map(ord, range_.split('-'))
        for range_ in _HASHTAG_CHARS.split(',')
    ]
    for ch_id in range(from_ch + 1, to_ch)
)))


def id_to_hashtag(id_: int) -> str:
    base = len(_HASHTAG_CHARS)
    res = ""
    while id_:
        id_, k = divmod(id_, base)
        res += _HASHTAG_CHARS[k]
    return res
