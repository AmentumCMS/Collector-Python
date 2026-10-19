#!/bin/bash
set -euo pipefail

: "${NEXUS_URL:?}"
: "${NEXUS_USER:?}"
: "${NEXUS_PASSWORD:?}"

command -v twine >/dev/null || {
    echo "ERROR: twine not found"
    exit 1
}

REPORT="upload.log"

: > "${REPORT}"

echo -en "\nFinding files to upload: "
find pypi \
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
        --skip-existing \
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