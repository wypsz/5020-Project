"""Insertion-only Space-Saving summary."""

from __future__ import annotations

from typing import Hashable

from .base import FrequencyEstimator


Item = Hashable


class SpaceSaving(FrequencyEstimator):
    """Classic insertion-only Space-Saving summary."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self.counters: dict[Item, int] = {}
        self._min_item: Item | None = None
        self._min_count = 0
        self._min_dirty = True

    @property
    def algorithm_name(self) -> str:
        return "Space-Saving"

    def update(self, item: Item, delta: int) -> None:
        if delta < 0:
            raise ValueError("Space-Saving only supports insertion-only updates")
        for _ in range(delta):
            self._insert_one(item)

    def _insert_one(self, item: Item) -> None:
        if item in self.counters:
            self.counters[item] += 1
            if item == self._min_item:
                self._min_dirty = True
            return

        if len(self.counters) < self.capacity:
            self.counters[item] = 1
            self._min_dirty = True
            return

        min_item, min_count = self._current_min()
        del self.counters[min_item]
        self.counters[item] = min_count + 1
        self._min_dirty = True

    def _current_min(self) -> tuple[Item, int]:
        if not self.counters:
            raise ValueError("summary is empty")
        if self._min_dirty or self._min_item not in self.counters:
            self._min_item, self._min_count = min(
                self.counters.items(),
                key=lambda pair: pair[1],
            )
            self._min_dirty = False
        return self._min_item, self._min_count

    def min_count(self) -> int:
        if not self.counters:
            return 0
        _, count = self._current_min()
        return count

    def query(self, item: Item) -> int:
        if item in self.counters:
            return self.counters[item]
        return self.min_count()

    def logical_size(self) -> int:
        return self.capacity

    def parameters(self) -> dict[str, int]:
        return {"capacity": self.capacity}
