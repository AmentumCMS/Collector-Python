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


class CollectionVersionTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "python-runtimes.json").read_text())

    def discover(self, workflow, config=None):
        if not (shutil.which("bash") and shutil.which("jq")):
            self.skipTest("Collection matrix generation requires bash and jq")
        contents = (ROOT / ".github" / "workflows" / workflow).read_text()
        step = contents.split("      - name: Get current Python versions\n", 1)[1]
        script = textwrap.dedent(step.split("        run: |\n", 1)[1].split(
            "      - name: Get requirements file\n", 1
        )[0])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            runtime_config = Path(directory) / "runtimes.json"
            runtime_config.write_text(json.dumps(self.config if config is None else config))
            result = subprocess.run(
                ["bash", "-c", script],
                env={
                    **os.environ,
                    "GITHUB_OUTPUT": output.as_posix(),
                    "PYTHON_RUNTIME_CONFIG": runtime_config.as_posix(),
                },
                capture_output=True,
                text=True,
            )
            return result, output.read_text() if output.exists() else ""

    def test_matrix_uses_configured_red_hat_images(self):
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                result, output = self.discover(workflow)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(output.removeprefix("matrix=")), {
                    "include": self.config["collection_targets"],
                })

    def test_base_and_additional_rhel_streams_are_separate(self):
        targets = self.config["collection_targets"]
        labels = [target["python-version"] for target in targets]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(set(labels), {
            "rhel9-python3.9", "rhel9-python3.11", "rhel9-python3.12",
            "rhel9-python3.14", "rhel10-python3.12", "rhel10-python3.14",
        })
        for target in targets:
            major = target["python-version"].split("-", 1)[0].removeprefix("rhel")
            self.assertEqual(target["python-version"], f"rhel{major}-python{target['series']}")
            self.assertIn(f"/ubi{major}/python-{target['series'].replace('.', '')}", target["image"])

    def test_only_collection_runs_inside_ubi(self):
        for workflow in WORKFLOWS:
            contents = (ROOT / ".github" / "workflows" / workflow).read_text()
            collect = contents.split("  Collect:\n", 1)[1].split("  SecurityScan:\n", 1)[0]
            scan = contents.split("  SecurityScan:\n", 1)[1].split("  MakeISO:\n", 1)[0]
            with self.subTest(workflow=workflow):
                self.assertIn("image: ${{ matrix.image }}", collect)
                self.assertIn("options: --user 0", collect)
                self.assertIn("shell: bash", collect)
                self.assertIn("microdnf install -y git tar gzip findutils", collect)
                self.assertIn("python${{ matrix.series }} -m venv", collect)
                self.assertIn("collection-environment.txt", collect)
                self.assertIn("hash_args+=(--require-hashes)", collect)
                for job in (collect, scan):
                    self.assertIn("fromJSON(needs.Setup.outputs.matrix)", job)
                    self.assertNotIn("actions/setup-python", job)
                    self.assertIn("pypi-${{ matrix.python-version }}", job)
                self.assertNotIn("pip install", scan)

    def test_source_and_windows_versions_do_not_control_collection(self):
        self.config["source_versions"] = ["3.15.1"]
        self.config["windows_versions"] = ["3.11.9"]
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                result, output = self.discover(workflow)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(output.removeprefix("matrix="))["include"],
                                 self.config["collection_targets"])

    def test_invalid_targets_fail_without_publishing_outputs(self):
        target = self.config["collection_targets"][0]
        for workflow in WORKFLOWS:
            for targets in (
                None, [], "invalid", [target, target], [{}],
                [{**target, "series": "invalid"}],
                [{**target, "image": "ubuntu:latest"}],
                [{**target, "python-version": "../invalid"}],
            ):
                with self.subTest(workflow=workflow, targets=targets):
                    result, output = self.discover(workflow, {"collection_targets": targets})
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
