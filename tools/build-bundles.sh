#!/usr/bin/env bash
#
# Rebuild the zip bundles behind every "Download all" button.
#
# GitHub Pages serves static files and cannot zip a folder on request, so the
# bundles are pre-built and committed. That makes staleness the one real failure
# mode of this site: a bundle can silently lag the folder it represents. Two
# things guard against it — this script is the only way bundles are made, and it
# stamps the build date into app.js so every download button shows how old the
# bundle is.
#
# Run it from anywhere; it locates the repo itself.
#
#   ./tools/build-bundles.sh
#
# Then COMMIT both the zips and the app.js change. A rebuild that isn't committed
# is the same as no rebuild at all.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v zip >/dev/null || { echo "error: 'zip' is not installed." >&2; exit 1; }

mkdir -p downloads

# Collection -> bundle name. Add a line here when a new collection appears.
COLLECTIONS=(
  "logos:rba-logos"
  "icons:rba-icons"
  "images:rba-images"
  "templates:rba-templates"
)

for entry in "${COLLECTIONS[@]}"; do
  src="assets/${entry%%:*}"
  out="downloads/${entry##*:}.zip"

  if [ ! -d "$src" ]; then
    echo "skip  $out — $src does not exist"
    continue
  fi

  # Check for content first. zip exits non-zero with "Nothing to do!" on an empty
  # folder, and letting that noise through would train everyone to ignore this
  # script's output — which is where the staleness warnings live.
  if [ -z "$(find "$src" -type f ! -name 'README.md' ! -name '.*' -print -quit)" ]; then
    echo "empty $out — $src has no files yet, no bundle written"
    continue
  fi

  # -x excludes the folder's own instructions and macOS cruft: a README telling
  # you how to add assets is noise inside a bundle of the assets themselves.
  rm -f "$out"
  ( cd "$src" && zip -q -r "$ROOT/$out" . -x "README.md" -x ".*" -x "__MACOSX/*" )

  if [ -f "$out" ]; then
    count=$(unzip -Z1 "$out" 2>/dev/null | grep -cv '/$' || true)
    printf 'built %-32s %s file(s), %s\n' "$out" "$count" "$(du -h "$out" | cut -f1 | tr -d ' ')"
  fi
done

# Stamp the build date so the pages can show it. Kept as a single-line constant
# in app.js precisely so this substitution stays a one-liner with no templating.
STAMP="$(date +%Y-%m-%d)"
if grep -q "^    const RBA_BUNDLE_BUILT = " app.js; then
  # BSD and GNU sed disagree about -i, so write through a temp file instead.
  sed "s/^    const RBA_BUNDLE_BUILT = .*/    const RBA_BUNDLE_BUILT = '${STAMP}';/" app.js > app.js.tmp
  mv app.js.tmp app.js
  echo "stamped app.js with build date ${STAMP}"
else
  echo "warning: could not find RBA_BUNDLE_BUILT in app.js — build date not stamped" >&2
fi

echo
echo "Done. Commit the files under downloads/ together with app.js."
