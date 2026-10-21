import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ("branch.yml", "main.yml")


@unittest.skipUnless(
    shutil.which("bash") and shutil.which("jq") and Path("/etc/os-release").exists(),
    "Collection version discovery requires bash, jq, and /etc/os-release",
)
class CollectionVersionTests(unittest.TestCase):
    def setUp(self):
        self.os_version = subprocess.check_output(
            ["bash", "-c", '. /etc/os-release; echo "$VERSION_ID"'], text=True
        ).strip()
        self.manifest = [
            self.release("3.9.25"),
            self.release("3.11.14"),
            self.release("3.12.12"),
            self.release("3.13.9"),
            self.release("3.13.10"),
        ]

    def release(self, version, stable=True, **file_overrides):
        return {
            "version": version,
            "stable": stable,
            "files": [{
                "platform": "linux",
                "platform_version": self.os_version,
                "arch": "x64",
                **file_overrides,
            }],
        }

    def discover(self, workflow, manifest=None, curl_status=0):
        contents = (ROOT / ".github" / "workflows" / workflow).read_text()
        step = contents.split("      - name: Get current Python versions\n", 1)[1]
        script = textwrap.dedent(step.split("        run: |\n", 1)[1].split(
            "      - name: Get requirements file\n", 1
        )[0])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = subprocess.run(
                ["bash", "-c", """
curl() {
    printf '%s' "$TEST_MANIFEST"
    return "$TEST_CURL_STATUS"
}
""" + script],
                env={
                    **os.environ,
                    "GITHUB_OUTPUT": str(output),
                    "TEST_MANIFEST": json.dumps(self.manifest) if manifest is None else manifest,
                    "TEST_CURL_STATUS": str(curl_status),
                },
                capture_output=True,
                text=True,
            )
            return result, output.read_text() if output.exists() else ""

    def test_selects_latest_supported_stable_build_for_each_series(self):
        self.manifest.extend([
            self.release("3.13.17", platform_version="unsupported"),
            self.release("3.13.18", platform="darwin"),
            self.release("3.13.19", arch="arm64"),
            self.release("3.13.20", arch="x64-freethreaded"),
            self.release("3.13.21rc1", stable=False),
            self.release("3.14.1"),
        ])
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                result, output = self.discover(workflow)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output.splitlines(), [
                    "v309=3.9.25", "v311=3.11.14", "v312=3.12.12", "v313=3.13.10",
                ])

    def test_missing_series_fails_without_publishing_outputs(self):
        self.manifest = [r for r in self.manifest if not r["version"].startswith("3.13.")]
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                result, output = self.discover(workflow)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("No stable Python 3.13 x64 build available", result.stderr)
                self.assertEqual(output, "")

    def test_invalid_manifest_and_download_failure_fail_without_outputs(self):
        for workflow in WORKFLOWS:
            for manifest, curl_status in (
                ("not json", 0),
                ("[]", 0),
                ("[]", 22),
                (json.dumps(self.manifest + ["malformed entry"]), 0),
            ):
                with self.subTest(workflow=workflow, manifest=manifest, status=curl_status):
                    result, output = self.discover(workflow, manifest, curl_status)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
