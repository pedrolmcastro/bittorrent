from dataclasses import dataclass


@dataclass
class Piece:
    index: int
    hash: bytes
    length: int

@dataclass
class Downloaded:
    piece: Piece
    data: bytes
