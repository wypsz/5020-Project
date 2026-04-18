#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/8] Generating project-required synthetic datasets"
python3 -m experiments.generate_datasets \
  --synthetic-config experiments/configs/synthetic_project_required_expanded.json \
  --output-dir data/generated_project_required_synthetic

echo "[2/8] Generating project-required kosarak datasets"
python3 -m experiments.generate_kosarak \
  --config experiments/configs/real_kosarak_project_required_expanded.json \
  --output-dir data/generated_project_required_kosarak

echo "[3/8] Running synthetic experiments"
python3 -m experiments.run_materialized \
  --config experiments/configs/run_generated_synthetic_project_required_expanded.json \
  --output-dir report/tables/project_required_expanded_synthetic

echo "[4/8] Summarizing synthetic experiments"
python3 -m experiments.summarize_results \
  report/tables/project_required_expanded_synthetic/results.jsonl \
  --output-csv report/tables/project_required_expanded_synthetic/summary.csv

echo "[5/8] Running kosarak experiments"
python3 -m experiments.run_materialized \
  --config experiments/configs/run_generated_kosarak_project_required_expanded.json \
  --output-dir report/tables/project_required_expanded_kosarak

echo "[6/8] Summarizing kosarak experiments"
python3 -m experiments.summarize_results \
  report/tables/project_required_expanded_kosarak/results.jsonl \
  --output-csv report/tables/project_required_expanded_kosarak/summary.csv

echo "[7/8] Merging synthetic and kosarak results"
mkdir -p report/tables/project_required_expanded_merged
python3 - <<'PY'
import json
from pathlib import Path
root = Path('/home/ypwang/5020-Project')
paths = [
    root / 'report/tables/project_required_expanded_synthetic/results.jsonl',
    root / 'report/tables/project_required_expanded_kosarak/results.jsonl',
]
rows = []
for path in paths:
    rows.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
out = root / 'report/tables/project_required_expanded_merged/results.jsonl'
out.write_text('\n'.join(json.dumps(row, sort_keys=True) for row in rows) + '\n', encoding='utf-8')
PY
python3 - <<'PY'
import json
from pathlib import Path
import sys
sys.path.insert(0, '/home/ypwang/5020-Project/src')
from seem5020.utils.io import write_csv, write_json
root = Path('/home/ypwang/5020-Project')
rows = [json.loads(line) for line in (root / 'report/tables/project_required_expanded_merged/results.jsonl').read_text().splitlines() if line.strip()]
write_csv(root / 'report/tables/project_required_expanded_merged/results.csv', rows)
write_json(root / 'report/tables/project_required_expanded_merged/merge_manifest.json', {
    'sources': [
        'report/tables/project_required_expanded_synthetic/results.jsonl',
        'report/tables/project_required_expanded_kosarak/results.jsonl'
    ],
    'num_rows': len(rows)
})
PY

echo "[8/8] Building merged summary"
python3 -m experiments.summarize_results \
  report/tables/project_required_expanded_merged/results.jsonl \
  --output-csv report/tables/project_required_expanded_merged/summary.csv

echo "Project-required expanded experiment pipeline completed."
