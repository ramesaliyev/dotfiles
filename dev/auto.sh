#!/usr/bin/env bash
# auto.sh — run this once inside the Docker container to install all prerequisites
# before running `uv run bootstrap`.
set -e

# ---------------------------------------------------------------------------
# zsh
# ---------------------------------------------------------------------------

# Install zsh
sudo apt-get install -y zsh

# Set zsh as the default login shell for the current user
chsh -s "$(which zsh)"

# Install oh-my-zsh without starting a zsh session afterward and without
# touching chsh again (we already did it above).
RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# ---------------------------------------------------------------------------
# tmux
# ---------------------------------------------------------------------------

# Install tmux
sudo apt-get install -y tmux

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

echo ""
echo "All prerequisites installed. Now you can continue with:"
echo "  uv run bootstrap"
echo ""

# Replace this bash session with zsh so PATH and shell environment are correct
exec zsh
