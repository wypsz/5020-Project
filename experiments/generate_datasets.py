"""Materialize synthetic or CAIDA datasets to disk."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from experiments.common import bootstrap_pythonpath

bootstrap_pythonpath()

from seem5020.stream.caida import CaidaStreamSpec, generate_caida_stream  # noqa: E402
from seem5020.stream.generators import dataset_to_json_rows, generate_synthetic_stream, load_synthetic_grid  # noqa: E402
from seem5020.stream.validators import validate_stream  # noqa: E402
from seem5020.utils.io import read_json, write_json, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate project datasets without running experiments.")
    parser.add_argument("--synthetic-config", type=Path, help="Synthetic grid JSON config")
    parser.add_argument("--caida-config", type=Path, help="Single CAIDA dataset JSON config")
    parser.add_argument("--output-dir", type=Path, default=Path("data/generated"))
    parser.add_argument("--limit", type=int, default=None, help="Optional dataset count limit")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    if args.synthetic_config:
        for spec in load_synthetic_grid(args.synthetic_config):
            dataset = generate_synthetic_stream(spec)
            validation = validate_stream(
                dataset.updates,
                expected_final_f1=int(dataset.metadata["final_f1_star"]),
                alpha=float(dataset.metadata["alpha"]),
            )
            _write_dataset(args.output_dir, dataset, asdict(validation))
            generated += 1
            if args.limit is not None and generated >= args.limit:
                return

    if args.caida_config:
        payload = read_json(args.caida_config)
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
        validation = validate_stream(
            dataset.updates,
            expected_final_f1=int(dataset.metadata["final_f1_star"]),
            alpha=float(dataset.metadata["alpha"]),
        )
        _write_dataset(args.output_dir, dataset, asdict(validation))


def _write_dataset(output_dir: Path, dataset, validation: dict[str, object]) -> None:
    dataset_dir = output_dir / dataset.name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(dataset_dir / "stream.jsonl", dataset_to_json_rows(dataset))
    metadata = dict(dataset.metadata)
    metadata["validation"] = validation
    write_json(dataset_dir / "metadata.json", metadata)


if __name__ == "__main__":
    main()
