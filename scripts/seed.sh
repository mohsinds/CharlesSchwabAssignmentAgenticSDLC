#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/data/audit" "$ROOT/artifacts"
echo "Seeded local data dirs."
echo "Brownfield seed repo at scenarios/brownfield/seed_repo"
