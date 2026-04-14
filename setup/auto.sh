#!/usr/bin/env bash
# setup/auto.sh — detects your environment and installs all prerequisites
# before running `uv run bootstrap`. Supported: macOS, Ubuntu/Debian, Fedora.
set -e

# ---------------------------------------------------------------------------
# Detect environment
# ---------------------------------------------------------------------------

if [[ "$(uname -s)" == "Darwin" ]]; then
    ENV="macos"
elif command -v apt-get &>/dev/null; then
    ENV="ubuntu"
elif command -v dnf &>/dev/null; then
    ENV="fedora"
else
    echo "Unsupported environment. Supported: macOS, Ubuntu/Debian, Fedora."
    exit 1
fi

echo "Detected environment: $ENV"

# ---------------------------------------------------------------------------
# Homebrew (macOS only)
# ---------------------------------------------------------------------------

if [[ "$ENV" == "macos" ]]; then
    # Install Homebrew if not already present
    if ! command -v brew &>/dev/null; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # Make brew available in this shell session — on Apple Silicon it lives in
    # /opt/homebrew rather than /usr/local, so it may not be on PATH yet.
    if [[ -f /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f /usr/local/bin/brew ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
fi

# ---------------------------------------------------------------------------
# zsh
# ---------------------------------------------------------------------------

if [[ "$ENV" == "macos" ]]; then
    # Install latest zsh via Homebrew (macOS ships an older system zsh)
    brew install zsh

    # Add Homebrew's zsh to the list of allowed shells, then set it as default.
    # chsh requires the target shell to be listed in /etc/shells.
    ZSH_PATH="$(brew --prefix)/bin/zsh"
    if ! grep -qF "$ZSH_PATH" /etc/shells; then
        echo "$ZSH_PATH" | sudo tee -a /etc/shells
    fi
    chsh -s "$ZSH_PATH"
elif [[ "$ENV" == "ubuntu" ]]; then
    sudo apt-get install -y zsh
    chsh -s "$(which zsh)"
elif [[ "$ENV" == "fedora" ]]; then
    # util-linux-user provides chsh on Fedora
    sudo dnf install -y zsh util-linux-user
    chsh -s "$(which zsh)"
fi

# Install oh-my-zsh without starting a zsh session afterward and without
# touching chsh again (we already did it above).
RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# ---------------------------------------------------------------------------
# tmux
# ---------------------------------------------------------------------------

if [[ "$ENV" == "macos" ]]; then
    brew install tmux
elif [[ "$ENV" == "ubuntu" ]]; then
    sudo apt-get install -y tmux
elif [[ "$ENV" == "fedora" ]]; then
    sudo dnf install -y tmux
fi

# Install TPM (tmux plugin manager) — bootstrap will sync .tmux.conf,
# and TPM must exist before you can install plugins inside tmux.
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

# ---------------------------------------------------------------------------
# uv + Python
# ---------------------------------------------------------------------------

# Install uv (the package/project manager used by this repo)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Make uv available in this shell session
# shellcheck source=/dev/null
source "$HOME/.local/bin/env"

# Install the Python version required by the project
uv python install 3.14

# ---------------------------------------------------------------------------

GREEN="\033[32m"
RESET="\033[0m"

echo ""
echo -e "${GREEN}All prerequisites installed. Now you can continue with:"
echo -e "  uv run bootstrap${RESET}"
echo ""
echo "WARNING: When you are done, close this terminal completely."
echo "Do not type 'exit' — it will drop you back into the old shell with an incomplete environment."
echo ""

# Replace this bash session with zsh so PATH and shell environment are correct
exec zsh
