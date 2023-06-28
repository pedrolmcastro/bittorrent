import sys
import peer

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

    print(torrent.name)
    print(torrent.length)
    print(torrent.piece_len)
    print(torrent.info_hash)
    print(torrent.announce_list)


def error(message: str, code = 1):
    print(f"ERROR: {message}")
    sys.exit(code)


if __name__ == "__main__":
    main()
