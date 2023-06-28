import sys
import peer
import bencode

from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        error(f"Usage is 'python {sys.argv[0]} path/to/file.torrent [path/to/output/directory/]'")


    filepath = Path(sys.argv[1])

    if not filepath.is_file():
        error(f"The path '{filepath}' does not point to a file")

    if filepath.suffix != ".torrent":
        error(f"The file '{filepath}' is not a .torrent")


    out_dir = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path('.')

    if not out_dir.is_dir():
        error(f"The path '{out_dir}' does not point to a directory")


    with filepath.open("rb") as file:
        encoded = file.read()
        decoded = bencode.decode(encoded)

        print(encoded == bencode.encode(decoded))


def error(message: str, code = 1):
    print(f"ERROR: {message}")
    sys.exit(code)


if __name__ == "__main__":
    main()
