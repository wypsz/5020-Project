#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/6] Generating formal synthetic datasets"
python3 -m experiments.generate_datasets \
  --synthetic-config experiments/configs/synthetic_formal_f1_1e5_non_interleaved.json \
  --output-dir data/generated_formal_synthetic

echo "[2/6] Generating formal kosarak datasets"
python3 -m experiments.generate_kosarak \
  --config experiments/configs/real_kosarak_formal_f1_1e5_non_interleaved.json \
  --output-dir data/generated_kosarak_formal

echo "[3/6] Running formal synthetic experiments"
python3 -m experiments.run_synthetic \
  --config experiments/configs/synthetic_formal_f1_1e5_non_interleaved.json \
  --output-dir report/tables/formal_synthetic_f1_1e5_non_interleaved

echo "[4/6] Summarizing synthetic results"
python3 -m experiments.summarize_results \
  report/tables/formal_synthetic_f1_1e5_non_interleaved/results.jsonl \
  --output-csv report/tables/formal_synthetic_f1_1e5_non_interleaved/summary.csv

echo "[5/6] Running formal kosarak experiments"
python3 -m experiments.run_kosarak \
  --config experiments/configs/run_kosarak_formal_f1_1e5_non_interleaved.json \
  --output-dir report/tables/formal_kosarak_f1_1e5_non_interleaved

echo "[6/6] Summarizing kosarak results"
python3 -m experiments.summarize_results \
  report/tables/formal_kosarak_f1_1e5_non_interleaved/results.jsonl \
  --output-csv report/tables/formal_kosarak_f1_1e5_non_interleaved/summary.csv

echo "Formal project pipeline completed."
