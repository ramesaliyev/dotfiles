#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

docker buildx build -f "$ROOT/dev/Dockerfile" -t dotfiles-dev "$ROOT"

docker run -it --rm \
  -v "$ROOT:/root/dotfiles" \
  -w /root/dotfiles \
  -e UV_PROJECT_ENVIRONMENT=/root/.venv \
  dotfiles-dev bash
