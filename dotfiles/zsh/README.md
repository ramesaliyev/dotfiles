# zsh

## 1. Install zsh

Make sure [zsh is installed](https://github.com/ohmyzsh/ohmyzsh/wiki/Installing-ZSH).

## 2. Install oh-my-zsh

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

## 3. Install plugins

Run the bootstrap script and it will install missing plugins automatically:

```bash
uv run bootstrap
```

Or install them manually:

### zsh-autosuggestions
Suggests commands as you type based on history.

```bash
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
```

### zsh-syntax-highlighting
Colors commands green/red as you type.

```bash
git clone https://github.com/zsh-users/zsh-syntax-highlighting ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

### you-should-use
Reminds you when an alias exists for a command you typed.

```bash
git clone https://github.com/MichaelAquilina/zsh-you-should-use.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/you-should-use
```

### autojump
Jump to frecently used directories with `j <partial-name>`. Requires a separate install step:

```bash
git clone https://github.com/wting/autojump.git /tmp/autojump
cd /tmp/autojump
python3 install.py
```

## 4. Update ~/.zshrc

Make sure this line is in your `~/.zshrc`:

```
plugins=(git copypath autojump you-should-use zsh-autosuggestions zsh-syntax-highlighting)
```

Then reload:

```bash
source ~/.zshrc
```

> Bootstrap will warn you if any of these plugins are missing from your `plugins=()` line.

## 5. VS Code: Set ZSH as Default Terminal

1. Press `Ctrl + Shift + P`
2. Search: `Terminal: Select Default Profile`
3. Select `zsh`
