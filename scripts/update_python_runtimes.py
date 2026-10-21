"""Refresh configured Python releases using the artifacts published on python.org."""

import argparse
import json
import re
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen

BASE_URL = "https://www.python.org/ftp/python/"
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+", re.ASCII)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.update(value for key, value in attrs if key == "href")


def version_key(version):
    return tuple(map(int, version.split(".")))


@lru_cache(maxsize=None)
def listing(directory=""):
    with urlopen(BASE_URL + directory, timeout=30) as response:
        page = response.read().decode("utf-8")
    parser = Links()
    parser.feed(page)
    return parser.links


def update(config, fetch=listing):
    for key in ("source_versions", "windows_versions"):
        versions = config.get(key)
        if not isinstance(versions, list) or not versions:
            raise ValueError(f"{key} must be a nonempty list")
        if any(not isinstance(v, str) or not VERSION.fullmatch(v) for v in versions):
            raise ValueError(f"{key} must contain stable major.minor.patch versions")

    available = sorted(
        {
            link[:-1]
            for link in fetch("")
            if link.endswith("/") and VERSION.fullmatch(link[:-1])
        },
        key=version_key,
        reverse=True,
    )
    result = dict(config)
    for key in ("source_versions", "windows_versions"):
        result[key] = []
        for current in config[key]:
            series = version_key(current)[:2]
            for candidate in available:
                if version_key(candidate)[:2] != series:
                    continue
                if version_key(candidate) < version_key(current):
                    continue
                files = fetch(candidate + "/")
                required = (
                    {f"Python-{candidate}.tgz"}
                    if key == "source_versions"
                    else {
                        f"python-{candidate}-amd64.exe",
                        f"python-{candidate}-embed-amd64.zip",
                    }
                )
                if required <= files:
                    result[key].append(candidate)
                    break
            else:
                raise ValueError(f"No published artifacts found for {key}: {current}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Runtime JSON configuration to update")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    refreshed = update(config)
    args.config.write_text(json.dumps(refreshed, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
