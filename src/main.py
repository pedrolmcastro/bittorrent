import sys
import peer
import tracker

from pathlib import Path
from torrent import Torrent


def main() -> None:
    if len(sys.argv) < 2:
        error(f"Usage is 'python {sys.argv[0]} path/to/file.torrent [path/to/output/directory/]'")


    filepath = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path('.')

    if not out_dir.is_dir():
        error(f"The path '{out_dir}' does not point to a directory")


    torrent = Torrent.from_filepath(filepath)
    print(tracker.request(torrent, peer.gen_id(), 6889))


def error(message: str, code = 1):
    print(f"ERROR: {message}")
    sys.exit(code)


if __name__ == "__main__":
    main()
