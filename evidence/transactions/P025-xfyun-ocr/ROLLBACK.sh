#!/bin/sh
set -eu
if [ "$#" -ne 1 ]; then
  echo "usage: $0 TARGET_COPY" >&2
  exit 2
fi
target=$1
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/BASELINE_FILE.py
[ -f "$base" ] || { echo "baseline is missing" >&2; exit 1; }
cp "$base" "$target"
