"""Exact frequency counter used as ground truth."""

from __future__ import annotations

from collections import defaultdict
from typing import Hashable


Item = Hashable


class ExactCounter:
    """Track exact frequencies and total insert/delete volumes."""

    def __init__(self) -> None:
        self.counts: dict[Item, int] = defaultdict(int)
        self.total_insertions = 0
        self.total_deletions = 0

    def update(self, item: Item, delta: int) -> None:
        if delta == 0:
            return
        if delta > 0:
            self.total_insertions += delta
        else:
            self.total_deletions += -delta

        new_value = self.counts[item] + delta
        if new_value < 0:
            raise ValueError(f"strict turnstile violation for item {item!r}")
        if new_value == 0:
            self.counts.pop(item, None)
        else:
            self.counts[item] = new_value

    def frequency(self, item: Item) -> int:
        return self.counts.get(item, 0)

    @property
    def final_f1(self) -> int:
        return sum(self.counts.values())

    def positive_items(self) -> list[Item]:
        return list(self.counts.keys())

    def snapshot(self) -> dict[Item, int]:
        return dict(self.counts)
