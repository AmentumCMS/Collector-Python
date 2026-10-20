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

## Remember:

Update lockfile to keep pins/reproducible:

```
pip install -r requirements-dev.txt 
pip-compile --generate-hashes -o requirements-lock.txt requirements-dev.txt
