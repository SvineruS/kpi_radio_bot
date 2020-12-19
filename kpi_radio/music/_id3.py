
def id3(tags):
    res = "ID3" + chr(4) + chr(0) + chr(0)
    all_length = 0
    frames = ""

    for tag, value in tags.items():
        value = chr(3) + value + chr(0)
        length = len(value.encode("utf-8"))
        all_length += length + 10
        frames += f"{tag}{_get_safe_length(length)}{chr(0) * 2}{value}"

    res += _get_safe_length(all_length)
    res += frames
    return res


def _get_safe_length(length):
    res = ""
    while length > 0:
        r = length % 128
        res += chr(r)
        length -= 128
    res = res.rjust(4, chr(0))
    return res
