"""Metric computation for experiments."""

from __future__ import annotations

import math
from typing import Hashable, Mapping

from seem5020.algorithms.base import FrequencyEstimator
from seem5020.utils.random_seed import make_rng


Item = Hashable


def build_query_groups(
    exact_counts: Mapping[Item, int],
    seed: int,
    heavy_k: int = 100,
    sample_k: int = 100,
) -> dict[str, list[Item]]:
    """Build deterministic heavy, middle, and tail query groups."""

    items = [(item, count) for item, count in exact_counts.items() if count > 0]
    items.sort(key=lambda pair: (-pair[1], repr(pair[0])))
    support = [item for item, _ in items]

    heavy = support[: min(heavy_k, len(support))]
    if not support:
        return {"heavy": [], "middle": [], "tail": []}

    rng = make_rng(seed)
    lower = len(support) // 3
    upper = (2 * len(support)) // 3
    middle_pool = support[lower:upper]
    tail_pool = support[max(0, len(support) - max(sample_k * 5, sample_k)) :]

    middle = _sample_without_replacement(middle_pool, sample_k, rng)
    tail = _sample_without_replacement(tail_pool, sample_k, rng)
    return {"heavy": heavy, "middle": middle, "tail": tail}


def evaluate_estimator(
    estimator: FrequencyEstimator,
    exact_counts: Mapping[Item, int],
    final_f1: int,
    seed: int,
    heavy_k: int = 100,
    sample_k: int = 100,
) -> dict[str, float | int]:
    """Compute error and heavy hitter metrics for one estimator."""

    queries = build_query_groups(exact_counts, seed=seed, heavy_k=heavy_k, sample_k=sample_k)
    support_items = [item for item, count in exact_counts.items() if count > 0]
    evaluated = {}
    abs_errors = []
    norm_abs_errors = []
    relative_errors = []

    for item in support_items:
        estimate = estimator.query(item)
        truth = exact_counts[item]
        abs_error = abs(estimate - truth)
        evaluated[item] = estimate
        abs_errors.append(abs_error)
        norm_abs_errors.append(abs_error / final_f1 if final_f1 else 0.0)
        relative_errors.append(abs_error / max(truth, 1))

    metrics: dict[str, float | int] = {
        "support_size": len(support_items),
        "avg_abs_error": _safe_mean(abs_errors),
        "avg_norm_abs_error": _safe_mean(norm_abs_errors),
        "max_norm_abs_error": max(norm_abs_errors) if norm_abs_errors else 0.0,
        "avg_relative_error": _safe_mean(relative_errors),
    }

    for group_name, items in queries.items():
        group_norm_errors = []
        group_rel_errors = []
        for item in items:
            estimate = estimator.query(item)
            truth = exact_counts[item]
            abs_error = abs(estimate - truth)
            group_norm_errors.append(abs_error / final_f1 if final_f1 else 0.0)
            group_rel_errors.append(abs_error / max(truth, 1))
        metrics[f"{group_name}_query_count"] = len(items)
        metrics[f"{group_name}_avg_norm_abs_error"] = _safe_mean(group_norm_errors)
        metrics[f"{group_name}_avg_relative_error"] = _safe_mean(group_rel_errors)

    top_true = _top_k_pairs(exact_counts, heavy_k)
    top_est = _top_k_pairs(evaluated, heavy_k)
    precision, recall, f1_score = _precision_recall_f1(
        {item for item, _ in top_true},
        {item for item, _ in top_est},
    )
    metrics["hh_precision"] = precision
    metrics["hh_recall"] = recall
    metrics["hh_f1"] = f1_score

    return metrics


def _top_k_pairs(values: Mapping[Item, int], k: int) -> list[tuple[Item, int]]:
    pairs = [(item, int(value)) for item, value in values.items()]
    pairs.sort(key=lambda pair: (-pair[1], repr(pair[0])))
    return pairs[: min(k, len(pairs))]


def _precision_recall_f1(
    truth: set[Item],
    predicted: set[Item],
) -> tuple[float, float, float]:
    if not truth or not predicted:
        return 0.0, 0.0, 0.0
    overlap = len(truth & predicted)
    precision = overlap / len(predicted)
    recall = overlap / len(truth)
    if precision + recall == 0:
        return precision, recall, 0.0
    return precision, recall, 2 * precision * recall / (precision + recall)


def _sample_without_replacement(items: list[Item], k: int, rng) -> list[Item]:
    if len(items) <= k:
        return list(items)
    return rng.sample(items, k)


def _safe_mean(values: list[float | int]) -> float:
    if not values:
        return 0.0
    return math.fsum(float(value) for value in values) / len(values)
