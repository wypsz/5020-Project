"""Run experiments on already materialized stream datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.common import bootstrap_pythonpath

bootstrap_pythonpath()

from seem5020.evaluation.runner import load_algorithm_configs, run_experiment_suite  # noqa: E402
from seem5020.stream.generators import dataset_from_json_rows  # noqa: E402
from seem5020.utils.io import read_json, write_csv, write_json, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run experiments over existing materialized datasets.")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to the materialized-dataset run config",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for JSONL and CSV outputs",
    )
    parser.add_argument(
        "--dataset-name",
        action="append",
        default=[],
        help="Optional exact dataset name filter; can be passed multiple times",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional dataset count limit for smoke runs")
    args = parser.parse_args()

    payload = read_json(args.config)
    dataset_root = Path(payload["dataset_root"])
    if not dataset_root.exists():
        raise FileNotFoundError(f"dataset root {dataset_root} does not exist")

    algorithm_configs = load_algorithm_configs(payload["algorithms"])
    filters = dict(payload.get("filters", {}))
    if args.dataset_name:
        filters["dataset_name"] = list(args.dataset_name)
    dataset_dirs = _select_dataset_dirs(dataset_root, filters)
    if args.limit is not None:
        dataset_dirs = dataset_dirs[: args.limit]

    all_results = []
    for dataset_dir in dataset_dirs:
        dataset = _load_dataset(dataset_dir)
        results = run_experiment_suite(
            dataset=dataset,
            algorithm_configs=algorithm_configs,
            seed=int(dataset.metadata.get("seed", payload.get("seed", 0))),
            heavy_k=int(payload.get("heavy_k", 100)),
            sample_k=int(payload.get("sample_k", 100)),
        )
        all_results.extend(results)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "results.jsonl", all_results)
    write_csv(args.output_dir / "results.csv", all_results)
    write_json(
        args.output_dir / "config_snapshot.json",
        {
            **payload,
            "selected_dataset_count": len(dataset_dirs),
            "selected_dataset_names": [path.name for path in dataset_dirs],
        },
    )


def _select_dataset_dirs(dataset_root: Path, filters: dict[str, Any]) -> list[Path]:
    selected = []
    for path in sorted(candidate for candidate in dataset_root.iterdir() if candidate.is_dir()):
        metadata_path = path / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if _matches_filters(metadata, filters):
            selected.append(path)
    return selected


def _matches_filters(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        expected_values = value if isinstance(value, list) else [value]
        if metadata.get(key) not in expected_values:
            return False
    return True


def _load_dataset(dataset_dir: Path):
    metadata = json.loads((dataset_dir / "metadata.json").read_text(encoding="utf-8"))
    rows = []
    with (dataset_dir / "stream.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return dataset_from_json_rows(name=metadata["dataset_name"], rows=rows, metadata=metadata)


if __name__ == "__main__":
    main()
