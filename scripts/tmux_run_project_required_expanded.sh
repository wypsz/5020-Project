#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SESSION_NAME="${1:-project_required_expanded}"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "tmux session '$SESSION_NAME' already exists"
  exit 1
fi

tmux new-session -d -s "$SESSION_NAME" -n "synthetic" \
  "cd '$ROOT_DIR' && python3 -m experiments.generate_datasets \
    --synthetic-config experiments/configs/synthetic_project_required_expanded.json \
    --output-dir data/generated_project_required_synthetic && \
    python3 -m experiments.run_materialized \
      --config experiments/configs/run_generated_synthetic_project_required_expanded.json \
      --output-dir report/tables/project_required_expanded_synthetic && \
    python3 -m experiments.summarize_results \
      report/tables/project_required_expanded_synthetic/results.jsonl \
      --output-csv report/tables/project_required_expanded_synthetic/summary.csv"

tmux new-window -t "$SESSION_NAME" -n "kosarak" \
  "cd '$ROOT_DIR' && python3 -m experiments.generate_kosarak \
    --config experiments/configs/real_kosarak_project_required_expanded.json \
    --output-dir data/generated_project_required_kosarak && \
    python3 -m experiments.run_materialized \
      --config experiments/configs/run_generated_kosarak_project_required_expanded.json \
      --output-dir report/tables/project_required_expanded_kosarak && \
    python3 -m experiments.summarize_results \
      report/tables/project_required_expanded_kosarak/results.jsonl \
      --output-csv report/tables/project_required_expanded_kosarak/summary.csv"

tmux new-window -t "$SESSION_NAME" -n "merge" \
  "cd '$ROOT_DIR' && bash"

echo "Started tmux session: $SESSION_NAME"
echo "Synthetic window runs synthetic datasets and experiments."
echo "Kosarak window runs real-data datasets and experiments."
echo "After both finish, run:"
echo "  bash scripts/finalize_project_required_expanded.sh"
