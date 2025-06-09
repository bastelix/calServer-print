#!/usr/bin/env bash

# Install Python and (optional) Node dependencies for calServer Labeltool
set -e

if [ ! -f requirements.txt ]; then
    echo "Please run this script from the repository root" >&2
    exit 1
fi

echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt

if [ -f electron/package.json ]; then
    if command -v npm >/dev/null 2>&1; then
        echo "Installing Node dependencies for Electron..."
        (cd electron && npm install)
    else
        echo "npm not found: skipping Electron dependency installation" >&2
    fi
fi

echo "Setup completed."
