#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/5] Running synthetic epsilon-sweep experiments"
python3 -m experiments.run_materialized \
  --config experiments/configs/run_generated_synthetic_epsilon_sweep.json \
  --output-dir report/tables/epsilon_sweep_synthetic

echo "[2/5] Summarizing synthetic epsilon-sweep experiments"
python3 -m experiments.summarize_results \
  report/tables/epsilon_sweep_synthetic/results.jsonl \
  --output-csv report/tables/epsilon_sweep_synthetic/summary.csv

echo "[3/5] Running kosarak epsilon-sweep experiments"
python3 -m experiments.run_materialized \
  --config experiments/configs/run_generated_kosarak_epsilon_sweep.json \
  --output-dir report/tables/epsilon_sweep_kosarak

echo "[4/5] Summarizing kosarak epsilon-sweep experiments"
python3 -m experiments.summarize_results \
  report/tables/epsilon_sweep_kosarak/results.jsonl \
  --output-csv report/tables/epsilon_sweep_kosarak/summary.csv

echo "[5/5] Finalizing merged epsilon-sweep results"
bash scripts/finalize_epsilon_sweep_existing_datasets.sh

echo "Epsilon-sweep experiment pipeline completed."
