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

Both collection workflows read `python-runtimes.json`. Its `source_versions`
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
