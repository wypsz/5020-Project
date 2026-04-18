"""Summarize JSONL experiment outputs into grouped CSV tables."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from experiments.common import bootstrap_pythonpath

bootstrap_pythonpath()

from seem5020.utils.io import write_csv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize experiment results.")
    parser.add_argument("results_file", type=Path, help="Path to a results.jsonl file")
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("report/tables/summary.csv"),
        help="Output path for the grouped CSV",
    )
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.results_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = (
            row.get("algorithm_variant", row.get("algorithm")),
            row.get("algorithm"),
            row.get("family"),
            row.get("stream_mode"),
            row.get("alpha"),
            row.get("final_f1_star"),
        )
        grouped[key].append(row)

    summary_rows = []
    for key, bucket in grouped.items():
        algorithm_variant, algorithm, family, mode, alpha, final_f1_star = key
        summary_rows.append(
            {
                "algorithm_variant": algorithm_variant,
                "algorithm": algorithm,
                "family": family,
                "stream_mode": mode,
                "alpha": alpha,
                "final_f1_star": final_f1_star,
                "num_runs": len(bucket),
                "config_epsilon": _first(bucket, "config_epsilon"),
                "config_delta": _first(bucket, "config_delta"),
                "config_target_logical_size": _first(bucket, "config_target_logical_size"),
                "avg_norm_abs_error": _mean(bucket, "avg_norm_abs_error"),
                "avg_relative_error": _mean(bucket, "avg_relative_error"),
                "avg_memory_usage_bytes": _mean(bucket, "memory_usage_bytes"),
                "avg_logical_size": _mean(bucket, "logical_size"),
                "avg_hh_f1": _mean(bucket, "hh_f1"),
            }
        )

    summary_rows.sort(
        key=lambda row: (
            str(row["algorithm_variant"]),
            str(row["algorithm"]),
            str(row["family"]),
            str(row["stream_mode"]),
            float(row["alpha"]),
            int(row["final_f1_star"]),
        )
    )
    write_csv(args.output_csv, summary_rows)


def _mean(rows: list[dict[str, object]], key: str) -> float:
    if not rows:
        return 0.0
    values = [float(row.get(key, 0.0)) for row in rows]
    return sum(values) / len(values)


def _first(rows: list[dict[str, object]], key: str) -> object:
    for row in rows:
        if key in row:
            return row[key]
    return None


if __name__ == "__main__":
    main()
