import struct
import asyncio
from dataclasses import dataclass

from peer import Peer
from message import Message


@dataclass
class Connection:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter


    @classmethod
    async def open(cls, peer: Peer) -> "Connection":
        reader, writer = await asyncio.open_connection(peer.ip, peer.port)
        return cls(reader, writer)

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()


    async def __aenter__(self) -> "Connection":
        return self

    async def __aexit__(self, typ, value, traceback) -> None:
        await self.close()


    async def handshake(self, info_hash: bytes, peer_id: bytes):
        message = self._handshake_msg(info_hash, peer_id)
        self.writer.write(message)
        await self.writer.drain()

        response = await self.reader.readexactly(len(message))

        if response[:20] != message[:20]:
            raise Exception("Invalid protocol in the handshake response")

        if response[28:48] != info_hash:
            raise Exception("Invalid info hash in the handshake response")

    @staticmethod
    def _handshake_msg(info_hash: bytes, peer_id: bytes) -> bytes:
        LENGTH = 19
        RESERVED = bytes(8)
        ID = b"BitTorrent protocol"

        return struct.pack(">B", LENGTH) + ID + RESERVED + info_hash + peer_id


    async def receive(self) -> Message:
        length = struct.unpack(">I", await self.reader.readexactly(4))[0]

        if length == 0:
            return Message.keep_alive()
        else:
            message = await self.reader.readexactly(length)
            return Message.from_bytes(message)

    async def send(self, message: Message):
        self.writer.write(message.to_bytes())
        await self.writer.drain()
