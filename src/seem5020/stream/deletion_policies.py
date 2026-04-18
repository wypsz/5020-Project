"""Deletion policies for alpha-bounded strict turnstile streams."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from random import Random
from typing import Hashable

from .update import Update


Item = Hashable


@dataclass(slots=True)
class DeleteCountPlan:
    """Derived insertion and deletion counts for one experiment point."""

    final_f1: int
    alpha: float
    insertions: int
    deletions: int


class AliveOccurrenceMultiset:
    """Support occurrence-uniform random deletion."""

    def __init__(self) -> None:
        self.occurrences: list[Item] = []

    def add(self, item: Item) -> None:
        self.occurrences.append(item)

    def pop_random(self, rng: Random) -> Item:
        if not self.occurrences:
            raise ValueError("cannot delete from an empty alive multiset")
        index = rng.randrange(len(self.occurrences))
        item = self.occurrences[index]
        last = self.occurrences.pop()
        if index < len(self.occurrences):
            self.occurrences[index] = last
        return item

    def __len__(self) -> int:
        return len(self.occurrences)


def compute_insert_delete_plan(final_f1: int, alpha: float) -> DeleteCountPlan:
    """Compute I and D from the target final mass and alpha."""

    if final_f1 < 1:
        raise ValueError("final_f1 must be positive")
    alpha_fraction = Fraction(str(alpha))
    if alpha_fraction < 1:
        raise ValueError("alpha must be at least 1")

    deletion_budget = ((alpha_fraction - 1) * final_f1) / 2
    deletions = deletion_budget.numerator // deletion_budget.denominator
    insertions = final_f1 + deletions
    max_total = alpha_fraction * final_f1

    while insertions + deletions > max_total:
        deletions -= 1
        insertions = final_f1 + deletions

    return DeleteCountPlan(
        final_f1=final_f1,
        alpha=float(alpha_fraction),
        insertions=insertions,
        deletions=deletions,
    )


def non_interleaved_random_deletion(
    insertion_items: list[Item],
    deletion_count: int,
    rng: Random,
) -> list[Update]:
    """Append deletions after all insertions."""

    if deletion_count < 0 or deletion_count > len(insertion_items):
        raise ValueError("invalid deletion count")

    sampled_indices = rng.sample(range(len(insertion_items)), deletion_count)
    deletions = [Update(insertion_items[index], -1) for index in sampled_indices]
    insertions = [Update(item, 1) for item in insertion_items]
    return insertions + deletions


def interleaved_random_deletion(
    insertion_items: list[Item],
    deletion_count: int,
    rng: Random,
) -> list[Update]:
    """Interleave insertion and deletion operations while preserving strictness."""

    insertion_count = len(insertion_items)
    if deletion_count < 0 or deletion_count > insertion_count:
        raise ValueError("invalid deletion count")

    if insertion_count == 0:
        return []

    burn_in = min(insertion_count, max(1000, int(0.01 * insertion_count + 0.999999)))
    total_length = insertion_count + deletion_count
    remaining_slots = total_length - burn_in
    remaining_inserts = insertion_count - burn_in

    deletion_positions = set(rng.sample(range(remaining_slots), deletion_count))
    updates: list[Update] = []
    alive = AliveOccurrenceMultiset()
    insert_index = 0

    for _ in range(burn_in):
        item = insertion_items[insert_index]
        updates.append(Update(item, 1))
        alive.add(item)
        insert_index += 1

    for position in range(remaining_slots):
        if position in deletion_positions:
            item = alive.pop_random(rng)
            updates.append(Update(item, -1))
            continue

        if remaining_inserts <= 0:
            item = alive.pop_random(rng)
            updates.append(Update(item, -1))
            continue

        item = insertion_items[insert_index]
        updates.append(Update(item, 1))
        alive.add(item)
        insert_index += 1
        remaining_inserts -= 1

    return updates
