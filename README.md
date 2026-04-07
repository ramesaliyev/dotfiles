# dotfiles

```bash
uv run collect    # pull latest configs from this machine into the repo
uv run bootstrap  # set up this machine from the repo
```

## Development

```bash
uv run setup-dev  # install pre-commit hooks (run once after cloning)
```

After that, every commit automatically runs `ruff check --fix`, `ruff format`, and `pytest`.
