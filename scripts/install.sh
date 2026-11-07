#!/usr/bin/env bash
set -euo pipefail
prepare_only=0
if [[ ${1:-} == '--prepare-only' ]]; then prepare_only=1; shift; fi
if [[ $# -ne 0 ]]; then echo 'Usage: install.sh [--prepare-only]' >&2; exit 2; fi
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
printf '%s\n' '1/3: Python va kutubxonalar tayyorlanmoqda.'
if ! command -v uv >/dev/null 2>&1; then
  installer="$(mktemp)"
  curl -fsSL https://astral.sh/uv/0.13.6/install.sh -o "$installer"
  sh "$installer"
  rm -f "$installer"
fi
export PATH="$HOME/.local/bin:$PATH"
cd "$project_dir"
uv sync --frozen --python 3.11 --no-dev --extra calls
hermes_profile="$(.venv/bin/python -c 'from hermes_personal_agent.voice_common import HERMES_HOME; print(HERMES_HOME)')"
export HERMES_HOME="$hermes_profile"
printf '%s\n' '2/3: Hermes shaxsiy nusxangiz uchun avtomatik ornatilmoqda.'
if [[ ! -x "$hermes_profile/bin/hermes" ]] || ! .venv/bin/python scripts/check-hermes.py "$hermes_profile/bin/hermes"; then
  installer="$(mktemp)"
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/bf0203a794a07aac3ff764972ab9087baa4e4f4e/scripts/install.sh -o "$installer"
  bash "$installer" --commit bf0203a794a07aac3ff764972ab9087baa4e4f4e --non-interactive
  rm -f "$installer"
fi
export PATH="$hermes_profile/bin:$HOME/.local/bin:$PATH"
# POSIX Hermes installers may place the launcher in ~/.local/bin.
if [[ -x "$hermes_profile/bin/hermes" ]]; then export HERMES_BIN="$hermes_profile/bin/hermes"; else export HERMES_BIN="$(command -v hermes)"; fi
.venv/bin/python scripts/check-hermes.py "$HERMES_BIN"
.venv/bin/python -c 'import os; from hermes_personal_agent.voice_common import save_config; save_config({"hermes_bin":os.environ["HERMES_BIN"],"hermes_home":os.environ["HERMES_HOME"]})'
printf '%s\n' '3/3: Ozbekcha sozlash ustasi tayyor.'
if (( ! prepare_only )); then exec .venv/bin/hpa web --setup; fi
