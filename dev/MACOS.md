# Docker on macOS

Use [Colima](https://github.com/abiosoft/colima) as a lightweight Docker runtime instead of Docker Desktop.

## Install

```sh
brew install colima docker docker-buildx
```

Check the output of the command. After installing `docker-buildx`, brew will probably prompt you to register it as a Docker CLI plugin by adding the following to `~/.docker/config.json`:

```json
{
  "cliPluginsExtraDirs": [
    "/opt/homebrew/lib/docker/cli-plugins"
  ]
}
```

## Usage

```sh
# Start 
colima start

# Verify it works
docker run hello-world

# Stop
colima stop

# Check the status
colima status
```

Start Colima before running any `docker` commands. Stop it when you're done.

## Uninstall / reset

To remove all installed stuff and start from scratch.

```sh
brew uninstall docker docker-buildx colima
rm -rf ~/.docker
rm -rf ~/.colima
```
