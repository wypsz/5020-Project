"""Double Space-Saving for strict turnstile streams."""

from __future__ import annotations

from typing import Hashable

from .base import FrequencyEstimator
from .space_saving import SpaceSaving


Item = Hashable


class DoubleSpaceSaving(FrequencyEstimator):
    """Two insertion-only Space-Saving summaries for inserts and deletes."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self.positive = SpaceSaving(capacity)
        self.negative = SpaceSaving(capacity)

    @property
    def algorithm_name(self) -> str:
        return "Double-SS"

    def update(self, item: Item, delta: int) -> None:
        if delta == 0:
            return
        target = self.positive if delta > 0 else self.negative
        target.update(item, abs(delta))

    def query(self, item: Item) -> int:
        raw = self.positive.query(item) - self.negative.query(item)
        return max(raw, 0)

    def logical_size(self) -> int:
        return 2 * self.capacity

    def parameters(self) -> dict[str, int]:
        return {"capacity_per_summary": self.capacity}
