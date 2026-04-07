# tmux

Configs are bootstrapped automatically. Plugins are managed by [TPM](https://github.com/tmux-plugins/tpm) and must be installed manually after bootstrap.

## Post-bootstrap steps

1. Start tmux: `tmux`
2. Install plugins: `Ctrl+A` then `I`
3. Reload config: `Ctrl+A` then `r`

Sessions auto-save every 10 minutes via tmux-resurrect/continuum once plugins are installed.
