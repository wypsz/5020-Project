#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p report/tables/epsilon_sweep_merged

echo "[1/2] Merging epsilon-sweep synthetic and kosarak results"
python3 - <<'PY'
import json
from pathlib import Path

root = Path('/home/ypwang/5020-Project')
paths = [
    root / 'report/tables/epsilon_sweep_synthetic/results.jsonl',
    root / 'report/tables/epsilon_sweep_kosarak/results.jsonl',
]
rows = []
for path in paths:
    rows.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip())

out = root / 'report/tables/epsilon_sweep_merged/results.jsonl'
out.write_text('\n'.join(json.dumps(row, sort_keys=True) for row in rows) + '\n', encoding='utf-8')
PY
python3 - <<'PY'
import json
from pathlib import Path
import sys

sys.path.insert(0, '/home/ypwang/5020-Project/src')
from seem5020.utils.io import write_csv, write_json

root = Path('/home/ypwang/5020-Project')
rows = [
    json.loads(line)
    for line in (root / 'report/tables/epsilon_sweep_merged/results.jsonl').read_text(encoding='utf-8').splitlines()
    if line.strip()
]
write_csv(root / 'report/tables/epsilon_sweep_merged/results.csv', rows)
write_json(
    root / 'report/tables/epsilon_sweep_merged/merge_manifest.json',
    {
        'sources': [
            'report/tables/epsilon_sweep_synthetic/results.jsonl',
            'report/tables/epsilon_sweep_kosarak/results.jsonl',
        ],
        'num_rows': len(rows),
    },
)
PY

echo "[2/2] Building merged epsilon-sweep summary"
python3 -m experiments.summarize_results \
  report/tables/epsilon_sweep_merged/results.jsonl \
  --output-csv report/tables/epsilon_sweep_merged/summary.csv

echo "Merged outputs written to report/tables/epsilon_sweep_merged"
