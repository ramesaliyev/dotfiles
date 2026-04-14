# First-time Setup

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

## 7. Clone and bootstrap

```sh
# HTTPS
git clone https://github.com/ramesaliyev/dotfiles.git ~/dotfiles
# SSH (for development)
git clone git@github.com:ramesaliyev/dotfiles.git ~/dotfiles

cd ~/dotfiles
uv run bootstrap
```

Follow any notes printed at the end of the bootstrap run.

## 8. Activate tmux config and install plugins

After bootstrap, `~/.tmux.conf` is in place. Start a tmux session so it loads the config:

```bash
tmux
```

If a tmux server was already running before bootstrap, reload the config from outside:

```bash
tmux source-file ~/.tmux.conf
```

Then inside tmux, install plugins:

```
Ctrl+A  then  I
```

TPM reloads config after installing. Sessions will auto-save every 10 minutes once plugins are in place.

## 9. VS Code: Set ZSH as Default Terminal

1. Press `Ctrl + Shift + P`
2. Search: `Terminal: Select Default Profile`
3. Select `zsh`

---

## Updating an existing machine

Running tmux sessions don't pick up config changes on disk automatically. Reload from any session:

```
Ctrl+A  then  R
```

If new plugins were added, install them:

```
Ctrl+A  then  I
```

---

## Troubleshooting

### tmux opens the wrong shell

tmux reads `$SHELL` from the **server process environment** — the environment that existed when the tmux server was first started, not from whatever shell you ran `tmux` from. tmux-sensible then sets `default-shell` from that value. New sessions and windows always inherit from the running server, not from the calling shell.

To fix the underlying shell, follow the [oh-my-zsh wiki: Installing ZSH](https://github.com/ohmyzsh/ohmyzsh/wiki/Installing-ZSH) to set zsh as your default shell, then log out and back in.

Even after fixing `$SHELL`, if a tmux server is already running it still holds the old environment. Kill it and start fresh:

```bash
tmux kill-server
tmux
```
