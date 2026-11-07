#!/usr/bin/env bash
set -euo pipefail
prepare_only=0
if [[ ${1:-} == '--prepare-only' ]]; then prepare_only=1; shift; fi
if [[ $# -ne 0 ]]; then echo 'Usage: install.sh [--prepare-only]' >&2; exit 2; fi
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(uname -s)" == Darwin && "$(uname -m)" == x86_64 ]]; then
  printf '%s\n' 'Intel Mac: use Docker Compose; the Telegram call library has no current Intel macOS wheel.'
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/0.13.6/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v hermes >/dev/null 2>&1 && [[ ! -x "$HOME/.local/bin/hermes" ]]; then
  installer="$(mktemp)"
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/bf0203a794a07aac3ff764972ab9087baa4e4f4e/scripts/install.sh -o "$installer"
  bash "$installer" --commit bf0203a794a07aac3ff764972ab9087baa4e4f4e --non-interactive
  rm -f "$installer"
fi
cd "$project_dir"
uv sync --frozen --python 3.11 --no-dev --extra calls
printf '\n%s\n' 'Installation complete. Start the local setup wizard:'
printf '  %q setup\n' "$project_dir/.venv/bin/hpa"
if (( ! prepare_only )); then
  "$project_dir/.venv/bin/hpa" setup
else
  printf '%s\n' 'Setup was skipped. Import your private transfer or run hpa setup manually.'
fi
