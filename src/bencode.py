# Module inspired by: https://github.com/utdemir/bencoder

import re


Data = int | bytes | list["Data"] | dict[bytes, "Data"]


def encode(data: Data) -> bytes:
    if type(data) is int:
        return b'i' + _int_to_bytes(data) + b'e'

    elif type(data) is bytes:
        return _int_to_bytes(len(data)) + b':' + data

    elif isinstance(data, list):
        return b'l' + b''.join(encode(element) for element in data) + b'e'

    elif isinstance(data, dict):
        return b'd' + b''.join(encode(key) + encode(value) for key, value in data.items()) + b'e'

    else:
        raise ValueError("Invalid bencode data")


def _int_to_bytes(num: int) -> bytes:
    return str(num).encode(encoding = "ascii")



def decode(encoded: bytes) -> Data:
    decoded, rest = _decode_partial(encoded)

    if rest:
        raise ValueError("Invalid bencode")

    return decoded


def _decode_partial(encoded: bytes) -> tuple[Data, bytes]:
    if encoded.startswith(b'i'):
        return _decode_int(encoded)

    elif _is_encoded_str(encoded):
        return _decode_str(encoded)

    elif encoded.startswith(b'l'):
        return _decode_list(encoded)

    elif encoded.startswith(b'd'):
        return _decode_dict(encoded)

    else:
        raise ValueError("Invalid bencode")


def _is_encoded_str(encoded: bytes) -> bool:
    return bool(encoded) and ord('0') <= encoded[0] <= ord('9')


def _decode_int(encoded: bytes) -> tuple[int, bytes]:
    matched = re.match(b"i(-?\\d+)e", encoded)

    if matched is None:
        raise ValueError("Invalid bencoded integer")

    return int(matched[1]), encoded[matched.end():]


def _decode_str(encoded: bytes) -> tuple[bytes, bytes]:
    matched = re.match(b"(\\d+):", encoded)

    if matched is None:
        raise ValueError("Invalid bencoded string")

    length = int(matched[1])
    begin = matched.end()
    end = begin + length

    if len(encoded) < end:
        raise ValueError("Missmatch between bencoded string length and value")

    return encoded[begin:end], encoded[end:]


def _decode_list(encoded: bytes) -> tuple[list[Data], bytes]:
    lst = []
    rest = encoded[1:]

    while rest and not rest.startswith(b'e'):
        element, rest = _decode_partial(rest)
        lst.append(element)

    if not rest:
        raise ValueError("Missing bencoded list terminator")

    return lst, rest[1:]


def _decode_dict(encoded: bytes) -> tuple[dict[bytes, Data], bytes]:
    dictionary = {}
    rest = encoded[1:]

    while rest and not rest.startswith(b'e'):
        if not _is_encoded_str(rest):
            raise ValueError("Bencoded dictionary key must be a string")

        key, rest = _decode_str(rest)

        if not rest or rest.startswith(b'e'):
            raise ValueError("Missing bencoded dictionary value")

        value, rest = _decode_partial(rest)
        dictionary[key] = value

    if not rest:
        raise ValueError("Missing bencoded dictionary terminator")

    return dictionary, rest[1:]
