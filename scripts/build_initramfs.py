#!/usr/bin/env python3
"""Build a small newc initramfs for the MiniX8 VM image."""
import argparse
import os
from pathlib import Path
import stat
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--busybox", required=True, type=Path)
    parser.add_argument("--minix8", required=True, type=Path)
    parser.add_argument("--hexrom", required=True, type=Path)
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument("--docs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", default="1.0.0")
    args = parser.parse_args()
    root = args.output.parent / "initramfs-root"
    if root.exists():
        import shutil
        shutil.rmtree(root)
    for d in ("bin", "dev", "proc", "sys", "tmp", "root", "usr/share/minix8/docs", "usr/share/minix8/examples"):
        (root / d).mkdir(parents=True, exist_ok=True)
    init = '''#!/bin/ash
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
export HOME=/root TERM=${TERM:-linux} PATH=/bin:/usr/bin
clear 2>/dev/null || true
echo 'MINIX8 VM LIVE / 1987-inspired 8-bit computer'
echo 'Linux + BusyBox host environment; MiniX8 is the 8-bit virtual CPU.'
echo 'Type HELP for commands, MINIX8 --monitor to start, or poweroff to stop.'
echo
exec /bin/ash -i -l
'''
    (root / "init").write_text(init)
    os.chmod(root / "init", 0o755)
    (root / "etc").mkdir()
    (root / "etc/minix8-version").write_text(f"MiniX8 {args.version} VM live image\n")
    profile = "alias HELP='cat /usr/share/minix8/docs/VM-HELP.txt'\nalias help='cat /usr/share/minix8/docs/VM-HELP.txt'\nalias RUN='minix8 --rom /usr/share/minix8/examples/hello.rom --monitor'\nalias run='minix8 --rom /usr/share/minix8/examples/hello.rom --monitor'\nalias DIR='ls -la'\nalias CLS='clear'\nalias VER='cat /etc/minix8-version'\nalias EXIT='poweroff'\nalias DEVICES='devices'\necho 'READY.'\n"
    (root / "etc/profile").write_text(profile)
    for source, dest in ((args.busybox, "bin/busybox"), (args.minix8, "bin/minix8"), (args.hexrom, "bin/hexrom")):
        import shutil
        shutil.copy2(source, root / dest)
        os.chmod(root / dest, 0o755)
        result = subprocess.run(["ldd", str(source)], text=True, capture_output=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                fields = line.strip().split()
                library = fields[2] if len(fields) >= 3 and fields[1] == "=>" else (fields[0] if fields and fields[0].startswith("/") else None)
                if library and Path(library).exists():
                    target = root / library.lstrip("/")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists():
                        shutil.copy2(library, target)
    for applet in ("ash", "sh", "ls", "cat", "cp", "mv", "rm", "mkdir", "pwd", "clear", "mount", "dmesg", "uname", "reboot", "poweroff", "hexdump", "vi", "grep", "find", "head", "tail", "wc", "date", "echo"):
        (root / "bin" / applet).symlink_to("busybox")
    devices = "#!/bin/ash\necho 'Dispositivos publicados pelo kernel Linux neste guest:'\nfor class in block net input sound drm video4linux tty bluetooth ieee80211 hwmon; do\n  path=/sys/class/$class\n  [ -d \"$path\" ] || continue\n  for device in \"$path\"/*; do\n    [ -e \"$device\" ] || continue\n    echo \"[$class] ${device##*/}\"\n  done\ndone\nfor bus in usb pci; do\n  path=/sys/bus/$bus/devices\n  [ -d \"$path\" ] || continue\n  for device in \"$path\"/*; do\n    [ -e \"$device\" ] || continue\n    echo \"[$bus] ${device##*/}\"\n  done\ndone\necho 'Inventário somente leitura; o guest só vê dispositivos apresentados pela VM.'\n"
    (root / "bin/devices").write_text(devices)
    os.chmod(root / "bin/devices", 0o755)
    import shutil
    shutil.copy2(args.rom, root / "usr/share/minix8/examples/hello.rom")
    shutil.copy2(args.docs / "VM-HELP.txt", root / "usr/share/minix8/docs/VM-HELP.txt")
    for doc in ("USER_GUIDE.md", "COMMANDS.md", "ISA.md", "ERRORS.md", "BOOTABLE_VM.md"):
        source = args.docs / doc
        if source.exists():
            shutil.copy2(source, root / "usr/share/minix8/docs/" / doc)
    entries = []
    for path in sorted(root.rglob("*")):
        rel = "./" + str(path.relative_to(root))
        mode = (stat.S_IFLNK | 0o777) if path.is_symlink() else ((stat.S_IFDIR | 0o755) if path.is_dir() else (stat.S_IFREG | stat.S_IMODE(path.stat().st_mode)))
        data = os.readlink(path).encode() if path.is_symlink() else (path.read_bytes() if path.is_file() else b"")
        entries.append((rel, mode, data))
    entries.append(("TRAILER!!!", 0, b""))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as out:
        ino = 1
        for name, mode, data in entries:
            encoded = name.encode() + b"\0"
            fields = (ino, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(encoded), 0)
            header = b"070701" + b"".join(f"{x:08x}".encode() for x in fields)
            out.write(header + encoded)
            out.write(b"\0" * ((- (len(header) + len(encoded))) % 4))
            out.write(data)
            out.write(b"\0" * ((-len(data)) % 4))
            ino += 1
    import gzip
    raw = args.output.read_bytes()
    args.output.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))


if __name__ == "__main__":
    main()
