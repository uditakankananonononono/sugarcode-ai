#!/usr/bin/env bash
# Re-vendor instinct_models from shared-models at a pinned commit.
# Usage: scripts/vendor_instinct_models.sh <commit>   (needs SSH read access to shared-models)
set -euo pipefail
commit="${1:?commit required}"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
git clone -q git@github.com:uditakankananonononono/shared-models.git "$tmp/sm"
git -C "$tmp/sm" checkout -q "$commit"
full="$(git -C "$tmp/sm" rev-parse HEAD)"
root="$(cd "$(dirname "$0")/.." && pwd)"
rm -rf "$root/src/instinct_models"
cp -r "$tmp/sm/instinct_models" "$root/src/instinct_models"
find "$root/src/instinct_models" -name __pycache__ -prune -exec rm -rf {} +
printf 'Vendored copy of `instinct_models` from https://github.com/uditakankananonononono/shared-models\npinned at commit %s. Do not edit here: change it in shared-models, then re-run this script.\n' "$full" > "$root/src/instinct_models/VENDORED.md"
echo "vendored instinct_models @ $full"
