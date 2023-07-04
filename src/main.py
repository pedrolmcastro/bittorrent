import os
import sys
import peer
import tracker
import asyncio
import logging

from pathlib import Path
from torrent import Torrent
from peer_conn import peer_task, Piece
from tqdm import tqdm

CONCURRENT_CONNECTIONS = 6

async def main() -> None:
    if len(sys.argv) < 2:
        error(f"Usage is 'python {sys.argv[0]} path/to/file.torrent [path/to/output/directory/]'")


    filepath = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path('.')

    if not out_dir.is_dir():
        error(f"The path '{out_dir}' does not point to a directory")


    torrent = Torrent.from_filepath(filepath)
    peer_id = peer.gen_id()
    response = tracker.request(torrent, peer_id, 6889)
    logging.debug(f"{response}")

    piece_queue = asyncio.Queue()
    downloaded_queue = asyncio.Queue()

    n_pieces = len(torrent.pieces)

    for index, hash in enumerate(torrent.pieces):
        piece_len = torrent.piece_len
        if index == n_pieces - 1:
            piece_len = torrent.length - (n_pieces - 1) * torrent.piece_len
        piece = Piece(index, hash, piece_len)
        piece_queue.put_nowait(piece)

    logging.info(f"start downloading {n_pieces} pieces")

    tasks = []
    for p in response.peers[:CONCURRENT_CONNECTIONS]:
        task = asyncio.create_task(peer_task(torrent.info_hash, peer_id, p, n_pieces, piece_queue, downloaded_queue))
        tasks.append(task)

    with open(out_dir / torrent.name, "wb") as out:
        for _ in tqdm(range(n_pieces)):
            downloaded = await downloaded_queue.get()
            out.seek(downloaded.piece.index * torrent.piece_len, os.SEEK_SET)
            out.write(downloaded.data)

    logging.info("done downloading, cancelling tasks")
    for task in tasks:
        task.cancel()
    asyncio.wait(tasks)

def error(message: str, code = 1):
    print(f"ERROR: {message}")
    sys.exit(code)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
