import struct
from enum import Enum
from dataclasses import dataclass

class MessageId(Enum):
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

    @classmethod
    def from_bytes(cls, encoded: int) -> "MessageId":
        match encoded:
            case MessageId.CHOKE.value:
                return MessageId.CHOKE
            case MessageId.UNCHOKE.value:
                return MessageId.UNCHOKE
            case MessageId.INTERESTED.value:
                return MessageId.INTERESTED
            case MessageId.NOT_INTERESTED.value:
                return MessageId.NOT_INTERESTED
            case MessageId.HAVE.value:
                return MessageId.HAVE
            case MessageId.BITFIELD.value:
                return MessageId.BITFIELD
            case MessageId.REQUEST.value:
                return MessageId.REQUEST
            case MessageId.PIECE.value:
                return MessageId.PIECE
            case MessageId.CANCEL.value:
                return MessageId.CANCEL
            case MessageId.REJECT.value:
                return MessageId.REJECT
            case MessageId.HASH_REQUEST.value:
                return MessageId.HASH_REQUEST
            case MessageId.HASHES.value:
                return MessageId.HASHES
            case MessageId.HASH_REJECT.value:
                return MessageId.HASH_REJECT

@dataclass
class Message:
    id: MessageId
    payload: bytes

    @classmethod
    def request(cls, index: int, begin: int, length: int) -> "Message":
        return cls(MessageId.REQUEST, struct.pack(">III", index, begin, length))

    @classmethod
    def from_bytes(cls, encoded: bytes) -> "Message":
        return cls(MessageId.from_bytes(encoded[0]), encoded[1:])

    def to_bytes(self) -> bytes:
        return bytes([self.id.value]) + self.payload

