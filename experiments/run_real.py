"""Run CAIDA-based experiments."""

from __future__ import annotations

import argparse
from pathlib import Path

from experiments.common import bootstrap_pythonpath

bootstrap_pythonpath()

from seem5020.evaluation.runner import load_algorithm_configs, run_experiment_suite  # noqa: E402
from seem5020.stream.caida import CaidaStreamSpec, generate_caida_stream  # noqa: E402
from seem5020.utils.io import read_json, write_csv, write_json, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CAIDA destination-IP experiments.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/real_caida_template.json"),
        help="Path to the CAIDA experiment config",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("report/tables/real_runs"),
        help="Directory for JSONL and CSV outputs",
    )
    args = parser.parse_args()

    payload = read_json(args.config)
    spec = CaidaStreamSpec(
        source_path=payload["source_path"],
        final_f1=int(payload["final_f1"]),
        alpha=float(payload["alpha"]),
        mode=payload["mode"],
        seed=int(payload.get("seed", 0)),
        destination_column=payload.get("destination_column"),
        destination_index=payload.get("destination_index"),
        delimiter=payload.get("delimiter"),
        has_header=bool(payload.get("has_header", True)),
        name=payload.get("name"),
    )
    dataset = generate_caida_stream(spec)
    algorithm_configs = load_algorithm_configs(payload["algorithms"])
    results = run_experiment_suite(
        dataset=dataset,
        algorithm_configs=algorithm_configs,
        seed=spec.seed,
        heavy_k=int(payload.get("heavy_k", 100)),
        sample_k=int(payload.get("sample_k", 100)),
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "results.jsonl", results)
    write_csv(args.output_dir / "results.csv", results)
    write_json(args.output_dir / "config_snapshot.json", payload)


if __name__ == "__main__":
    main()
