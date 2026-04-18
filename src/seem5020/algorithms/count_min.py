"""Count-Min Sketch implementation."""

from __future__ import annotations

from typing import Hashable

from seem5020.utils.hashing import UniversalHashFamily

from .base import FrequencyEstimator


Item = Hashable


class CountMinSketch(FrequencyEstimator):
    """Standard Count-Min Sketch with configurable width and depth."""

    def __init__(self, width: int, depth: int, seed: int = 0) -> None:
        if width < 1 or depth < 1:
            raise ValueError("width and depth must both be at least 1")
        self.width = width
        self.depth = depth
        self.seed = seed
        self.hashes = UniversalHashFamily(width=width, depth=depth, seed=seed)
        self.table = [[0 for _ in range(width)] for _ in range(depth)]

    @property
    def algorithm_name(self) -> str:
        return "Count-Min Sketch"

    def update(self, item: Item, delta: int) -> None:
        if delta == 0:
            return
        for row in range(self.depth):
            column = self.hashes.bucket(row, item)
            self.table[row][column] += delta

    def query(self, item: Item) -> int:
        values = []
        for row in range(self.depth):
            column = self.hashes.bucket(row, item)
            values.append(self.table[row][column])
        return min(values) if values else 0

    def logical_size(self) -> int:
        return self.width * self.depth

    def parameters(self) -> dict[str, int]:
        return {"width": self.width, "depth": self.depth, "seed": self.seed}
