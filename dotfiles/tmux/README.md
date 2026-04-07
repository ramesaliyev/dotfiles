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

**3. Source the config** (inside tmux):
```
<prefix>  then  :source-file ~/.tmux.conf
```
> What prefix to use depends on whether a tmux server was already running before step 2. If it wasn't, tmux started fresh and loaded our config — prefix is already `Ctrl+A`. If it was, the old config is still active — use whatever prefix was set then (likely `Ctrl+B`, the tmux default). If you're unsure, try `Ctrl+A` first, then `Ctrl+B`.

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
