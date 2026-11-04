import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ("branch.yml", "main.yml")


@unittest.skipUnless(
    all(shutil.which(tool) for tool in ("bash", "curl", "sha256sum", "tar")),
    "Trivy installation requires bash, curl, sha256sum, and tar",
)
class TrivyInstallationTests(unittest.TestCase):
    def install(self, workflow, corrupt=False, curl_status=0, missing_checksum=False):
        contents = (ROOT / ".github" / "workflows" / workflow).read_text()
        self.assertIn("  SecurityScan:\n    runs-on: ubuntu-24.04\n", contents)
        step = contents.split("      - name: Security - Install Trivy\n", 1)[1]
        step, scan = step.split("      - name: Security - Scan SBOM with Trivy\n", 1)
        version = step.split("          TRIVY_VERSION: ", 1)[1].splitlines()[0]
        script = textwrap.dedent(step.split("        run: |\n", 1)[1])
        self.assertIn("          skip-setup-trivy: true\n", scan)
        self.assertIn("          scan-type: sbom\n", scan)
        self.assertIn("          exit-code: 0\n", scan)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            fixture = directory / "fixture.tar.gz"
            with tarfile.open(fixture, "w:gz") as archive:
                binary = b"#!/bin/sh\necho test-trivy\n"
                info = tarfile.TarInfo("trivy")
                info.mode = 0o755
                info.size = len(binary)
                archive.addfile(info, io.BytesIO(binary))
            digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
            if corrupt:
                digest = "0" * 64
            filename = f"trivy_{version}_Linux-64bit.tar.gz"
            checksums = directory / "checksums.txt"
            checksums.write_text(f"{digest}  {'other.tar.gz' if missing_checksum else filename}\n")
            output = directory / "path"
            result = subprocess.run(
                ["bash", "-c", """
curl() {
    if [ "$TEST_CURL_STATUS" != 0 ]; then
        return "$TEST_CURL_STATUS"
    fi
    case "${7}" in
        "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz")
            cp "$TEST_ARCHIVE" "${9}" ;;
        "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_checksums.txt")
            cp "$TEST_CHECKSUMS" "${9}" ;;
        *) return 99 ;;
    esac
}
""" + script],
                env={
                    **os.environ,
                    "RUNNER_TEMP": str(directory),
                    "GITHUB_PATH": str(output),
                    "TRIVY_VERSION": version,
                    "TEST_ARCHIVE": str(fixture),
                    "TEST_CHECKSUMS": str(checksums),
                    "TEST_CURL_STATUS": str(curl_status),
                },
                capture_output=True,
                text=True,
            )
            path = output.read_text().strip() if output.exists() else ""
            if result.returncode == 0:
                self.assertEqual(
                    subprocess.check_output([str(Path(path) / "trivy")], text=True),
                    "test-trivy\n",
                )
            return result, path

    def test_installs_verified_release_from_github(self):
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                result, path = self.install(workflow)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(path)

    def test_invalid_checksum_does_not_publish_binary(self):
        for workflow in WORKFLOWS:
            for options in ({"corrupt": True}, {"missing_checksum": True}):
                with self.subTest(workflow=workflow, options=options):
                    result, path = self.install(workflow, **options)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(path, "")

    def test_download_failure_does_not_publish_binary(self):
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                result, path = self.install(workflow, curl_status=6)
                self.assertEqual(result.returncode, 6)
                self.assertEqual(path, "")


if __name__ == "__main__":
    unittest.main()
