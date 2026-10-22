#!/bin/bash
set -euo pipefail

PYTHON="${PYTHON:-python3.12}"
VENV="${VENV:-.venv}"

command -v "${PYTHON}" >/dev/null 2>&1 || {
    echo "ERROR: Python interpreter not found: ${PYTHON}" >&2
    exit 1
}

if [[ -z "${WHEELHOUSE:-}" ]]; then
    PYTHON_SERIES=$(
        "${PYTHON}" -c \
            'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
    )

    shopt -s nullglob
    matches=( "pypi-${PYTHON_SERIES}."* )
    shopt -u nullglob

    case "${#matches[@]}" in
        0)
            echo "ERROR: No pypi-${PYTHON_SERIES}.* directory found." >&2
            exit 1
            ;;
        1)
            WHEELHOUSE="${matches[0]}"
            ;;
        *)
            echo "ERROR: Multiple matching wheelhouses found:" >&2
            printf '  %s\n' "${matches[@]}" >&2
            echo "Set WHEELHOUSE explicitly to select one." >&2
            exit 1
            ;;
    esac
fi

[[ -d "${WHEELHOUSE}" ]] || {
    echo "ERROR: Wheelhouse is not a directory: ${WHEELHOUSE}" >&2
    exit 1
}

echo "Using Python:     $("${PYTHON}" --version 2>&1)"
echo "Using wheelhouse: ${WHEELHOUSE}"

if [[ ${LOCK+x} ]]; then
    echo "LOCK is set."
    REQFILE="${REQFILE:-requirements-lock.txt}"
else
    REQFILE="${REQFILE:-requirements-dev.txt}"
fi

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