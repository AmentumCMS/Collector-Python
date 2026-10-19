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

if [[ ${LOCK+x} ]]; then
  echo "LOCK is set, using requirements-lock.txt"
  REQUIREMENTS_FILE="requirements-lock.txt"
  echo "Installing development requirements."
  pip install -r "$REQUIREMENTS_FILE"
else
  echo "LOCK is not set, using requirements-dev.txt"
  REQUIREMENTS_FILE="requirements-dev.txt"
  echo "Installing development requirements and generating lock file."
  pip install -r "$REQUIREMENTS_FILE"
  pip-compile --generate-hashes -o requirements-lock.txt requirements-dev.txt
fi