#!/usr/bin/env bash
# Rebuild dependencies only; never downloads model weights or starts experiments.
set -euo pipefail

cd "$(dirname "$0")/.."
uv_bin="${SUPPLEMENT_UV_BIN:-uv}"
"$uv_bin" --version
"$uv_bin" python install 3.12.13
"$uv_bin" sync --python 3.12.13 --frozen --extra gpu --no-install-package flash-attn
"$uv_bin" sync --python 3.12.13 --frozen --extra gpu
.venv/bin/python -c 'import sys; print(sys.version)'
