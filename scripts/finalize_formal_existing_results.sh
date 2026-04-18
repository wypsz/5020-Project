#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INPUT_ROOT="report/tables/formal_existing_per_dataset"
OUTPUT_DIR="report/tables/formal_existing_merged"

echo "[1/2] Merging per-dataset result directories"
python3 -m experiments.merge_result_dirs \
  --input-root "$INPUT_ROOT" \
  --output-dir "$OUTPUT_DIR"

echo "[2/2] Building grouped summary table"
python3 -m experiments.summarize_results \
  "$OUTPUT_DIR/results.jsonl" \
  --output-csv "$OUTPUT_DIR/summary.csv"

echo "Merged outputs written to $OUTPUT_DIR"
