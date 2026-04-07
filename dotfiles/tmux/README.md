# tmux

You need to have [tmux already installed](https://github.com/tmux/tmux/wiki/Installing).

Config (`~/.tmux.conf`) is bootstrapped automatically. Plugins are managed by [TPM](https://github.com/tmux-plugins/tpm) and are not committed to this repo.

## New machine

**1. Install TPM:**
```bash
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

**2. Start a new tmux session:**
```bash
tmux
```

**3. Source the config** (inside tmux) — on first install the active prefix is tmux's default `Ctrl+B`, since our custom `Ctrl+A` isn't loaded yet. If you previously had a custom prefix configured, use that instead:
```
Ctrl+B  then  :source-file ~/.tmux.conf
```

**4. Install plugins:**
```
Ctrl+A  then  I
```

TPM reloads config after installing. Sessions will auto-save every 10 minutes once plugins are in place.

## Updating an existing machine

Running tmux sessions doesn't pick up config changes on disk automatically. Reload it manually from any session:

```
Ctrl+A  then  R
```

If new plugins were added, install them:
```
Ctrl+A  then  I
```
