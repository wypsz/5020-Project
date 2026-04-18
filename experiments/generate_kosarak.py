"""Download kosarak, build strict-turnstile streams, and validate them."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from experiments.common import bootstrap_pythonpath

bootstrap_pythonpath()

from seem5020.stream.generators import dataset_to_json_rows  # noqa: E402
from seem5020.stream.deletion_policies import compute_insert_delete_plan  # noqa: E402
from seem5020.stream.kosarak import build_kosarak_grid_specs, prepare_kosarak_summary, generate_kosarak_stream  # noqa: E402
from seem5020.stream.validators import validate_stream  # noqa: E402
from seem5020.utils.io import read_json, write_json, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and generate kosarak-based stream datasets.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/real_kosarak_grid.json"),
        help="Path to the kosarak grid config",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/generated_kosarak"),
        help="Directory where generated kosarak datasets will be stored",
    )
    args = parser.parse_args()

    payload = read_json(args.config)
    specs = build_kosarak_grid_specs(payload)
    max_insertions = max(
        compute_insert_delete_plan(dataset_spec.final_f1, dataset_spec.alpha).insertions
        for dataset_spec in specs
    )
    summary = prepare_kosarak_summary(payload.get("data_home", "data/raw/skmine_data"), max_occurrences=max_insertions)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        args.output_dir / "kosarak_summary.json",
        {
            "source_path": summary.source_path,
            "transaction_count": summary.transaction_count,
            "occurrence_count": summary.occurrence_count,
            "distinct_items": summary.distinct_items,
            "average_transaction_size": summary.average_transaction_size,
            "max_prefix_occurrences_materialized": len(summary.prefix_occurrences),
        },
    )

    for spec in specs:
        dataset = generate_kosarak_stream(spec, summary=summary)
        validation = validate_stream(
            dataset.updates,
            expected_final_f1=int(dataset.metadata["final_f1_star"]),
            alpha=float(dataset.metadata["alpha"]),
        )
        dataset_dir = args.output_dir / dataset.name
        dataset_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(dataset_dir / "stream.jsonl", dataset_to_json_rows(dataset))
        metadata = dict(dataset.metadata)
        metadata["validation"] = asdict(validation)
        write_json(dataset_dir / "metadata.json", metadata)


if __name__ == "__main__":
    main()
