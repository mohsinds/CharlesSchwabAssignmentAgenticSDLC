#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
bash scripts/seed.sh
python scripts/run_scenario.py --scenario greenfield --mode replay
echo "Demo complete. Open http://localhost:5173"
