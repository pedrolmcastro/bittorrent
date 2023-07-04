import bencode
import hashlib

from piece import Piece
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Torrent:
    name: str
    length: int
    piece_len: int
    info_hash: bytes
    pieces: list[Piece]
    announce_list: list[str]


    @classmethod
    def from_bencoded(cls, encoded: bytes) -> "Torrent":
        decoded = bencode.decode(encoded)
        assert isinstance(decoded, dict)

        info = decoded[b"info"]
        assert isinstance(info, dict)

        name = info[b"name"]
        assert type(name) is bytes

        length = info[b"length"]
        assert type(length) is int

        piece_len = info[b"piece length"]
        assert type(piece_len) is int

        pieces = info[b"pieces"]
        assert type(pieces) is bytes


        return cls(
            length = length,
            name = name.decode(),
            piece_len = piece_len,
            announce_list = _announce_list(decoded),
            pieces = _pieces(pieces, piece_len, length),
            info_hash = hashlib.sha1(bencode.encode(info)).digest(),
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


def _announce_list(decoded: dict[bytes, bencode.Data]) -> list[str]:
    if b"announce-list" in decoded:
        assert isinstance(decoded[b"announce-list"], list)
        return [announce.decode() for announce in _flatten(decoded[b"announce-list"])]

    elif b"announce" in decoded:
        assert type(decoded[b"announce"]) is bytes
        return [decoded[b"announce"].decode()]

    else:
        raise ValueError("The bdecoded data does not contain 'announce-list' nor 'announce'")


def _pieces(blob: bytes, piece_len: int, total_len: int) -> list[Piece]:
    if len(blob) % 20 != 0:
        raise ValueError("The pices info blob must have a multiple of 20 length")

    pieces = [Piece(index = i // 20, hash = blob[i:i + 20], length = piece_len) for i in range(0, len(blob), 20)]
    pieces[-1].length = total_len - (len(pieces) - 1) * piece_len

    return pieces
