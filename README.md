# What is this?

[![Release](https://github.com/amentumcms/Collector-Python/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/amentumcms/Collector-Python/actions/workflows/main.yml)

This is a project that automatically collects artifacts to ease in air-gapped transfer from the internet.

It runs actions on Push or on Mondays at 00:00 and creates a release.

In this case, it collects python modules and .wheels needed.

## First time?

Run the handy setup script to setup the venv and regen the lock file:
`./setup.sh` on the low side

Use `collect.sh <dir>` on the low side to collect the requirements for one runtime

Use `kickstart.sh` on the highside to setup the venv to enable uploading

Use `upload.sh` on the highside to setup the venv to enable uploading

## Python runtime versions

Collection runs on x86_64 inside public Red Hat UBI Python containers, using
Red Hat's packaged interpreters rather than Ubuntu builds from `setup-python`.
Both workflows read the `collection_targets` list in `python-runtimes.json`:

| Target | Base Python | Additional Python streams |
| --- | --- | --- |
| RHEL 9 / UBI 9 | 3.9 | 3.11, 3.12, 3.14 |
| RHEL 10 / UBI 10 | 3.12 | 3.14 |

RHEL 10 uses the published `python-312-minimal` and `python-314-minimal`
images. Python 3.13 is not included because Red Hat does not publish a matching
UBI Python image. The list is explicit: add future published streams to
`collection_targets`; the source/Windows updater does not discover UBI streams.
The `latest` image tags receive Red Hat updates, so patch versions can change
between runs. Pin image digests in the configuration when repeatability matters.

Archives include the RHEL major and Python series in their names, for example
`pypi-rhel10-python3.12`, and contain `collection-environment.txt` with the image
reference, actual interpreter version, OS release, and pip wheel compatibility
tags. Locked collection verifies package hashes during download. Requirements
are downloaded, not installed into the collector environment.

Ubuntu remains the GitHub Actions host for orchestration, SBOM/security scanning,
and ISO creation; it does not supply the collection interpreter or select wheels.
Branch unit tests also use hosted Python, without collecting packages.
UBI 9 and UBI 10 resolve against their respective glibc and Python ABIs; a RHEL 10
archive is not a substitute for a RHEL 9 archive. This targets the current UBI
release, not every earlier RHEL minor release. UBI collection does not collect
RHEL Python RPMs, OS libraries, or subscription-only packages. Source distributions
may still require compilers, development headers, and build dependencies on the
offline target. Other architectures require separate collection targets/runners.

The same configuration's `source_versions`
list selects the Python source archives; `windows_versions` independently selects
the Windows x64 installers and embeddable ZIPs. These versions can differ because
security-only Python releases may not include Windows binaries.

Branch validation tests each distinct major.minor Python series from both lists,
so adding or removing a configured series automatically updates the test matrix.
It checks shell script syntax and runs the runtime updater's standard-library
unit tests without installing the third-party packages being collected.

Edit these lists to pin releases or add/remove Python major.minor series.
To refresh them, run **Update Python runtime versions** from the Actions tab,
selecting the branch to update. The workflow finds the latest stable release in
each configured series with the required artifacts, retaining older Windows
versions when newer releases are source-only. It does not add new series or
downgrade pins, and fails without changing the file if discovery fails.

The updater commits only the configuration file to the selected branch using
`GITHUB_TOKEN`; repository rules must permit that bot to push. Protected branches
may require running it on an unprotected branch and merging the change. Bot
commits do not trigger push workflows, so dispatch collection separately when
ready.

Run the updater tests with `python -m unittest discover -s tests`.

## Remember:

Update lockfile to keep pins/reproducible:

```
pip install -r requirements-dev.txt 
pip-compile --generate-hashes -o requirements-lock.txt requirements-dev.txt
