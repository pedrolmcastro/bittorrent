import random
import socket
import string
import struct

from dataclasses import dataclass


@dataclass
class Peer:
    ip: str
    port: int


    @classmethod
    def from_bytes(cls, blob: bytes) -> "Peer":
        if len(blob) != 6:
            raise ValueError("The peer blob must have length 6")

        return cls(ip = socket.inet_ntoa(blob[:4]), port = struct.unpack(">H", blob[4:])[0])


    def __str__(self) -> str:
        return f"{self.ip}:{self.port}"


def gen_id():
    # From: https://markuseliasson.se/article/bittorrent-in-python/
    CLIENT = b"PY"
    VERSION = b"0001"
    CHARS = string.ascii_letters + string.digits

    return b'-' + CLIENT + VERSION + b'-' + b''.join((bytes(random.choice(CHARS), encoding = "ascii") for _ in range(12)))
