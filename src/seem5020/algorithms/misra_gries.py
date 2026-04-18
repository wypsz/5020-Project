"""Insertion-only Misra-Gries summary."""

from __future__ import annotations

from typing import Hashable

from .base import FrequencyEstimator


Item = Hashable


class MisraGries(FrequencyEstimator):
    """Classic Misra-Gries summary for insertion-only streams."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self.counters: dict[Item, int] = {}

    @property
    def algorithm_name(self) -> str:
        return "Misra-Gries"

    def update(self, item: Item, delta: int) -> None:
        if delta < 0:
            raise ValueError("Misra-Gries only supports insertion-only updates")
        for _ in range(delta):
            self._insert_one(item)

    def _insert_one(self, item: Item) -> None:
        if item in self.counters:
            self.counters[item] += 1
            return
        if len(self.counters) < self.capacity:
            self.counters[item] = 1
            return

        to_delete = []
        for key in self.counters:
            self.counters[key] -= 1
            if self.counters[key] == 0:
                to_delete.append(key)
        for key in to_delete:
            del self.counters[key]

    def query(self, item: Item) -> int:
        return self.counters.get(item, 0)

    def logical_size(self) -> int:
        return self.capacity

    def parameters(self) -> dict[str, int]:
        return {"capacity": self.capacity}
