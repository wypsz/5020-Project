#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SESSION_NAME="${1:-seem5020_formal}"
BASE_OUTPUT_DIR="report/tables/formal_existing_per_dataset"

SYNTH_CONFIG="experiments/configs/run_existing_synthetic_formal_f1_1e5_non_interleaved.json"
KOSARAK_CONFIG="experiments/configs/run_existing_kosarak_formal_f1_1e5_non_interleaved.json"

SYNTH_DATASETS=(
  "binomial__F1_100000__alpha_1p5__non_interleaved__p_0p5"
  "binomial__F1_100000__alpha_2p0__non_interleaved__p_0p5"
  "binomial__F1_100000__alpha_4p0__non_interleaved__p_0p5"
  "binomial__F1_100000__alpha_8p0__non_interleaved__p_0p5"
  "uniform__F1_100000__alpha_1p5__non_interleaved"
  "uniform__F1_100000__alpha_2p0__non_interleaved"
  "uniform__F1_100000__alpha_4p0__non_interleaved"
  "uniform__F1_100000__alpha_8p0__non_interleaved"
  "zipf__F1_100000__alpha_1p5__non_interleaved__s_1p2"
  "zipf__F1_100000__alpha_2p0__non_interleaved__s_1p2"
  "zipf__F1_100000__alpha_4p0__non_interleaved__s_1p2"
  "zipf__F1_100000__alpha_8p0__non_interleaved__s_1p2"
)

KOSARAK_DATASETS=(
  "kosarak__F1_100000__alpha_1p5__non_interleaved"
  "kosarak__F1_100000__alpha_2p0__non_interleaved"
  "kosarak__F1_100000__alpha_4p0__non_interleaved"
  "kosarak__F1_100000__alpha_8p0__non_interleaved"
)

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "tmux session '$SESSION_NAME' already exists"
  exit 1
fi

tmux new-session -d -s "$SESSION_NAME" -n "orchestrator" "cd '$ROOT_DIR' && bash"
tmux set-option -t "$SESSION_NAME" remain-on-exit on

mkdir -p "$BASE_OUTPUT_DIR"

for dataset_name in "${SYNTH_DATASETS[@]}"; do
  output_dir="${BASE_OUTPUT_DIR}/${dataset_name}"
  tmux new-window -t "$SESSION_NAME" -n "${dataset_name:0:28}" \
    "cd '$ROOT_DIR' && mkdir -p '$BASE_OUTPUT_DIR' && python3 -m experiments.run_materialized \
      --config '$SYNTH_CONFIG' \
      --dataset-name '$dataset_name' \
      --output-dir '$output_dir' | tee '${output_dir}.log'"
done

for dataset_name in "${KOSARAK_DATASETS[@]}"; do
  output_dir="${BASE_OUTPUT_DIR}/${dataset_name}"
  tmux new-window -t "$SESSION_NAME" -n "${dataset_name:0:28}" \
    "cd '$ROOT_DIR' && mkdir -p '$BASE_OUTPUT_DIR' && python3 -m experiments.run_materialized \
      --config '$KOSARAK_CONFIG' \
      --dataset-name '$dataset_name' \
      --output-dir '$output_dir' | tee '${output_dir}.log'"
done

echo "Started tmux session: $SESSION_NAME"
echo "Attach with: tmux attach -t $SESSION_NAME"
