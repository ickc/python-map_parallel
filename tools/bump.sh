#!/usr/bin/env bash
# Bump the version in pyproject.toml, commit and tag it, and push: the tag
# triggers .github/workflows/release.yml, which publishes to PyPI.
#
#     pixi run -e build bump [major|minor|patch]   # default: patch
set -euo pipefail

# --frozen needs a uv.lock, which this project does not keep (pixi.lock is its
# lockfile); --no-sync writes one, which is removed
had_uv_lock=false
[[ -e uv.lock ]] && had_uv_lock=true
uv version --bump "${1:-patch}" --no-sync
version="$(uv version --short --no-sync)"
"${had_uv_lock}" || rm -f uv.lock
git commit -m "Bump version: ${version}" pyproject.toml
git tag -a "v${version}" -m "v${version}"
git push --follow-tags
