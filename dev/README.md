# dev

## Test environment (Docker)

The Dockerfile provides an Ubuntu 24.04 image with only the essentials needed to follow [SETUP.md](../SETUP.md) inside the container (sudo, curl, git). The purpose is to validate the full bootstrap flow from scratch.

### Prerequisites (macOS)

See [MACOS.md](MACOS.md) for Docker setup on macOS.

### Build and run

```sh
./dev/docker.sh
```

Inside the container, follow SETUP.md step by step. Skip the `git clone` in step 7 — your dotfiles are already mounted at `~/dotfiles`. This confirms that bootstrap works on a clean Linux environment.

The `--rm` flag means the container is automatically deleted when you exit. Run the `docker run` command again to get a fresh container.

## Pre-commit hooks

To install pre-commit hooks for local development:

```sh
./dev/dev.sh
```

After that, every commit automatically runs `ruff check --fix`, `ruff format`, and `pytest`.
