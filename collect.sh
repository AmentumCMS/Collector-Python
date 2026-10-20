#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
  echo -e "\nUsage Instructions:"
  echo -e "\t $0 directory"
  exit 1
fi

ROOTDIR=${1}
echo -e "\n$ROOTDIR"

PYTHON="${PYTHON:-python3.12}"
VENV="${VENV:-.venv}"
WHEELHOUSE="${WHEELHOUSE:-pypi}"

if [[ ${LOCK+x} ]]; then
  echo "LOCK is set."
  REQFILE="${REQFILE:-requirements-lock.txt}"
else
  REQFILE="${REQFILE:-requirements.txt}"
fi

command -v "${PYTHON}" >/dev/null 2>&1 || {
    echo "ERROR: ${PYTHON} is not installed." >&2
    exit 1
}

[[ -f "${REQFILE}" ]] || {
    echo "ERROR: Requirements file not found: ${REQFILE}" >&2
    exit 1
}

echo "Creating ${VENV} with ${PYTHON}..."
"${PYTHON}" -m venv "${VENV}"

echo "Python environment:"
"${VENV}/bin/python" --version
"${VENV}/bin/python" -c 'import sys; print(sys.executable)'
"${VENV}/bin/python" -m pip --version

echo -e "\nVerifying installed requirements..."
"${VENV}/bin/python" -m pip check

echo -e "\nInstalling/upgrading essential packages..."
"${VENV}/bin/python" -m pip install \
  --upgrade \
  pip \
  pip-tools \
  setuptools \
  wheel
echo -e "\nEssential packages installed."

echo -e "\nInstalling project requirements..."
if [[ ${LOCK+x} ]]; then
  echo "LOCK is set."
  "${VENV}/bin/python" -m pip install \
    --require-hashes \
    --requirement ${REQFILE}
else
  echo "LOCK is not set."
  "${VENV}/bin/python" -m pip install \
    --requirement ${REQFILE}
fi

echo -e "\nDownloading packages to wheelhouse..."
"${VENV}/bin/python" -m pip download \
  --dest pypi-$("${VENV}/bin/python" --version | awk '{print $2}') \
  --requirement ${REQFILE}

echo
echo "Environment created successfully: ${VENV}"
echo "Activate with: source ${VENV}/bin/activate"