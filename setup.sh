#!/bin/bash
set -euo pipefail

if [[ -d .venv ]]; then
  echo ".venv already exists."
  source .venv/bin/activate
  echo "Activated existing .venv."
else
  echo "Creating new .venv."
  python -m venv .venv
  source .venv/bin/activate
  echo "Activated new .venv."
  python -m pip install \
    --upgrade \
    pip \
    pip-tools \
    setuptools \
    wheel
fi

echo "Installing development requirements and generating lock file."
pip install -r requirements-dev.txt 
pip-compile --generate-hashes -o requirements-lock.txt requirements-dev.txt