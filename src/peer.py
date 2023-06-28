import random
import string


def gen_id():
    # From: https://markuseliasson.se/article/bittorrent-in-python/
    CLIENT = b"PY"
    VERSION = b"0001"
    CHARS = string.ascii_letters + string.digits

    return b'-' + CLIENT + VERSION + b'-' + b''.join((bytes(random.choice(CHARS), encoding = "ascii") for _ in range(12)))
