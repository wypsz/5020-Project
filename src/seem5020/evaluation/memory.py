"""Memory accounting helpers."""

from __future__ import annotations

import sys
from collections import deque
from dataclasses import is_dataclass, fields
from typing import Any


def recursive_sizeof(obj: Any) -> int:
    """Approximate memory usage of nested Python objects."""

    seen: set[int] = set()
    total = 0
    queue = deque([obj])

    while queue:
        current = queue.popleft()
        ident = id(current)
        if ident in seen:
            continue
        seen.add(ident)
        total += sys.getsizeof(current)

        if isinstance(current, dict):
            for key, value in current.items():
                queue.append(key)
                queue.append(value)
            continue

        if isinstance(current, (list, tuple, set, frozenset, deque)):
            queue.extend(current)
            continue

        if is_dataclass(current):
            for field in fields(current):
                queue.append(getattr(current, field.name))
            continue

        if hasattr(current, "__dict__"):
            queue.append(vars(current))
            continue

        if hasattr(current, "__slots__"):
            for slot in current.__slots__:
                if hasattr(current, slot):
                    queue.append(getattr(current, slot))

    return total
