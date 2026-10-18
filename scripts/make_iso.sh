#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUTPUT=${1:-"$ROOT/dist/MiniX8-1987.iso"}
BINARIES=${2:-"$ROOT"}
ISO_TOOL=${ISO_TOOL:-}
REQUIRE_ALL_PLATFORMS=${REQUIRE_ALL_PLATFORMS:-0}

if [ -z "$ISO_TOOL" ]; then
    if command -v xorriso >/dev/null 2>&1; then ISO_TOOL=xorriso
    elif command -v genisoimage >/dev/null 2>&1; then ISO_TOOL=genisoimage
    elif command -v mkisofs >/dev/null 2>&1; then ISO_TOOL=mkisofs
    else ISO_TOOL=python3
    fi
fi

case "$ISO_TOOL" in
    xorriso|genisoimage|mkisofs|python3) ;;
    *) echo "Unsupported ISO tool: $ISO_TOOL" >&2; exit 2 ;;
esac

mkdir -p "$(dirname -- "$OUTPUT")"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT HUP INT TERM
mkdir -p "$STAGE/bin" "$STAGE/source/src" "$STAGE/source/scripts" "$STAGE/source/tests" "$STAGE/source/tools" "$STAGE/examples" "$STAGE/docs" "$STAGE/site/docs"

copy_binary() {
    source_path=$1
    destination=$2
    if [ -f "$source_path" ]; then
        cp "$source_path" "$STAGE/bin/$destination"
        case "$destination" in *.exe) ;; *) chmod 755 "$STAGE/bin/$destination" ;; esac
        return 0
    fi
    return 1
}

found=0
copy_binary "$BINARIES/minix8-linux-x86_64/minix8-linux-x86_64" "minix8-linux-x86_64" && found=$((found + 1)) || :
copy_binary "$BINARIES/minix8-macos-arm64/minix8-macos-arm64" "minix8-macos-arm64" && found=$((found + 1)) || :
copy_binary "$BINARIES/minix8-windows-x86_64/minix8-windows-x86_64.exe" "minix8-windows-x86_64.exe" && found=$((found + 1)) || :

# Accept flat artifact directories and a local `make iso` build as well.
if [ ! -f "$STAGE/bin/minix8-linux-x86_64" ]; then
    if [ -f "$BINARIES/minix8-linux-x86_64" ]; then
        copy_binary "$BINARIES/minix8-linux-x86_64" "minix8-linux-x86_64" && found=$((found + 1)) || :
    elif [ -f "$BINARIES/minix8" ]; then
        copy_binary "$BINARIES/minix8" "minix8-linux-local" && found=$((found + 1)) || :
    fi
fi
if [ ! -f "$STAGE/bin/minix8-macos-arm64" ] && [ -f "$BINARIES/minix8-macos-arm64" ]; then
    copy_binary "$BINARIES/minix8-macos-arm64" "minix8-macos-arm64" && found=$((found + 1)) || :
fi
if [ ! -f "$STAGE/bin/minix8-windows-x86_64.exe" ] && [ -f "$BINARIES/minix8-windows-x86_64.exe" ]; then
    copy_binary "$BINARIES/minix8-windows-x86_64.exe" "minix8-windows-x86_64.exe" && found=$((found + 1)) || :
fi
if [ "$found" -eq 0 ]; then
    echo "No MiniX8 executable found in $BINARIES; run make first or download release artifacts." >&2
    exit 1
fi
if [ "$REQUIRE_ALL_PLATFORMS" = 1 ] && [ "$found" -lt 3 ]; then
    echo "A release ISO requires Linux, macOS, and Windows binaries (found $found)." >&2
    exit 1
fi

cp "$ROOT/README.md" "$ROOT/LICENSE" "$ROOT/CONTRIBUTING.md" "$ROOT/SECURITY.md" "$ROOT/SECURITY_AUDIT.md" "$ROOT/START-HERE.txt" "$STAGE/"
cp "$ROOT/CMakeLists.txt" "$ROOT/Makefile" "$ROOT/Dockerfile" "$STAGE/source/"
cp "$ROOT/src/minix8.c" "$ROOT/src/minix8_core.c" "$ROOT/src/minix8_core.h" "$STAGE/source/src/"
cp "$ROOT"/scripts/*.py "$STAGE/source/scripts/"
cp "$ROOT/scripts/make_iso.sh" "$STAGE/source/scripts/"
cp "$ROOT"/tests/*.py "$STAGE/source/tests/"
cp "$ROOT"/tools/*.py "$STAGE/source/tools/"
cp "$ROOT/tools/hexrom.c" "$STAGE/source/tools/"
cp "$ROOT/scripts/START-UNIX.sh" "$STAGE/START-UNIX.sh"
cp "$ROOT/scripts/START-WINDOWS.bat" "$STAGE/START-WINDOWS.bat"
chmod 755 "$STAGE/START-UNIX.sh"
cp "$ROOT/examples/hello.hex" "$ROOT/examples/README.md" "$STAGE/examples/"
cp "$ROOT/examples/hello.asm" "$STAGE/examples/"
python3 "$ROOT/scripts/hex_to_rom.py" "$ROOT/examples/hello.hex" "$STAGE/examples/hello.rom" >/dev/null
cp "$ROOT"/docs/*.md "$STAGE/docs/"
cp "$ROOT/docs/VM-HELP.txt" "$STAGE/docs/"
cp -R "$ROOT/site/." "$STAGE/site/"
PROJECT_VERSION=$(git -C "$ROOT" describe --tags --exact-match 2>/dev/null | sed 's/^v//' || sed -n 's/^project(MiniX8 VERSION \([^ ]*\).*/\1/p' "$ROOT/CMakeLists.txt")
REPOSITORY=${GITHUB_REPOSITORY:-mnl-nox/minix8}
sed -e "s|__REPOSITORY__|${REPOSITORY}|g" -e "s|__VERSION__|${PROJECT_VERSION}|g" \
  "$ROOT/site/config.js" > "$STAGE/site/config.js"
cp "$ROOT"/docs/*.md "$STAGE/site/docs/"
cp "$ROOT/SECURITY.md" "$ROOT/SECURITY_AUDIT.md" "$STAGE/site/"

VERSION=$PROJECT_VERSION
REVISION=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || printf 'source-snapshot')
if git -C "$ROOT" diff --quiet && [ -z "$(git -C "$ROOT" status --porcelain 2>/dev/null)" ]; then
    WORKTREE=clean
else
    WORKTREE=modified-or-snapshot
fi
cat > "$STAGE/BUILD-INFO.txt" <<EOF
MiniX8 professional development image
Version: $VERSION
Source revision: $REVISION
Working tree: $WORKTREE
Architectures: host binaries are identified in bin/; VM live image is x86-64.
Encoding: UTF-8 for documentation, assembly strings and terminal text.
Integrity: verify files with MANIFEST.sha256 before use.
Scope: educational 8-bit VM, assembly lab, ROM tools and read-only host inventory.
EOF

cat > "$STAGE/ISO-README.txt" <<'EOF'
MINIX8 / RETRO-COMPUTING DEVELOPMENT LAB / EDITION 1987

This ISO9660/Joliet data image is not bootable. Extract it, verify
MANIFEST.sha256, then follow START-HERE.txt. Use START-UNIX.sh on Linux/macOS or
START-WINDOWS.bat on Windows. Add --gui for the optional Tkinter workbench.
The 1987 label is a visual homage. This package includes source, virtual ISA
assembler, ROM utilities, QA and security notes, and read-only device inventory.
For VM boot media see docs/BOOTABLE_VM.md; the live guest uses Linux/BusyBox.
EOF

(cd "$STAGE" && find . -type f ! -name MANIFEST.sha256 -print | LC_ALL=C sort | xargs sha256sum > MANIFEST.sha256)

case "$ISO_TOOL" in
    xorriso) xorriso -as mkisofs -iso-level 3 -J -R -V MINIX8_1987 -o "$OUTPUT" "$STAGE" ;;
    genisoimage) genisoimage -iso-level 3 -J -R -V MINIX8_1987 -o "$OUTPUT" "$STAGE" ;;
    mkisofs) mkisofs -iso-level 3 -J -R -V MINIX8_1987 -o "$OUTPUT" "$STAGE" ;;
    python3) python3 "$ROOT/scripts/make_iso9660.py" "$STAGE" "$OUTPUT" ;;
esac
python3 "$ROOT/scripts/write_sha256.py" "$OUTPUT"
echo "Distribution ISO created: $OUTPUT"
