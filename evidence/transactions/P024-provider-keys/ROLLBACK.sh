#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then echo "usage: $0 TARGET_COPY" >&2; exit 2; fi
target="$1"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
baseline="$script_dir/BASELINE_FILE.yml"
[[ -f "$target" && -f "$baseline" ]] || { echo "target or sibling baseline is missing" >&2; exit 1; }
cp -- "$baseline" "$target"
cmp -s -- "$baseline" "$target"
