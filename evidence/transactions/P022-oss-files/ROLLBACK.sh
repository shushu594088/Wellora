#!/bin/sh
set -eu

target=${1:?usage: ROLLBACK.sh TARGET_COPY}
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cp -- "$script_dir/BASELINE_FILE.py" "$target"
