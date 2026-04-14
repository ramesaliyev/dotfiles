#!/bin/sh
echo "→ Installing pre-commit hooks"
uv run pre-commit install -f
echo "  ✓ Done — hooks will run on every commit"
