#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SYSTEM=$(uname -s)
case "$SYSTEM" in
    Linux) BIN="$ROOT/bin/minix8-linux-x86_64"; [ -f "$BIN" ] || BIN="$ROOT/bin/minix8-linux-local" ;;
    Darwin) BIN="$ROOT/bin/minix8-macos-arm64" ;;
    *) echo "Unsupported host: $SYSTEM. Open bin/ and choose its matching executable." >&2; exit 2 ;;
esac
if [ ! -f "$BIN" ]; then echo "No binary found for $SYSTEM in $ROOT/bin" >&2; exit 1; fi
TEMP_DIR=
cleanup() { [ -z "$TEMP_DIR" ] || rm -rf "$TEMP_DIR"; }
trap cleanup EXIT HUP INT TERM
# ISO9660/Joliet alone does not store POSIX executable bits; copy if needed.
if [ ! -x "$BIN" ]; then
    TEMP_DIR=$(mktemp -d)
    cp "$BIN" "$TEMP_DIR/minix8"
    chmod 700 "$TEMP_DIR/minix8"
    BIN="$TEMP_DIR/minix8"
fi
ROM="$ROOT/examples/hello.rom"
if [ "${1:-}" = "--gui" ]; then
    command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required for the desktop GUI." >&2; exit 1; }
    python3 "$ROOT/source/tools/minix8_gui.py" --binary "$BIN" --rom "$ROM"
    exit $?
fi
"$BIN" --rom "$ROM" --monitor
