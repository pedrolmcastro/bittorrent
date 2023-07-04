import os
import sys
import asyncio
import logging
from tqdm import tqdm
from pathlib import Path

import task
import peer
import piece
import tracker
from torrents import Torrent


MAX_CONNS = 6


async def main() -> None:
    if len(sys.argv) < 2:
        error(f"Usage is 'python3.10 {sys.argv[0]} path/to/file.torrent [path/to/output/directory/]'")

    filepath = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path('.')

    if not out_dir.is_dir():
        error(f"The path '{out_dir}' does not point to a directory")


    logging.info("Parsing the .torrent")
    torrent = Torrent.from_filepath(filepath)


    peer_id = peer.gen_id()
    logging.info("Requesting tracker info")
    response = tracker.request(torrent, peer_id, 6889)


    n_pieces = len(torrent.pieces)

    logging.info(f"Downloading {n_pieces} pieces")
    pending: asyncio.Queue[piece.Piece] = asyncio.Queue(n_pieces)
    downloaded: asyncio.Queue[piece.Downloaded] = asyncio.Queue(n_pieces)

    for part in torrent.pieces:
        await pending.put(part)


    tasks = []
    for connect in response.peers[:MAX_CONNS]:
        tasks.append(asyncio.create_task(task.spawn(torrent.info_hash, n_pieces, peer_id, connect, pending, downloaded)))


    outpath = out_dir / torrent.name

    with outpath.open("wb") as out:
        for _ in tqdm(range(n_pieces)):
            result = await downloaded.get()
            out.seek(result.piece.index * torrent.piece_len, os.SEEK_SET)
            out.write(result.data)


    logging.info("Done downloading")
    for job in tasks:
        job.cancel()
    await asyncio.wait(tasks)

def error(message: str, code = 1):
    print(f"ERROR: {message}")
    sys.exit(code)


if __name__ == "__main__":
    logging.basicConfig(level = logging.INFO)
    asyncio.run(main())
