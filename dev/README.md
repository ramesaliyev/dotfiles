# dev

## Test environment (Docker)

The Dockerfile provides a raw Ubuntu 24.04 image with nothing pre-installed. The purpose is to validate the full bootstrap flow from scratch by following [SETUP.md](../SETUP.md) inside the container.

### Prerequisites (macOS)

See [MACOS.md](MACOS.md) for Docker setup on macOS.

### Build and run

```sh
docker buildx build -f dev/Dockerfile -t dotfiles-dev .
docker run -it --rm -v "$(pwd):/dotfiles" dotfiles-dev bash
```

Inside the container, follow SETUP.md step by step. This confirms that bootstrap works on a clean Linux environment.

The `--rm` flag means the container is automatically deleted when you exit. Run the `docker run` command again to get a fresh container.

## Pre-commit hooks

To install pre-commit hooks for local development:

```sh
./dev/dev.sh
```

After that, every commit automatically runs `ruff check --fix`, `ruff format`, and `pytest`.
