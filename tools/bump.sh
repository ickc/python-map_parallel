#!/usr/bin/env bash
# Bump the version in pyproject.toml, commit and tag it, and push: the tag
# triggers .github/workflows/release.yml, which publishes to PyPI.
#
#     pixi run -e build bump [major|minor|patch]   # default: patch
set -euo pipefail

# --frozen: rewrite pyproject.toml only, without locking (pixi.lock is this
# project's lockfile). Reading the version back takes no --frozen, which there
# needs a uv.lock; without it, uv neither locks nor syncs.
uv version --bump "${1:-patch}" --frozen
version="$(uv version --short)"
git commit -m "Bump version: ${version}" pyproject.toml
git tag -a "v${version}" -m "v${version}"
git push --follow-tags
