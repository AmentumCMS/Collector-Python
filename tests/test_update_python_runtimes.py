import copy
import unittest
from unittest.mock import patch

from scripts.update_python_runtimes import Links, main, update


class RuntimeUpdateTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "source_versions": ["3.11.9", "3.12.10"],
            "windows_versions": ["3.11.9", "3.12.10"],
        }
        self.pages = {
            "": {
                "3.11.9/", "3.11.10/", "3.11.13/", "3.12.10/", "3.12.11/",
                "3.13.1/", "3.12.12rc1/", "3.12.99/",
            },
            "3.11.9/": self.artifacts("3.11.9"),
            "3.11.10/": {"Python-3.11.10.tgz"},
            "3.11.13/": {"Python-3.11.13.tgz"},
            "3.12.10/": self.artifacts("3.12.10"),
            "3.12.11/": {"Python-3.12.11.tgz", "python-3.12.11-amd64.exe"},
            "3.12.99/": {"Python-3.12.99rc1.tgz"},
        }

    @staticmethod
    def artifacts(version):
        return {
            f"Python-{version}.tgz",
            f"python-{version}-amd64.exe",
            f"python-{version}-embed-amd64.zip",
        }

    def test_source_only_releases_do_not_replace_windows_binaries(self):
        original = copy.deepcopy(self.config)
        refreshed = update(self.config, self.pages.__getitem__)
        self.assertEqual(refreshed["source_versions"], ["3.11.13", "3.12.11"])
        self.assertEqual(refreshed["windows_versions"], ["3.11.9", "3.12.10"])
        self.assertEqual(self.config, original)
        self.assertEqual(update(refreshed, self.pages.__getitem__), refreshed)

    def test_new_binary_release_updates_both_versions(self):
        self.pages["3.12.11/"] = self.artifacts("3.12.11")
        self.assertEqual(
            update(self.config, self.pages.__getitem__)["windows_versions"],
            ["3.11.9", "3.12.11"],
        )

    def test_missing_artifacts_and_downgrades_fail(self):
        self.pages["3.11.9/"] = set()
        with self.assertRaisesRegex(ValueError, "windows_versions"):
            update(self.config, self.pages.__getitem__)
        self.config["source_versions"] = ["3.11.99"]
        with self.assertRaisesRegex(ValueError, "source_versions"):
            update(self.config, self.pages.__getitem__)

    def test_invalid_config_fails_before_fetching(self):
        for invalid in ([], "3.11.9", ["3.11.9rc1"], ["../3.11.9"], [None]):
            with self.subTest(invalid=invalid):
                self.config["source_versions"] = invalid
                with self.assertRaises(ValueError):
                    update(self.config, lambda: self.fail("Unexpected network request"))

    def test_network_failure_does_not_write_configuration(self):
        with (
            patch("sys.argv", ["update_python_runtimes.py", "python-runtimes.json"]),
            patch("pathlib.Path.read_text", return_value='{"source_versions": ["3.11.9"]}'),
            patch("scripts.update_python_runtimes.update", side_effect=OSError("offline")),
            patch("pathlib.Path.write_text") as write,
        ):
            with self.assertRaises(OSError):
                main()
            write.assert_not_called()

    def test_directory_parser_collects_only_links(self):
        parser = Links()
        parser.feed('<a href="3.11.9/">release</a><a>missing</a><img src="3.12.1/">')
        self.assertEqual(parser.links, {"3.11.9/"})


if __name__ == "__main__":
    unittest.main()
