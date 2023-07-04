import asyncio
import struct
import logging
import hashlib
from enum import Enum
from dataclasses import dataclass

from peer import Peer
from message import Message, MessageId

@dataclass
class Piece:
    index: int
    hash: bytes
    length: int

@dataclass
class DownloadedPiece:
    piece: Piece
    data: bytes

class PeerConnection:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    is_choked: bool
    bitfield: [int]

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.is_choked = True
        self.bitfield = []

    @classmethod
    async def open_connection(cls, peer: Peer, info_hash: bytes, peer_id: bytes) -> "PeerConnection":
        reader, writer = await asyncio.open_connection(peer.ip, peer.port)
        return cls(reader, writer)

    async def handshake(self, info_hash: bytes, peer_id: bytes):
        handshake = _handshake_start(info_hash, peer_id)
        self.writer.write(handshake)
        await self.writer.drain()

        response = await self.reader.read(len(handshake))
        response_info_hash = response[28:48]

        assert response_info_hash == info_hash, f"expected to get the same bytes back from handshake: {handshake} != {response}"

    async def recv_message_unchoked(self):
        while True:
            msg = await self.recv_message()
            if msg.id == MessageId.CHOKE:
                logging.debug("chocked")
                self.is_choked = True
                await self.wait_for_unchoke()
            else:
                return msg

    async def wait_for_unchoke(self):
        while self.is_choked:
            msg = await self.recv_message()
            if msg.id == MessageId.UNCHOKE:
                logging.debug("unchocked")
                self.is_choked = False

    async def recv_message(self) -> Message:
        # Messages with length 0 are keep-alive only, and can be ignored
        length = 0
        while length == 0:
            length_encoded = await self.reader.readexactly(4)
            length = struct.unpack(">I", length_encoded)[0]
            if length == 0:
                logging.debug("[recv] keep-alive")

        message_encoded = await self.reader.readexactly(length)
        if self.reader.at_eof():
            raise EOFError()
        message = Message.from_bytes(message_encoded)
        logging.debug(f"[recv] {message}")
        return message

    async def send_message(self, message: Message):
        logging.debug(f"[send] {message}")
        encoded = message.to_bytes()
        self.writer.write(struct.pack(">I", len(encoded)))
        self.writer.write(encoded)
        await self.writer.drain()

    async def recv_bitfield(self) -> bytes:
        message = await self.recv_message()
        assert message.id == MessageId.BITFIELD, f"expected bitfield, got: {message.id}"
        self.bitfield = list(message.payload)
        return message.payload

async def peer_task(info_hash: bytes, peer_id: bytes, peer: Peer, npieces: int, piece_queue: asyncio.Queue[Piece], downloaded_queue: asyncio.Queue[DownloadedPiece]):
    logging.info(f"openning a connection to the peer {peer.ip}")
    conn = await PeerConnection.open_connection(peer, info_hash, peer_id)
    conn.bitfield = [0 for _ in range(npieces // 8)]

    logging.debug("starting handshake")
    await conn.handshake(info_hash, peer_id)
    logging.debug("handshake successfull")

    logging.debug("waiting bitfield")
    while True:
        msg = await conn.recv_message()
        match msg.id:
            case MessageId.BITFIELD:
                conn.bitfield = msg.payload
                break

            case MessageId.UNCHOKE:
                conn.is_choked = False

            case MessageId.HAVE:
                index = struct.unpack(">I", msg.payload[:4])[0]
                _bitfield_set(conn.bitfield, index)
                break

            case _:
                logging.warn(f"unexpected message id {msg.id}")

    logging.debug(f"sending unchoke and interested messages")
    await conn.send_message(Message(MessageId.UNCHOKE, bytes()))
    await conn.send_message(Message(MessageId.INTERESTED, bytes()))

    while not asyncio.current_task().cancelled():
        piece = await piece_queue.get()
        logging.debug(f"processing piece {piece}")

        if not _bitfield_contains(conn.bitfield, piece.index):
            await piece_queue.put(piece)
            continue

        try:
            logging.debug(f"downloading piece {piece.index}")
            downloaded = await download_piece(piece, conn)
            logging.debug(f"piece {piece.index} finished downloading")
            if downloaded is not None:
                await downloaded_queue.put(downloaded)
            else:
                piece_queue.put(piece)
        except Exception as e:
            logging.exception("failed to download piece")
            await piece_queue.put(piece)
            return

async def download_piece(piece: Piece, conn: PeerConnection) -> DownloadedPiece | None:
    await conn.wait_for_unchoke()
    await conn.send_message(Message.request(piece.index, 0, piece.length))

    while True:
        msg = await conn.recv_message()
        match msg.id:
            case MessageId.PIECE:
                index, begin = struct.unpack(">II", msg.payload[:8])
                assert index == piece.index
                piece_data = msg.payload[8:]
                hash = hashlib.sha1(piece_data).digest()
                if hash == piece.hash:
                    return DownloadedPiece(piece, piece_data)
                else:
                    return None

            case MessageId.HAVE:
                index = struct.unpack(">I", msg.payload[:4])[0]
                _bitfield_set(conn.bitfield, index)

            case MessageId.CHOKE:
                conn.is_choked = True

            case _:
                logging.warn(f"unexpected message with id {msg.id}")
                pass

def _bitfield_contains(bitfield: bytes, index: int) -> bool:
    byte_index = index // 8
    bit_index = 7 - index % 8
    if byte_index not in range(len(bitfield)):
        return False
    return (bitfield[byte_index] >> bit_index) & 1 != 0

def _bitfield_set(bitfield: bytes, index: int):
    byte_index = index // 8
    bit_index = 7 - index % 8
    assert byte_index in range(len(bitfield)), f"byte index not in bitfield: index is {byte_index}, but bitfield has length {len(bitfield)}"
    bitfield[byte_index] |= (1 << bit_index)

def _handshake_start(info_hash: bytes, peer_id: bytes) -> bytes:
    PROTOCOL_LENGTH = 19
    PROTOCOL_ID = b'BitTorrent protocol'
    RESERVED = bytes(8)
    return bytes([PROTOCOL_LENGTH]) + PROTOCOL_ID + RESERVED + info_hash + peer_id
