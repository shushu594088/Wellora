#!/bin/sh
set -eu
if [ "$#" -ne 1 ]; then
  echo "Usage: ROLLBACK.sh TARGET_COPY" >&2
  exit 2
fi
target=$1
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/BASELINE_FILE.py
[ -f "$base" ] || { echo "BASELINE_FILE.py is missing" >&2; exit 1; }
[ -f "$target" ] || { echo "Target copy is missing" >&2; exit 1; }
tmp="${target}.rollback.$$"
trap 'rm -f "$tmp"' EXIT HUP INT TERM
cp "$base" "$tmp"
mv "$tmp" "$target"
trap - EXIT HUP INT TERM
printf '%s\n' RESTORED_PRISTINE_BASELINE
