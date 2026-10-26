#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

cd "$ROOT"
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') scrape started ==="
  "$ROOT/.venv/bin/python" -m Scraper.validate
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') scrape finished ==="
} >> "$LOG_DIR/scrape.log" 2>&1
