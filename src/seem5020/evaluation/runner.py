"""Experiment runner and estimator factory."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from seem5020.algorithms import (
    CountMinSketch,
    CountSketch,
    DoubleMisraGries,
    DoubleSpaceSaving,
    IntegratedSpaceSavingPM,
)
from seem5020.algorithms.base import FrequencyEstimator
from seem5020.evaluation.exact_counter import ExactCounter
from seem5020.evaluation.metrics import evaluate_estimator
from seem5020.stream.update import StreamDataset
from seem5020.stream.validators import validate_stream


@dataclass(slots=True)
class AlgorithmConfig:
    """Serializable algorithm configuration."""

    name: str
    label: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


def build_estimator(config: AlgorithmConfig, alpha: float, seed: int) -> FrequencyEstimator:
    """Instantiate one estimator from a config object."""

    name = config.name.lower()
    params = dict(config.params)

    if name == "double_mg":
        capacity = int(params.get("capacity", _double_mg_capacity(alpha, float(params.get("epsilon", 0.01)))))
        return DoubleMisraGries(capacity=capacity)

    if name == "double_ss":
        capacity = int(params.get("capacity", _space_saving_capacity(alpha, float(params.get("epsilon", 0.01)))))
        return DoubleSpaceSaving(capacity=capacity)

    if name == "integrated_sspm":
        capacity = int(params.get("capacity", _integrated_sspm_capacity(alpha, float(params.get("epsilon", 0.01)))))
        return IntegratedSpaceSavingPM(capacity=capacity)

    if name == "count_min":
        epsilon = float(params.get("epsilon", 0.01))
        delta = float(params.get("delta", 0.01))
        width = int(params.get("width", math.ceil(math.e / epsilon)))
        depth = int(params.get("depth", max(1, math.ceil(math.log(1 / delta)))))
        return CountMinSketch(width=width, depth=depth, seed=seed)

    if name == "count_sketch":
        epsilon = float(params.get("epsilon", 0.01))
        delta = float(params.get("delta", 0.01))
        width = int(params.get("width", max(1, math.ceil(1 / (epsilon * epsilon)))))
        depth = int(params.get("depth", _odd(max(1, math.ceil(math.log(1 / delta))))))
        return CountSketch(width=width, depth=depth, seed=seed)

    raise ValueError(f"unknown algorithm: {config.name}")


def run_experiment_suite(
    dataset: StreamDataset,
    algorithm_configs: Iterable[AlgorithmConfig],
    seed: int,
    heavy_k: int = 100,
    sample_k: int = 100,
) -> list[dict[str, Any]]:
    """Run all configured algorithms on a materialized dataset."""

    truth = ExactCounter()
    for update in dataset.updates:
        truth.update(update.item, update.delta)

    expected_final_f1 = int(dataset.metadata.get("final_f1_star", truth.final_f1))
    alpha = float(dataset.metadata["alpha"])
    validation = validate_stream(dataset.updates, expected_final_f1=expected_final_f1, alpha=alpha)
    if not (validation.strict_turnstile_ok and validation.final_f1_ok and validation.alpha_ok):
        raise ValueError(f"dataset validation failed: {validation}")

    results = []
    exact_counts = truth.snapshot()
    for offset, config in enumerate(algorithm_configs):
        estimator_seed = seed + offset
        estimator = build_estimator(config, alpha=alpha, seed=estimator_seed)
        for update in dataset.updates:
            estimator.update(update.item, update.delta)

        metrics = evaluate_estimator(
            estimator=estimator,
            exact_counts=exact_counts,
            final_f1=truth.final_f1,
            seed=seed,
            heavy_k=heavy_k,
            sample_k=sample_k,
        )
        result = {
            "dataset_name": dataset.name,
            "algorithm": config.name,
            "algorithm_variant": config.label or config.name,
            "alpha": alpha,
            "final_f1_star": expected_final_f1,
            "observed_final_f1": truth.final_f1,
            "stream_length": len(dataset.updates),
            "stream_mode": dataset.metadata.get("stream_mode"),
            "family": dataset.metadata.get("family"),
            "memory_usage_bytes": estimator.memory_usage(),
            "logical_size": estimator.logical_size(),
            "estimator_seed": estimator_seed,
        }
        result.update(dataset.metadata)
        result.update({f"config_{key}": value for key, value in config.params.items()})
        result.update({f"param_{key}": value for key, value in estimator.parameters().items()})
        result.update(metrics)
        results.append(result)

    return results


def load_algorithm_configs(payload: list[dict[str, Any]]) -> list[AlgorithmConfig]:
    """Convert JSON objects into AlgorithmConfig instances."""

    return [
        AlgorithmConfig(
            name=item["name"],
            label=item.get("label"),
            params=dict(item.get("params", {})),
        )
        for item in payload
    ]


def _double_mg_capacity(alpha: float, epsilon: float) -> int:
    return max(1, math.ceil(alpha / epsilon) - 1)


def _space_saving_capacity(alpha: float, epsilon: float) -> int:
    return max(1, math.ceil(alpha / epsilon))


def _integrated_sspm_capacity(alpha: float, epsilon: float) -> int:
    return max(1, math.ceil((alpha + 1) / (2 * epsilon)))


def _odd(value: int) -> int:
    return value if value % 2 == 1 else value + 1
