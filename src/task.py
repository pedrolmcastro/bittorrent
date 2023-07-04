import struct
import typing
import asyncio
import hashlib
import logging

import piece
import message
from peer import Peer
from connection import Connection


async def spawn(
        info_hash: bytes,
        n_pieces: int,
        peer_id: bytes,
        peer: Peer,
        pending: asyncio.Queue[piece.Piece],
        downloaded: asyncio.Queue[piece.Downloaded]
    ):
    is_choked = True
    first_msg = True
    downloading: piece.Piece | None = None
    have = [False for _ in range(n_pieces)]


    logging.debug(f"Connection to peer {peer}")
    conn = await Connection.open(peer)

    try:
        logging.debug(f"Handshaking with peer {peer}")
        await conn.handshake(info_hash, peer_id)

        await conn.send(message.Message.intrested())
        await conn.send(message.Message.unchoke())


        while not typing.cast(asyncio.Task, asyncio.current_task()).cancelled():
            msg = await conn.receive()

            match msg.id:
                case message.Id.BITFIELD:
                    if not first_msg:
                        raise Exception("Bitfield must be the first message")
                    else:
                        have = [bool((byte >> i) & 1) for byte in msg.payload for i in range(7, -1, -1)]

                case message.Id.HAVE:
                    index = struct.unpack(">I", msg.payload[:4])[0]
                    have[index] = True

                case message.Id.CHOKE:
                    is_choked = True

                case message.Id.UNCHOKE:
                    is_choked = False

                    if downloading is None and (downloading := await _start_download(pending, have, conn)) is None:
                        return

                case message.Id.PIECE:
                    if downloading is None:
                        raise Exception(f"Received unexcepected piece from peer {peer}")

                    index, begin = struct.unpack(">II", msg.payload[:8])

                    if index != downloading.index:
                        raise Exception(f"Expected piece {downloading.index} but received {index}")

                    if begin != 0:
                        raise Exception("Received an offseted piece")

                    if hashlib.sha1(msg.payload[8:]).digest() != downloading.hash:
                        raise Exception("Received piece with incompatiple hash")

                    await downloaded.put(piece.Downloaded(piece = downloading, data = msg.payload[8:]))

                    if not is_choked and (downloading := await _start_download(pending, have, conn)) is None:
                        return

                case message.Id.KEEP_ALIVE | message.Id.INTERESTED | message.Id.NOT_INTERESTED:
                    pass

                case _:
                    logging.warn(f"Unexpected message with id {msg.id}")

            first_msg = False

    except Exception as exception:
        logging.exception(exception)

        if downloading is not None:
            await pending.put(downloading)

    finally:
        await conn.close()


async def _get_piece(pending: asyncio.Queue[piece.Piece], have: list[bool]) -> piece.Piece | None:
    for _ in range(len(have)):
        piece = await pending.get()

        if have[piece.index]:
            return piece
        else:
            await pending.put(piece)

    return None


async def _start_download(pending: asyncio.Queue[piece.Piece], have: list[bool], conn: Connection) -> piece.Piece | None:
    downloading = await _get_piece(pending, have)

    if downloading is not None:
        await conn.send(message.Message.request(downloading.index, 0, downloading.length))
        return downloading
    else:
        return None
