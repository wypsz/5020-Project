"""CAIDA destination IP preprocessing and stream generation."""

from __future__ import annotations

import csv
import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO

from seem5020.utils.random_seed import make_rng

from .deletion_policies import (
    compute_insert_delete_plan,
    interleaved_random_deletion,
    non_interleaved_random_deletion,
)
from .update import StreamDataset


@dataclass(slots=True)
class CaidaStreamSpec:
    """Configuration for one CAIDA-based dataset."""

    source_path: str
    final_f1: int
    alpha: float
    mode: str
    seed: int
    destination_column: str | None = "destination_ip"
    destination_index: int | None = None
    delimiter: str | None = None
    has_header: bool = True
    name: str | None = None

    def resolved_name(self) -> str:
        if self.name:
            return self.name
        source_stem = Path(self.source_path).stem.replace(".", "_")
        return "__".join(
            [
                "caida",
                source_stem,
                f"F1_{self.final_f1}",
                f"alpha_{str(self.alpha).replace('.', 'p')}",
                self.mode.replace("-", "_"),
            ]
        )


def generate_caida_stream(spec: CaidaStreamSpec) -> StreamDataset:
    """Generate a strict turnstile stream from CAIDA destination IP occurrences."""

    plan = compute_insert_delete_plan(spec.final_f1, spec.alpha)
    base_items = load_destination_ips(
        path=spec.source_path,
        limit=plan.insertions,
        destination_column=spec.destination_column,
        destination_index=spec.destination_index,
        delimiter=spec.delimiter,
        has_header=spec.has_header,
    )
    if len(base_items) < plan.insertions:
        raise ValueError(
            f"source file does not contain enough occurrences: need {plan.insertions}, got {len(base_items)}"
        )

    rng = make_rng(spec.seed)
    if spec.mode == "non-interleaved":
        updates = non_interleaved_random_deletion(base_items, plan.deletions, rng)
    elif spec.mode == "interleaved":
        updates = interleaved_random_deletion(base_items, plan.deletions, rng)
    else:
        raise ValueError(f"unsupported stream mode: {spec.mode}")

    metadata = {
        "dataset_name": spec.resolved_name(),
        "family": "caida",
        "source_path": spec.source_path,
        "final_f1_star": spec.final_f1,
        "alpha": spec.alpha,
        "stream_mode": spec.mode,
        "seed": spec.seed,
        "insertions": plan.insertions,
        "deletions": plan.deletions,
        "stream_length": len(updates),
        "destination_column": spec.destination_column,
        "destination_index": spec.destination_index,
    }
    return StreamDataset(name=spec.resolved_name(), updates=updates, metadata=metadata)


def load_destination_ips(
    path: str | Path,
    limit: int | None,
    destination_column: str | None,
    destination_index: int | None,
    delimiter: str | None,
    has_header: bool,
) -> list[str]:
    """Load destination IP occurrences from a text, CSV, TSV, or gzipped file."""

    source = Path(path)
    with _open_text(source) as handle:
        return list(
            _iter_destination_ips(
                handle=handle,
                limit=limit,
                destination_column=destination_column,
                destination_index=destination_index,
                delimiter=delimiter,
                has_header=has_header,
            )
        )


def _iter_destination_ips(
    handle: TextIO,
    limit: int | None,
    destination_column: str | None,
    destination_index: int | None,
    delimiter: str | None,
    has_header: bool,
) -> Iterable[str]:
    sample = handle.read(2048)
    handle.seek(0)
    delimiter = delimiter or _infer_delimiter(sample)

    if has_header and destination_column:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row_number, row in enumerate(reader):
            value = row.get(destination_column)
            if value:
                yield value.strip()
            if limit is not None and row_number + 1 >= limit:
                break
        return

    reader = csv.reader(handle, delimiter=delimiter)
    if has_header:
        next(reader, None)

    index = 0 if destination_index is None else destination_index
    for row_number, row in enumerate(reader):
        if len(row) <= index:
            continue
        value = row[index].strip()
        if value:
            yield value
        if limit is not None and row_number + 1 >= limit:
            break


def _infer_delimiter(sample: str) -> str:
    if "\t" in sample:
        return "\t"
    if "," in sample:
        return ","
    return " "


def _open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("r", encoding="utf-8", newline="")
