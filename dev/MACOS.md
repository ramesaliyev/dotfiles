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

# Stop
colima stop

# Check status
colima status
```

Start Colima before running any `docker` commands. Stop it when you're done.

## Troubleshooting

### Slow network inside containers

If downloads inside containers are very slow (~100 KB/s), test the VM's network speed:

```sh
colima ssh -- curl -L -o /dev/null -w "Speed: %{speed_download} bytes/sec\n" https://files.pythonhosted.org/packages/source/p/pip/pip-24.3.1.tar.gz
```

If it's slow, a full reinstall (see below) usually fixes it — likely corrupted state. If that doesn't help, run `colima start` once to generate the config, then stop it and set `network.address: true` in `~/.colima/default/colima.yaml` — this switches from user-space NAT to macOS's vmnet framework:

```yaml
network:
  address: true
```

Then `colima delete && colima start`.

## Uninstall / reset

To remove all installed stuff and start from scratch.

```sh
brew uninstall docker docker-buildx colima
rm -rf ~/.docker
rm -rf ~/.colima
```
