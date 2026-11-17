#!/bin/sh
set -eu
if [ "$#" -ne 1 ]; then
  echo "usage: $0 TARGET_COPY" >&2
  exit 2
fi
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=$1
case "$target" in /*) ;; *) target="$(pwd)/$target" ;; esac
[ -f "$script_dir/BASELINE_FILE.kt" ] || { echo "baseline missing" >&2; exit 1; }
[ -f "$target" ] || { echo "target copy missing" >&2; exit 1; }
cp "$script_dir/BASELINE_FILE.kt" "$target"
