"""Shared stream data classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Hashable


Item = Hashable


@dataclass(frozen=True, slots=True)
class Update:
    """One unit-weight stream update."""

    item: Item
    delta: int

    def __post_init__(self) -> None:
        if self.delta not in {-1, 1}:
            raise ValueError("project datasets use only unit updates: delta must be +1 or -1")


@dataclass(slots=True)
class StreamDataset:
    """A materialized stream and its metadata."""

    name: str
    updates: list[Update]
    metadata: dict[str, Any] = field(default_factory=dict)
