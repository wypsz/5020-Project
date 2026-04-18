"""Stable hashing helpers for sketches."""

from __future__ import annotations

import hashlib
import ipaddress
from functools import lru_cache
from typing import Hashable


Item = Hashable
MERSENNE61 = (1 << 61) - 1


@lru_cache(maxsize=1_000_000)
def stable_item_int(item: Item) -> int:
    """Map supported items to a stable non-negative integer."""

    if isinstance(item, int):
        return item & 0x7FFFFFFFFFFFFFFF
    if isinstance(item, str):
        try:
            return int(ipaddress.ip_address(item))
        except ValueError:
            digest = hashlib.blake2b(item.encode("utf-8"), digest_size=8).digest()
            return int.from_bytes(digest, "big")

    digest = hashlib.blake2b(repr(item).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


class UniversalHashFamily:
    """Pairwise-style bucket and sign hashes backed by stable integer encoding."""

    def __init__(self, width: int, depth: int, seed: int) -> None:
        self.width = width
        self.depth = depth
        self.seed = seed
        self.a: list[int] = []
        self.b: list[int] = []
        self.sa: list[int] = []
        self.sb: list[int] = []

        state = (seed ^ 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        for _ in range(depth):
            state = _mix64(state + 0x9E3779B97F4A7C15)
            self.a.append((state % (MERSENNE61 - 1)) + 1)
            state = _mix64(state + 0x9E3779B97F4A7C15)
            self.b.append(state % MERSENNE61)
            state = _mix64(state + 0x9E3779B97F4A7C15)
            self.sa.append((state % (MERSENNE61 - 1)) + 1)
            state = _mix64(state + 0x9E3779B97F4A7C15)
            self.sb.append(state % MERSENNE61)

    def bucket(self, row: int, item: Item) -> int:
        x = stable_item_int(item) % MERSENNE61
        value = (self.a[row] * x + self.b[row]) % MERSENNE61
        return value % self.width

    def sign(self, row: int, item: Item) -> int:
        x = stable_item_int(item) % MERSENNE61
        value = (self.sa[row] * x + self.sb[row]) % MERSENNE61
        return 1 if (value & 1) == 0 else -1


def _mix64(value: int) -> int:
    value ^= value >> 30
    value = (value * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    value ^= value >> 27
    value = (value * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    value ^= value >> 31
    return value & 0xFFFFFFFFFFFFFFFF
