# What is this?

[![Release](https://github.com/amentumcms/Collector-Python/actions/workflows/yarn-main.yml/badge.svg?branch=main)](https://github.com/amentumcms/Collector-Python/actions/workflows/yarn-main.yml)

This is a project that automatically collects artifacts to ease in air-gapped transfer from the internet.

It runs actions on Push or on Mondays at 00:00 and creates a release.

In this case, it collects python modules and .wheels needed.

## Remember:

Update lockfile to keep pins/reproducible:

```
pip install -r requirements-dev.txt 
pip-compile --generate-hashes -o requirements-lock.txt requirements-dev.txt
