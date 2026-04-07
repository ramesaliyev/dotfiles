# tmux

Config (`~/.tmux.conf`) is bootstrapped automatically. tmux reads it on startup, but if a session is already running you need to reload it manually (see below).

Plugins are managed by [TPM](https://github.com/tmux-plugins/tpm) and must be set up manually — TPM itself is not committed to this repo.

## Fresh setup (first time on a new machine)

**1. Install TPM:**
```bash
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

**2. Start tmux:**
```bash
tmux
```

**3. Install plugins** (inside tmux):
```
Ctrl+A  then  I
```

**4. Reload config** (inside tmux):
```
Ctrl+A  then  r
```

Sessions auto-save every 10 minutes via tmux-resurrect/continuum once plugins are installed.

## Already running tmux (config updated)

Reload config inside tmux:
```
Ctrl+A  then  r
```

## New plugins added to `.tmux.conf`

Install them inside tmux:
```
Ctrl+A  then  I
```
