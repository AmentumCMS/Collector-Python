#!/bin/bash
set -euo pipefail

: "${NEXUS_URL:?}"
: "${NEXUS_USER:?}"
: "${NEXUS_PASSWORD:?}"

if [[ ${CA_BUNDLE+x} ]]; then
    echo "CA_BUNDLE is set: ${CA_BUNDLE}"
else
    CA_BUNDLE="${CA_BUNDLE:-/etc/ssl/cert.pem}"
    echo "Using CA_BUNDLE: ${CA_BUNDLE}"
fi

command -v twine >/dev/null || {
    echo "ERROR: twine not found"
    echo "Run kickstart.sh to set up the environment"
    exit 1
}

REPORT="upload.log"

: > "${REPORT}"

[[ -r "${CA_BUNDLE}" ]] || {
    echo "ERROR: CA bundle is not readable: ${CA_BUNDLE}" >&2
    exit 1
}
export TWINE_CERT="${CA_BUNDLE}"
export REQUESTS_CA_BUNDLE="${CA_BUNDLE}"

echo -en "\nFinding files to upload: "
find pypi-* \
-type f \
\( -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" \) \
| sort > upload.lst
TOTAL=$(wc -l < upload.lst)
echo "Done. Found ${TOTAL} files."

echo -e "\nUploading files:"
while IFS= read -r FILE
do
    if twine upload \
    --repository-url "${NEXUS_URL}" \
    --username "${NEXUS_USER}" \
    --password "${NEXUS_PASSWORD}" \
    "${FILE}" \
    >> "${REPORT}" 2>&1
    then
        echo "SUCCESS: ${FILE}" | tee -a "${REPORT}"
    else
        echo "FAILED:  ${FILE}" | tee -a "${REPORT}"
    fi
done < upload.lst

echo -e "\nSummary:"
grep -E 'SUCCESS|FAILED' "${REPORT}" || true

SUCCESS=$(grep -c '^SUCCESS:' "${REPORT}" || true)
FAILED=$(grep -c '^FAILED:' "${REPORT}" || true)

echo
echo "Total:    ${TOTAL}"
echo "Success:  ${SUCCESS}"
echo "Failed:   ${FAILED}"

echo -e "\nUpload complete. See ${REPORT} for details."

if [ "${FAILED}" -gt 0 ]; then
    exit 1
fi