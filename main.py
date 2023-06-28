import bencode


def main():
    with open("torrent/debian-10.10.0-amd64-netinst.iso.torrent", "rb") as file:
        decoded = bencode.decode(file.read())
        print(decoded[b"info"][b"name"])


if __name__ == "__main__":
    main()
