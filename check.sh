#!/usr/bin/env sh
set -x
set -eou pipefail
uv run black --check .
uv run mypy .
