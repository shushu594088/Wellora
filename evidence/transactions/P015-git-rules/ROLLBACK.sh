#!/usr/bin/env sh
set -eu
if [ "$#" -ne 1 ]; then echo "usage: $0 TARGET_COPY" >&2; exit 2; fi
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BASELINE="$DIR/BASELINE_FILE"
TARGET="$1"
[ -f "$BASELINE" ] || { echo "missing baseline" >&2; exit 3; }
[ -f "$TARGET" ] || { echo "missing target" >&2; exit 4; }
cp "$BASELINE" "$TARGET"
