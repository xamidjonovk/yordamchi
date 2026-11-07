#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  installer="$(mktemp)"
  curl -fsSL https://astral.sh/uv/0.13.6/install.sh -o "$installer"
  sh "$installer"
  rm -f "$installer"
  export PATH="$HOME/.local/bin:$PATH"
fi
cd "$project_dir"
uv sync --frozen --python 3.11 --no-dev
if [[ ${1:-} != '--prepare-only' ]]; then exec .venv/bin/hpa web; fi
