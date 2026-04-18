"""Merge many per-dataset result directories into one consolidated result set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.common import bootstrap_pythonpath

bootstrap_pythonpath()

from seem5020.utils.io import write_csv, write_json, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge many result directories into one combined result file.")
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Root directory containing many subdirectories with results.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory for merged results",
    )
    args = parser.parse_args()

    result_files = sorted(args.input_root.glob("*/results.jsonl"))
    all_rows = []
    sources = []
    for result_file in result_files:
        dataset_dir = result_file.parent
        rows = _read_jsonl(result_file)
        all_rows.extend(rows)
        sources.append(
            {
                "dataset_dir": str(dataset_dir),
                "row_count": len(rows),
                "has_config_snapshot": (dataset_dir / "config_snapshot.json").exists(),
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "results.jsonl", all_rows)
    write_csv(args.output_dir / "results.csv", all_rows)
    write_json(
        args.output_dir / "merge_manifest.json",
        {
            "input_root": str(args.input_root),
            "num_result_dirs": len(result_files),
            "num_rows": len(all_rows),
            "sources": sources,
        },
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


if __name__ == "__main__":
    main()
