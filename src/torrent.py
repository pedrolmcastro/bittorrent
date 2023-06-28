import bencode
import hashlib

from pathlib import Path
from dataclasses import dataclass


@dataclass
class Torrent:
    name: str
    length: int
    piece_len: int
    info_hash: bytes
    pieces: list[bytes]
    announce_list: list[str]


    @staticmethod
    def from_bencoded(encoded: bytes) -> "Torrent":
        decoded = bencode.decode(encoded)
        assert isinstance(decoded, dict)

        info = decoded[b"info"]
        assert isinstance(info, dict)

        name = info[b"name"]
        assert type(name) is bytes

        pieces = info[b"pieces"]
        assert type(pieces) is bytes and len(pieces) % 20 == 0

        assert type(info[b"length"]) is int
        assert type(info[b"piece length"]) is int

        return Torrent(
            name = name.decode(),
            length = info[b"length"],
            piece_len = info[b"piece length"],
            announce_list = _get_announce_list(decoded),
            info_hash = hashlib.sha1(bencode.encode(info)).digest(),
            pieces = [pieces[i:i + 20] for i in range(0, len(pieces), 20)],
        )

    @classmethod
    def from_filepath(cls, filepath: Path) -> "Torrent":
        if not filepath.is_file():
            raise ValueError(f"The path '{filepath}' does not point to a file")

        if filepath.suffix != ".torrent":
            raise ValueError(f"The file '{filepath}' is not a .torrent")

        with filepath.open("rb") as file:
            return cls.from_bencoded(file.read())


def _flatten(lst: list) -> list:
    flatten = []

    for element in lst:
        if isinstance(element, list):
            flatten.extend(_flatten(element))
        else:
            flatten.append(element)

    return flatten


def _get_announce_list(decoded: dict[bytes, bencode.Data]) -> list[str]:
    if b"announce-list" in decoded:
        assert isinstance(decoded[b"announce-list"], list)
        return [announce.decode() for announce in _flatten(decoded[b"announce-list"])]

    elif b"announce" in decoded:
        assert type(decoded[b"announce"]) is bytes
        return [decoded[b"announce"].decode()]

    else:
        raise ValueError("The bdecoded data does not contain 'announce-list' nor 'announce'")
