import bencode
import urllib.parse
import urllib.request

from peer import Peer
from torrent import Torrent
from dataclasses import dataclass


@dataclass
class Response:
    interval: int
    peers: list[Peer]


    @classmethod
    def from_bencode(cls, encoded: bytes) -> "Response":
        decoded = bencode.decode(encoded)
        assert isinstance(decoded, dict)

        interval = decoded[b"interval"]
        assert type(interval) is int

        peers = decoded[b"peers"]

        if isinstance(peers, list):
            lst = []

            for peer in peers:
                assert isinstance(peer, dict)
                assert type(peer[b"ip"]) is bytes
                assert type(peer[b"port"]) is int

                lst.append(Peer(ip = peer[b"ip"].decode(), port = peer[b"port"]))

            return cls(peers = lst, interval = interval)

        elif type(peers) is bytes and len(peers) % 6 == 0:
            lst = [Peer.from_bytes(peers[i:i + 6]) for i in range(0, len(peers), 6)]
            return cls(peers = lst, interval = interval)

        else:
            raise ValueError("Invalid bdecoded peers type")



def request(torrent: Torrent, peer_id: bytes, port: int, uploaded = 0, downloaded = 0, compact = True):
    url = _request_url(torrent, peer_id, port, uploaded, downloaded, compact)

    with urllib.request.urlopen(url) as response:
        if response.status == 200:
            return Response.from_bencode(response.read())
        else:
            raise IOError(f"Request failed with status {response.status}")


def _request_url(torrent: Torrent, peer_id: bytes, port: int, uploaded: int, downloaded: int, compact: bool):
    if port < 0 or port > 65535:
        raise ValueError("Invalid port number")

    if len(peer_id) != 20:
        raise ValueError("The peer ID must have length 20")

    if len(torrent.info_hash) != 20:
        raise ValueError("The info hash must have length 20")

    if downloaded >= torrent.length:
        raise ValueError("The downloaded ammount must be lower than the torrent length")

    if uploaded < 0 or downloaded < 0 or torrent.length < 0:
        raise ValueError("The uploaded, downloaded and torrent length amounts must not be negative")

    return torrent.announce_list[0] + '?' + urllib.parse.urlencode({
        "port": port,
        "peer_id": peer_id,
        "uploaded": uploaded,
        "compact": int(compact),
        "downloaded": downloaded,
        "info_hash": torrent.info_hash,
        "left": torrent.length - downloaded,
    })
