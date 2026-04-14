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

### First-time setup

After installing, fix the MTU before starting Colima. Docker's default MTU (1500) causes packet fragmentation inside the VM, which significantly slows down network operations.

Start Colima once so it generates the config file:

```sh
colima start
colima stop
```

Then add `mtu: 1450` under the `docker:` section in `~/.colima/default/colima.yaml`:

```yaml
docker:
  mtu: 1450
```

Start Colima again and verify:

```sh
colima start
docker run --rm ubuntu:24.04 cat /sys/class/net/eth0/mtu
# should show 1450
```

This persists across `colima delete`/`start` cycles as Colima generates the Docker daemon config from this file on every start.

### Daily use

```sh
# Start
colima start

# Stop
colima stop

# Check status
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
