#!/usr/bin/env sh
set -eu
target=${1:?usage: rollback.sh TARGET_COPY}
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
baseline="$script_dir/MainActivity.baseline"
if [ ! -f "$baseline" ]; then
  printf '%s\n' "missing baseline: $baseline" >&2
  exit 2
fi
cp "$baseline" "$target"
printf '%s\n' "restored $target from $baseline"
