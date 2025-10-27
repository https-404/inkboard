#!/usr/bin/env bash

set -e

PY_VERSION="3.12.12"
VENV_DIR=".venv"

echo "🚀 Starting Python environment setup..."

# --- STEP 1: Check for Python 3.12 ---
echo "🔍 Checking existing Python installation..."
PY_CMD=$(command -v python3 || true)

if [ -n "$PY_CMD" ]; then
  PY_VER=$($PY_CMD -V 2>&1 | awk '{print $2}')
  if [[ "$PY_VER" == 3.12* ]]; then
    echo "✅ Found Python $PY_VER system-wide."
    PYTHON_BIN=$PY_CMD
  else
    echo "⚠️ Found Python $PY_VER, but need 3.12.x."
    PYTHON_BIN=""
  fi
else
  echo "❌ No Python installation found."
  PYTHON_BIN=""
fi

# --- STEP 2: Fallback to pyenv if needed ---
if [ -z "$PYTHON_BIN" ]; then
  if command -v pyenv &>/dev/null; then
    echo "📦 Using pyenv to ensure Python $PY_VERSION..."
    if ! pyenv versions --bare | grep -q "$PY_VERSION"; then
      echo "⬇️ Installing Python $PY_VERSION with pyenv..."
      pyenv install $PY_VERSION
    else
      echo "✅ Python $PY_VERSION already installed via pyenv."
    fi
    pyenv local $PY_VERSION
    eval "$(pyenv init -)"
    PYTHON_BIN=$(pyenv which python)
  else
    echo "❌ Python 3.12 not found and pyenv not installed."
    echo "👉 Please install pyenv first:"
    echo "   https://github.com/pyenv/pyenv#installation"
    exit 1
  fi
fi

# --- STEP 3: Create virtual environment ---
if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 Creating virtual environment with $PYTHON_BIN..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "✅ Virtual environment already exists."
fi

# --- STEP 4: Activate and install deps ---
echo "🔗 Activating virt
