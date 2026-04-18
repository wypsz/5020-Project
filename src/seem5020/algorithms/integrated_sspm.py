"""Integrated SpaceSaving± style summary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .base import FrequencyEstimator


Item = Hashable


@dataclass(slots=True)
class _Entry:
    insertions: int
    deletions: int


class IntegratedSpaceSavingPM(FrequencyEstimator):
    """One-summary variant that tracks insert and delete counts together."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self.entries: dict[Item, _Entry] = {}
        self._min_item: Item | None = None
        self._min_insertions = 0
        self._min_dirty = True

    @property
    def algorithm_name(self) -> str:
        return "Integrated-SpaceSaving±"

    def update(self, item: Item, delta: int) -> None:
        if delta == 0:
            return
        step = 1 if delta > 0 else -1
        for _ in range(abs(delta)):
            self._update_one(item, step)

    def _update_one(self, item: Item, step: int) -> None:
        if item in self.entries:
            entry = self.entries[item]
            if step > 0:
                entry.insertions += 1
            else:
                entry.deletions += 1
            if item == self._min_item:
                self._min_dirty = True
            return

        if len(self.entries) < self.capacity:
            if step > 0:
                self.entries[item] = _Entry(insertions=1, deletions=0)
                self._min_dirty = True
            return

        if step < 0:
            return

        min_item, min_insertions = self._current_min()
        del self.entries[min_item]
        self.entries[item] = _Entry(insertions=min_insertions + 1, deletions=0)
        self._min_dirty = True

    def _current_min(self) -> tuple[Item, int]:
        if not self.entries:
            raise ValueError("summary is empty")
        if self._min_dirty or self._min_item not in self.entries:
            self._min_item, entry = min(
                self.entries.items(),
                key=lambda pair: pair[1].insertions,
            )
            self._min_insertions = entry.insertions
            self._min_dirty = False
        return self._min_item, self._min_insertions

    def min_insertions(self) -> int:
        if not self.entries:
            return 0
        _, value = self._current_min()
        return value

    def query(self, item: Item) -> int:
        entry = self.entries.get(item)
        if entry is None:
            return 0
        return entry.insertions - entry.deletions

    def logical_size(self) -> int:
        return self.capacity

    def parameters(self) -> dict[str, int]:
        return {"capacity": self.capacity}
