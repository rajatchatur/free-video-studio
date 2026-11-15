#!/usr/bin/env bash
# Free Video Studio - setup for macOS (Apple Silicon M1/M2/M3)
set -euo pipefail

if ! command -v brew >/dev/null; then
  echo "Installing Homebrew (free)..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

brew install ffmpeg node@22 python@3.12 git
brew link --overwrite node@22 || true

cd "$(dirname "$0")/.."
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Hyperframes + its agent skills (free, Apache 2.0)
npx --yes hyperframes doctor || true
npx skills add heygen-com/hyperframes || echo "Skills step skipped - run it again later"

# Optional: motion-design skill packs from GitHub
# npx skills add iart-ai/motion-skills
# npx skills add whaleyxbt/claude-motion

echo ""
echo "Setup finished. Start the studio with:  ./scripts/run_mac.sh"
