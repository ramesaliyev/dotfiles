# First-time Setup

## Automatic

A single script supports macOS, Ubuntu/Debian, and Fedora — it detects your environment automatically. Try it first:

```sh
./setup/auto.sh
```

This installs all prerequisites and drops you into a zsh session ready to run `uv run bootstrap`. If anything fails, fall back to the manual steps below.

---

## Manual

Follow these steps in order on a fresh machine before running `uv run bootstrap`.

## 1. Install zsh and set as default shell

Follow the [oh-my-zsh wiki: Installing ZSH](https://github.com/ohmyzsh/ohmyzsh/wiki/Installing-ZSH) — it covers macOS, Ubuntu, Fedora, and more.

## 2. Install oh-my-zsh

Follow the [oh-my-zsh repo](https://github.com/ohmyzsh/ohmyzsh) for install instructions.

## 3. Install tmux

Follow the [tmux wiki: Installing](https://github.com/tmux/tmux/wiki/Installing).

## 4. Install TPM (tmux plugin manager)

Follow the [TPM repo](https://github.com/tmux-plugins/tpm) for install instructions.

## 5. Install uv

Follow the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

## 6. Install Python 3.14

```sh
uv python install 3.14
```

## 7. Bootstrap

Clone the repo if you haven't already and go into it:

```sh
# HTTPS
git clone https://github.com/ramesaliyev/dotfiles.git ~/dotfiles
# SSH (for development)
git clone git@github.com:ramesaliyev/dotfiles.git ~/dotfiles

cd ~/dotfiles
```

Then run bootstrap and follow any instructions it prints:

```sh
uv run bootstrap
```

---

## Notes

### Updating an existing machine

Running tmux sessions don't pick up config changes on disk automatically. Reload from any session:

```
Ctrl+A  then  R
```

If new plugins were added, install them:

```
Ctrl+A  then  I
```

### Troubleshooting

#### tmux opens the wrong shell

tmux reads `$SHELL` from the **server process environment** — the environment that existed when the tmux server was first started, not from whatever shell you ran `tmux` from. tmux-sensible then sets `default-shell` from that value. New sessions and windows always inherit from the running server, not from the calling shell.

To fix the underlying shell, follow the [oh-my-zsh wiki: Installing ZSH](https://github.com/ohmyzsh/ohmyzsh/wiki/Installing-ZSH) to set zsh as your default shell, then log out and back in.

Even after fixing `$SHELL`, if a tmux server is already running it still holds the old environment. Kill it and start fresh:

```bash
tmux kill-server
tmux
```
