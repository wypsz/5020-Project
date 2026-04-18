"""Shared estimator interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Hashable

from seem5020.evaluation.memory import recursive_sizeof


Item = Hashable


class FrequencyEstimator(ABC):
    """Common interface for all stream estimators."""

    @property
    @abstractmethod
    def algorithm_name(self) -> str:
        """Return the display name of the estimator."""

    @abstractmethod
    def update(self, item: Item, delta: int) -> None:
        """Process one stream update."""

    @abstractmethod
    def query(self, item: Item) -> int:
        """Estimate the final frequency of an item."""

    @abstractmethod
    def logical_size(self) -> int:
        """Return the logical number of counters or cells."""

    def memory_usage(self) -> int:
        """Return an approximate memory footprint in bytes."""
        return recursive_sizeof(self)

    def parameters(self) -> dict[str, Any]:
        """Expose estimator parameters for experiment logs."""
        return {}
