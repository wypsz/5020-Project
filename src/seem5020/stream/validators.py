"""Stream validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from seem5020.evaluation.exact_counter import ExactCounter

from .update import Update


@dataclass(slots=True)
class ValidationReport:
    """Validation outcome for one generated stream."""

    strict_turnstile_ok: bool
    alpha_ok: bool
    final_f1_ok: bool
    observed_final_f1: int
    total_insertions: int
    total_deletions: int
    failure_prefix: int | None
    failure_reason: str | None


def validate_stream(
    updates: Iterable[Update],
    expected_final_f1: int,
    alpha: float,
) -> ValidationReport:
    """Check prefix non-negativity and final alpha-bounded deletion property."""

    exact = ExactCounter()
    failure_prefix: int | None = None
    failure_reason: str | None = None

    for prefix, update in enumerate(updates, start=1):
        try:
            exact.update(update.item, update.delta)
        except ValueError as exc:
            failure_prefix = prefix
            failure_reason = str(exc)
            break

    observed_final_f1 = exact.final_f1
    total_insertions = exact.total_insertions
    total_deletions = exact.total_deletions
    final_f1_ok = observed_final_f1 == expected_final_f1
    alpha_ok = total_insertions + total_deletions <= alpha * expected_final_f1
    strict_turnstile_ok = failure_prefix is None

    return ValidationReport(
        strict_turnstile_ok=strict_turnstile_ok,
        alpha_ok=alpha_ok,
        final_f1_ok=final_f1_ok,
        observed_final_f1=observed_final_f1,
        total_insertions=total_insertions,
        total_deletions=total_deletions,
        failure_prefix=failure_prefix,
        failure_reason=failure_reason,
    )
