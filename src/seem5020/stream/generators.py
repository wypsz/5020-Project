"""Synthetic stream generation."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Iterable

from seem5020.utils.io import read_json
from seem5020.utils.random_seed import make_rng

from .deletion_policies import (
    compute_insert_delete_plan,
    interleaved_random_deletion,
    non_interleaved_random_deletion,
)
from .update import StreamDataset, Update


SYNTHETIC_FAMILIES = {"zipf", "uniform", "binomial"}
STREAM_MODES = {"non-interleaved", "interleaved"}


@dataclass(slots=True)
class SyntheticStreamSpec:
    """Configuration for one synthetic dataset."""

    family: str
    final_f1: int
    alpha: float
    mode: str
    seed: int
    domain_size: int = 100_000
    zipf_s: float | None = None
    binomial_n: int | None = None
    binomial_p: float | None = None
    name: str | None = None

    def resolved_name(self) -> str:
        if self.name:
            return self.name
        pieces = [
            self.family,
            f"F1_{self.final_f1}",
            f"alpha_{str(self.alpha).replace('.', 'p')}",
            self.mode.replace("-", "_"),
        ]
        if self.family == "zipf" and self.zipf_s is not None:
            pieces.append(f"s_{str(self.zipf_s).replace('.', 'p')}")
        if self.family == "binomial" and self.binomial_p is not None:
            pieces.append(f"p_{str(self.binomial_p).replace('.', 'p')}")
        return "__".join(pieces)


def generate_synthetic_stream(spec: SyntheticStreamSpec) -> StreamDataset:
    """Materialize one synthetic stream."""

    if spec.family not in SYNTHETIC_FAMILIES:
        raise ValueError(f"unsupported family: {spec.family}")
    if spec.mode not in STREAM_MODES:
        raise ValueError(f"unsupported stream mode: {spec.mode}")

    plan = compute_insert_delete_plan(spec.final_f1, spec.alpha)
    rng = make_rng(spec.seed)
    insertion_items = _generate_insertion_items(spec, plan.insertions, rng)

    if spec.mode == "non-interleaved":
        updates = non_interleaved_random_deletion(insertion_items, plan.deletions, rng)
    else:
        updates = interleaved_random_deletion(insertion_items, plan.deletions, rng)

    metadata = {
        "dataset_name": spec.resolved_name(),
        "family": spec.family,
        "final_f1_star": spec.final_f1,
        "alpha": spec.alpha,
        "domain_size": spec.domain_size,
        "stream_mode": spec.mode,
        "seed": spec.seed,
        "insertions": plan.insertions,
        "deletions": plan.deletions,
        "stream_length": len(updates),
    }
    if spec.zipf_s is not None:
        metadata["zipf_s"] = spec.zipf_s
    if spec.family == "binomial":
        metadata["binomial_n"] = spec.binomial_n if spec.binomial_n is not None else spec.domain_size - 1
        metadata["binomial_p"] = spec.binomial_p if spec.binomial_p is not None else 0.5

    return StreamDataset(name=spec.resolved_name(), updates=updates, metadata=metadata)


def dataset_to_json_rows(dataset: StreamDataset) -> Iterable[dict[str, object]]:
    """Serialize updates to JSONL rows."""

    for update in dataset.updates:
        yield {"item": update.item, "delta": update.delta}


def dataset_from_json_rows(
    name: str,
    rows: Iterable[dict[str, object]],
    metadata: dict[str, object] | None = None,
) -> StreamDataset:
    """Deserialize a stream from JSON-compatible rows."""

    updates = [Update(row["item"], int(row["delta"])) for row in rows]
    return StreamDataset(name=name, updates=updates, metadata=dict(metadata or {}))


def load_synthetic_grid(path: str | Path) -> list[SyntheticStreamSpec]:
    """Expand the synthetic grid configuration into concrete specs."""

    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("synthetic grid config must be a JSON object")

    seed = int(payload.get("seed", 0))
    domain_size = int(payload["grid"]["domain_size"])
    include_families = set(payload["grid"].get("include_families", ["uniform", "binomial", "zipf"]))
    unknown_families = include_families - SYNTHETIC_FAMILIES
    if unknown_families:
        raise ValueError(f"unsupported families in config: {sorted(unknown_families)}")
    binomial_cfg = payload["grid"].get("binomial", {})
    binomial_n = int(binomial_cfg.get("n", domain_size - 1))
    binomial_p = float(binomial_cfg.get("p", 0.5))

    specs: list[SyntheticStreamSpec] = []

    for final_f1, alpha, mode in product(
        payload["grid"]["final_f1_values"],
        payload["grid"]["alpha_values"],
        payload["grid"]["stream_modes"],
    ):
        if "uniform" in include_families:
            specs.append(
                SyntheticStreamSpec(
                    family="uniform",
                    final_f1=int(final_f1),
                    alpha=float(alpha),
                    mode=str(mode),
                    seed=seed,
                    domain_size=domain_size,
                )
            )
        if "binomial" in include_families:
            specs.append(
                SyntheticStreamSpec(
                    family="binomial",
                    final_f1=int(final_f1),
                    alpha=float(alpha),
                    mode=str(mode),
                    seed=seed,
                    domain_size=domain_size,
                    binomial_n=binomial_n,
                    binomial_p=binomial_p,
                )
            )
        if "zipf" in include_families:
            for zipf_s in payload["grid"]["zipf_s_values"]:
                specs.append(
                    SyntheticStreamSpec(
                        family="zipf",
                        final_f1=int(final_f1),
                        alpha=float(alpha),
                        mode=str(mode),
                        seed=seed,
                        domain_size=domain_size,
                        zipf_s=float(zipf_s),
                    )
                )

    return specs


def _generate_insertion_items(spec: SyntheticStreamSpec, count: int, rng) -> list[int]:
    if spec.family == "uniform":
        return [rng.randrange(spec.domain_size) for _ in range(count)]

    if spec.family == "binomial":
        n = spec.binomial_n if spec.binomial_n is not None else spec.domain_size - 1
        p = spec.binomial_p if spec.binomial_p is not None else 0.5
        return [rng.binomialvariate(n, p) for _ in range(count)]

    if spec.family == "zipf":
        if spec.zipf_s is None:
            raise ValueError("zipf_s must be provided for Zipf datasets")
        cdf = _zipf_cdf(spec.domain_size, spec.zipf_s)
        return [_sample_from_cdf(cdf, rng.random()) for _ in range(count)]

    raise ValueError(f"unsupported family: {spec.family}")


def _zipf_cdf(domain_size: int, skew: float) -> list[float]:
    weights = [1.0 / ((rank + 1) ** skew) for rank in range(domain_size)]
    total = sum(weights)
    cumulative = 0.0
    cdf: list[float] = []
    for weight in weights:
        cumulative += weight / total
        cdf.append(cumulative)
    cdf[-1] = 1.0
    return cdf


def _sample_from_cdf(cdf: list[float], draw: float) -> int:
    return bisect_left(cdf, draw)
