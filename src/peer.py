import random
import string


def gen_id():
    # Format: -<2B client ID><4B client version>-<12B random chars>
    CLIENT = b"PY"
    VERSION = b"0001"
    CHARS = string.ascii_letters + string.digits

    return b'-' + CLIENT + VERSION + b'-' + b''.join((bytes(random.choice(CHARS), encoding = "ascii") for _ in range(12)))
