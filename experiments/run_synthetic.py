"""Run synthetic experiments from a grid config."""

from __future__ import annotations

import argparse
from pathlib import Path

from experiments.common import bootstrap_pythonpath

bootstrap_pythonpath()

from seem5020.evaluation.runner import load_algorithm_configs, run_experiment_suite  # noqa: E402
from seem5020.stream.generators import generate_synthetic_stream, load_synthetic_grid  # noqa: E402
from seem5020.utils.io import read_json, write_csv, write_json, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic experiments.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/synthetic_grid.json"),
        help="Path to the synthetic grid config",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("report/tables/synthetic_runs"),
        help="Directory for JSONL and CSV outputs",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional dataset limit for smoke runs")
    args = parser.parse_args()

    payload = read_json(args.config)
    algorithm_configs = load_algorithm_configs(payload["algorithms"])
    specs = load_synthetic_grid(args.config)
    if args.limit is not None:
        specs = specs[: args.limit]

    all_results = []
    for spec in specs:
        dataset = generate_synthetic_stream(spec)
        results = run_experiment_suite(
            dataset=dataset,
            algorithm_configs=algorithm_configs,
            seed=spec.seed,
            heavy_k=int(payload.get("heavy_k", 100)),
            sample_k=int(payload.get("sample_k", 100)),
        )
        all_results.extend(results)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "results.jsonl", all_results)
    write_csv(args.output_dir / "results.csv", all_results)
    write_json(args.output_dir / "config_snapshot.json", payload)


if __name__ == "__main__":
    main()
