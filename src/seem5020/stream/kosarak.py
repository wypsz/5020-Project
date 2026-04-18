"""Kosarak dataset download, preprocessing, and stream generation."""

from __future__ import annotations

import itertools
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from seem5020.utils.random_seed import make_rng

from .deletion_policies import (
    compute_insert_delete_plan,
    interleaved_random_deletion,
    non_interleaved_random_deletion,
)
from .update import StreamDataset


KOSARAK_FILENAME = "kosarak.dat"
KOSARAK_HTTPS_URL = "https://fimi.uantwerpen.be/data/kosarak.dat"


@dataclass(slots=True)
class KosarakSummary:
    """Basic descriptive statistics extracted from the raw kosarak file."""

    source_path: str
    transaction_count: int
    occurrence_count: int
    distinct_items: int
    average_transaction_size: float
    prefix_occurrences: list[int]


@dataclass(slots=True)
class KosarakStreamSpec:
    """Configuration for one kosarak-derived strict-turnstile stream."""

    data_home: str
    final_f1: int
    alpha: float
    mode: str
    seed: int
    name: str | None = None

    def resolved_name(self) -> str:
        if self.name:
            return self.name
        return "__".join(
            [
                "kosarak",
                f"F1_{self.final_f1}",
                f"alpha_{str(self.alpha).replace('.', 'p')}",
                self.mode.replace("-", "_"),
            ]
        )


def ensure_kosarak_downloaded(data_home: str | Path) -> Path:
    """Download kosarak.dat into the requested cache directory if needed."""

    base = Path(data_home)
    base.mkdir(parents=True, exist_ok=True)
    target = base / KOSARAK_FILENAME
    if target.exists():
        return target

    urllib.request.urlretrieve(KOSARAK_HTTPS_URL, target)
    return target


def prepare_kosarak_summary(
    data_home: str | Path,
    max_occurrences: int,
) -> KosarakSummary:
    """Download kosarak if needed and parse enough data for stream generation."""

    raw_path = ensure_kosarak_downloaded(data_home)
    universe: set[int] = set()
    prefix_occurrences: list[int] = []
    transaction_count = 0
    occurrence_count = 0

    with raw_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            transaction = [int(token) for token in stripped.split()]
            transaction_count += 1
            occurrence_count += len(transaction)
            universe.update(transaction)
            needed = max_occurrences - len(prefix_occurrences)
            if needed > 0:
                prefix_occurrences.extend(itertools.islice(transaction, needed))

    avg_size = occurrence_count / transaction_count if transaction_count else 0.0
    return KosarakSummary(
        source_path=str(raw_path),
        transaction_count=transaction_count,
        occurrence_count=occurrence_count,
        distinct_items=len(universe),
        average_transaction_size=avg_size,
        prefix_occurrences=prefix_occurrences,
    )


def generate_kosarak_stream(
    spec: KosarakStreamSpec,
    summary: KosarakSummary | None = None,
) -> StreamDataset:
    """Generate one strict-turnstile stream from kosarak occurrences."""

    plan = compute_insert_delete_plan(spec.final_f1, spec.alpha)
    summary = summary or prepare_kosarak_summary(spec.data_home, max_occurrences=plan.insertions)
    if len(summary.prefix_occurrences) < plan.insertions:
        raise ValueError(
            f"kosarak prefix too short: need {plan.insertions} occurrences, got {len(summary.prefix_occurrences)}"
        )

    insertion_items = summary.prefix_occurrences[: plan.insertions]
    rng = make_rng(spec.seed)
    if spec.mode == "non-interleaved":
        updates = non_interleaved_random_deletion(insertion_items, plan.deletions, rng)
    elif spec.mode == "interleaved":
        updates = interleaved_random_deletion(insertion_items, plan.deletions, rng)
    else:
        raise ValueError(f"unsupported stream mode: {spec.mode}")

    metadata = {
        "dataset_name": spec.resolved_name(),
        "family": "kosarak",
        "source_path": summary.source_path,
        "final_f1_star": spec.final_f1,
        "alpha": spec.alpha,
        "stream_mode": spec.mode,
        "seed": spec.seed,
        "insertions": plan.insertions,
        "deletions": plan.deletions,
        "stream_length": len(updates),
        "transaction_count": summary.transaction_count,
        "occurrence_count": summary.occurrence_count,
        "distinct_items": summary.distinct_items,
        "average_transaction_size": summary.average_transaction_size,
    }
    return StreamDataset(name=spec.resolved_name(), updates=updates, metadata=metadata)


def build_kosarak_grid_specs(payload: dict[str, object]) -> list[KosarakStreamSpec]:
    """Expand a kosarak grid config into concrete generation specs."""

    grid = payload["grid"]
    seed = int(payload.get("seed", 0))
    data_home = str(payload.get("data_home", "data/raw/skmine_data"))
    specs = []
    for final_f1 in grid["final_f1_values"]:
        for alpha in grid["alpha_values"]:
            for mode in grid["stream_modes"]:
                specs.append(
                    KosarakStreamSpec(
                        data_home=data_home,
                        final_f1=int(final_f1),
                        alpha=float(alpha),
                        mode=str(mode),
                        seed=seed,
                    )
                )
    return specs
