#!/bin/bash
set -euo pipefail

PYTHON="${PYTHON:-python3.12}"
VENV="${VENV:-.venv}"
WHEELHOUSE="${WHEELHOUSE:-pypi}"

if [[ ${LOCK+x} ]]; then
  echo "LOCK is set."
  REQFILE="${REQFILE:-requirements-lock.txt}"
else
  REQFILE="${REQFILE:-requirements.txt}"
fi

CA_BUNDLE="${CA_BUNDLE:-/etc/ssl/certs/ca-certificates.crt}"
export TWINE_CA_BUNDLE="${CA_BUNDLE}"

command -v "${PYTHON}" >/dev/null 2>&1 || {
    echo "ERROR: ${PYTHON} is not installed." >&2
    exit 1
}

[[ -d "${WHEELHOUSE}" ]] || {
    echo "ERROR: Wheelhouse not found: ${WHEELHOUSE}" >&2
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

echo
echo "Installing packages from ${WHEELHOUSE}..."
if [[ ${LOCK+x} ]]; then
  "${VENV}/bin/python" -m pip install \
    --no-index \
    --find-links "${WHEELHOUSE}" \
    --require-hashes \
    --requirement "${REQFILE}"
else
  "${VENV}/bin/python" -m pip install \
    --no-index \
    --find-links "${WHEELHOUSE}" \
    --requirement "${REQFILE}"
fi

echo
echo "Verifying installed requirements..."
"${VENV}/bin/python" -m pip check

echo
echo "Environment created successfully: ${VENV}"
echo "Activate with: source ${VENV}/bin/activate"
echo "CA bundle used: ${CA_BUNDLE}"