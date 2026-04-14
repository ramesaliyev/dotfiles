#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

docker buildx build -f "$ROOT/dev/Dockerfile" -t dotfiles-dev "$ROOT"

# The container will be removed after exit, so we don't have to worry about cleanup.
docker run -it --rm \
  -v "$ROOT:/root/dotfiles" \
  -w /root/dotfiles \
  -e UV_PROJECT_ENVIRONMENT=/root/.venv \
  dotfiles-dev bash
