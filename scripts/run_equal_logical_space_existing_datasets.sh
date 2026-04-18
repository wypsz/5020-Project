#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/5] Running synthetic equal-logical-space experiments"
python3 -m experiments.run_materialized \
  --config experiments/configs/run_generated_synthetic_equal_logical_space.json \
  --output-dir report/tables/equal_logical_space_synthetic

echo "[2/5] Summarizing synthetic equal-logical-space experiments"
python3 -m experiments.summarize_results \
  report/tables/equal_logical_space_synthetic/results.jsonl \
  --output-csv report/tables/equal_logical_space_synthetic/summary.csv

echo "[3/5] Running kosarak equal-logical-space experiments"
python3 -m experiments.run_materialized \
  --config experiments/configs/run_generated_kosarak_equal_logical_space.json \
  --output-dir report/tables/equal_logical_space_kosarak

echo "[4/5] Summarizing kosarak equal-logical-space experiments"
python3 -m experiments.summarize_results \
  report/tables/equal_logical_space_kosarak/results.jsonl \
  --output-csv report/tables/equal_logical_space_kosarak/summary.csv

echo "[5/5] Finalizing merged equal-logical-space results"
bash scripts/finalize_equal_logical_space_existing_datasets.sh

echo "Equal-logical-space experiment pipeline completed."
