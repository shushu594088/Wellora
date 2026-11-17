#!/bin/sh
set -eu
[ "$#" -eq 1 ] || { echo "usage: $0 TARGET_COPY" >&2; exit 2; }
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=$1
case "$target" in /*) ;; *) target="$(pwd)/$target" ;; esac
cp "$dir/BASELINE_FILE.py" "$target"
