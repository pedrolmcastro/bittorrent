import struct
from enum import Enum
from dataclasses import dataclass


class Id(Enum):
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7
    CANCEL = 8
    REJECT = 16
    HASH_REQUEST = 21
    HASHES = 22
    HASH_REJECT = 23
    KEEP_ALIVE = None


@dataclass
class Message:
    id: Id
    payload: bytes


    @classmethod
    def request(cls, index: int, begin: int, length: int) -> "Message":
        return cls(Id.REQUEST, struct.pack(">III", index, begin, length))

    @classmethod
    def keep_alive(cls) -> "Message":
        return cls(id = Id.KEEP_ALIVE, payload = bytes())

    @classmethod
    def unchoke(cls) -> "Message":
        return cls(id = Id.UNCHOKE, payload = bytes())

    @classmethod
    def intrested(cls) -> "Message":
        return cls(id = Id.INTERESTED, payload = bytes())


    @classmethod
    def from_bytes(cls, blob: bytes) -> "Message":
        return cls(id = Id(blob[0]), payload = blob[1:])

    def to_bytes(self) -> bytes:
        return struct.pack(">IB", len(self.payload) + 1, self.id.value) + self.payload
