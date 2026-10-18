#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT=${1:-"$ROOT/dist/MiniX8-VM-boot.iso"}
BUSYBOX=${BUSYBOX:-$(command -v busybox || true)}
KERNEL=${KERNEL:-}
# CI runners may expose an Azure kernel in /boot that is not readable by the
# unprivileged runner. Pick the newest readable kernel instead of blindly
# selecting the final path from the version-sorted list.
if [ -z "$KERNEL" ]; then
  for candidate in $(ls -1v /boot/vmlinuz-* 2>/dev/null || true); do
    if [ -f "$candidate" ] && [ -r "$candidate" ]; then
      KERNEL=$candidate
    fi
  done
fi
GRUB_MODULES=${GRUB_MODULES:-/usr/lib/grub/x86_64-efi}
for tool in python3 gzip grub-mkimage grub-file; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Missing required tool: $tool" >&2; exit 1; }
done
[ -n "$BUSYBOX" ] && [ -x "$BUSYBOX" ] || { echo "Install BusyBox (static recommended)." >&2; exit 1; }
[ -n "$KERNEL" ] && [ -f "$KERNEL" ] && [ -r "$KERNEL" ] || { echo "No readable Linux kernel found; set KERNEL=/path/to/readable/vmlinuz." >&2; exit 1; }
[ -d "$GRUB_MODULES" ] || { echo "GRUB EFI modules not found: $GRUB_MODULES" >&2; exit 1; }
mkdir -p "$(dirname "$OUT")"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
CC=${CC:-cc}
VERSION=$(sed -n 's/^project(MiniX8 VERSION \\([^ ]*\\).*/\\1/p' "$ROOT/CMakeLists.txt")
"$CC" -static -O2 -std=c11 -Wall -Wextra -Wpedantic -o "$TMP/minix8" "$ROOT/src/minix8.c" "$ROOT/src/minix8_core.c"
"$CC" -static -O2 -std=c11 -Wall -Wextra -Wpedantic -o "$TMP/hexrom" "$ROOT/tools/hexrom.c"
python3 "$ROOT/scripts/hex_to_rom.py" "$ROOT/examples/hello.hex" "$TMP/hello.rom" >/dev/null
python3 "$ROOT/scripts/build_initramfs.py" --busybox "$BUSYBOX" --minix8 "$TMP/minix8" \
  --hexrom "$TMP/hexrom" --rom "$TMP/hello.rom" --docs "$ROOT/docs" \
  --output "$TMP/initramfs.cpio" --version "$VERSION"
mkdir -p "$TMP/iso/boot/grub" "$TMP/iso/EFI/BOOT"
cp "$KERNEL" "$TMP/iso/boot/vmlinuz"
cp "$TMP/initramfs.cpio" "$TMP/iso/boot/initramfs.cpio"
cat > "$TMP/grub.cfg" <<'EOF'
set timeout=3
set default=0
menuentry "MiniX8 1987-inspired VM Live" {
  linux /boot/vmlinuz console=tty0 rdinit=/init
  initrd /boot/initramfs.cpio
}
EOF
cp "$TMP/grub.cfg" "$TMP/iso/boot/grub/grub.cfg"
grub-mkimage -O x86_64-efi -d "$GRUB_MODULES" -p /boot/grub -c "$TMP/grub.cfg" \
  -o "$TMP/iso/EFI/BOOT/BOOTX64.EFI" part_gpt part_msdos fat iso9660 normal linux configfile search search_fs_file
grub-file --is-x86_64-efi "$TMP/iso/EFI/BOOT/BOOTX64.EFI"
if command -v grub-mkrescue >/dev/null 2>&1; then
  grub-mkrescue -o "$OUT" "$TMP/iso" >/dev/null
else
  echo "grub-mkrescue missing; local bootable ISO creation needs grub-common, grub-pc-bin, xorriso." >&2
  exit 1
fi
echo "Bootable VM ISO created: $OUT"
python3 "$ROOT/scripts/write_sha256.py" "$OUT"
