# dev

## Test environment (Docker)

The Dockerfile provides an Ubuntu 24.04 image with only the essentials needed to follow [SETUP.md](../SETUP.md) inside the container (sudo, curl, git). The purpose is to validate the full bootstrap flow from scratch.

### Prerequisites (macOS)

See [MACOS.md](MACOS.md) for Docker setup on macOS.

### Build and run

Following will spin-up one-time container for testing, which will be removed when you exit.

```sh
./dev/docker.sh
```

Inside the container, follow SETUP.md step by step. Skip step 7 (clone) — your dotfiles are already mounted at `~/dotfiles`. Continue from step 8 (bootstrap). This confirms that bootstrap works on a clean Linux environment.

For a quicker test run, `auto.sh` automates all the SETUP.md prerequisites in one shot:

```sh
./dev/auto.sh
```

This installs zsh, oh-my-zsh, tmux, TPM, uv, and Python 3.14 — then drops you into a zsh session ready to run `uv run bootstrap`.

## Pre-commit hooks

To install pre-commit hooks for local development:

```sh
./dev/dev.sh
```

After that, every commit automatically runs `ruff check --fix`, `ruff format`, and `pytest`.
