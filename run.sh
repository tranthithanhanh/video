#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Chưa cài đặt. Chạy: bash install.sh' >&2
  exit 1
fi
exec .venv/bin/python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --browser.gatherUsageStats false "$@"
