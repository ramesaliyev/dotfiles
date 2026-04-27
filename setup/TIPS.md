# Tips

Loose collection of editor / tooling tweaks that aren't worth automating but are worth remembering.

## VS Code

### Set zsh as the default terminal

1. `Ctrl + Shift + P`
2. Search: `Terminal: Select Default Profile`
3. Pick `zsh`

### Fast Python `.venv` activation

VS Code's built-in venv activation runs the full `activate` script every time a terminal opens, which can take noticeable seconds on zsh. Skip it: set `VIRTUAL_ENV` and `PATH` directly via terminal env vars — every tool that matters (`python`, `pip`, `which`, etc.) only checks `PATH` anyway.

**1. Per-project `.vscode/settings.json`:**

```json
{
  "python.terminal.activateEnvironment": false,
  "terminal.integrated.env.osx": {
    "VIRTUAL_ENV": "${workspaceFolder}/.venv",
    "PATH": "${workspaceFolder}/.venv/bin:${env:PATH}"
  },
  "terminal.integrated.env.linux": {
    "VIRTUAL_ENV": "${workspaceFolder}/.venv",
    "PATH": "${workspaceFolder}/.venv/bin:${env:PATH}"
  },
  "terminal.integrated.env.windows": {
    "VIRTUAL_ENV": "${workspaceFolder}\\.venv",
    "PATH": "${workspaceFolder}\\.venv\\Scripts;${env:PATH}"
  }
}
```

VS Code only reads the key matching the current OS; the others are ignored, so it's safe to ship all three.

**2. Show the venv name in your zsh prompt** (`~/.zshrc`):

```zsh
if [[ -n "$VIRTUAL_ENV" && -z "$VIRTUAL_ENV_DISABLE_PROMPT" ]]; then
    PROMPT="(${VIRTUAL_ENV:t}) $PROMPT"
fi
```

Place this **after** your prompt framework (oh-my-zsh `source`, starship init, p10k, etc.) — otherwise the theme overwrites it. If your prompt framework already shows a venv segment, skip this block.

**Caveats:** since the `activate` script never runs, `deactivate` isn't defined and `PYTHONHOME` isn't unset. Neither matters in a typical VS Code integrated terminal session, but worth knowing.
