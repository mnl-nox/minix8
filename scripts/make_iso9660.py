#!/usr/bin/env python3
"""Build a small ISO9660/Joliet data disc using only the Python standard library."""
from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path
import re
import struct

SECTOR = 2048
SYSTEM_ID = b"MINIX8"
VOLUME_ID = "MINIX8_1987"


def both16(value: int) -> bytes:
    return struct.pack("<H", value) + struct.pack(">H", value)


def both32(value: int) -> bytes:
    return struct.pack("<I", value) + struct.pack(">I", value)


def sectors(length: int) -> int:
    return (length + SECTOR - 1) // SECTOR


class Entry:
    def __init__(self, name: str, path: Path | None, parent: "Entry | None" = None):
        self.name = name
        self.path = path
        self.parent = parent
        self.children: list[Entry] = []
        self.is_dir = path is None or path.is_dir()
        self.size = 0 if self.is_dir else path.stat().st_size  # type: ignore[union-attr]
        self.extent = 0
        self.joliet_extent = 0
        self.joliet_size = 0
        self.pvd_name = ""
        self.number = 0

    def dirs(self) -> list["Entry"]:
        out = [self] if self.is_dir else []
        for child in self.children:
            out.extend(child.dirs())
        return out

    def files(self) -> list["Entry"]:
        out = [self] if not self.is_dir else []
        for child in self.children:
            out.extend(child.files())
        return out


def load_tree(root: Path) -> Entry:
    top = Entry("", None)

    def visit(directory: Entry, source: Path) -> None:
        for path in sorted(source.iterdir(), key=lambda value: value.name.casefold()):
            if path.is_symlink():
                raise ValueError(f"symlinks are not supported in ISO staging: {path}")
            if not path.is_file() and not path.is_dir():
                continue
            child = Entry(path.name, path if path.is_file() else None, directory)
            directory.children.append(child)
            if child.is_dir:
                visit(child, path)

    visit(top, root)
    return top


def name_joliet(entry: Entry) -> bytes:
    name = entry.name if entry.is_dir else entry.name + ";1"
    return name.encode("utf-16-be")


def entry_extent(entry: Entry, joliet: bool = False) -> int:
    return entry.joliet_extent if joliet and entry.is_dir else entry.extent


def entry_size(entry: Entry, joliet: bool = False) -> int:
    return entry.joliet_size if joliet and entry.is_dir else entry.size


def assign_primary_names(directory: Entry) -> None:
    used: set[str] = set()
    counter = 1
    for child in directory.children:
        if child.is_dir:
            base = re.sub(r"[^A-Za-z0-9_]", "_", child.name).upper()
            candidate = base[:8] if len(base) <= 8 else ""
        else:
            stem, dot, ext = child.name.rpartition(".")
            if not dot:
                stem, ext = child.name, ""
            stem_clean = re.sub(r"[^A-Za-z0-9_]", "_", stem).upper()
            ext_clean = re.sub(r"[^A-Za-z0-9_]", "_", ext).upper()
            candidate = f"{stem_clean}.{ext_clean};1" if len(stem_clean) <= 8 and len(ext_clean) <= 3 else ""
        if not candidate or candidate in used:
            while True:
                candidate = (f"D{counter:07d}" if child.is_dir else f"F{counter:07d}.DAT;1")
                counter += 1
                if candidate not in used:
                    break
        child.pvd_name = candidate
        used.add(candidate)
        if child.is_dir:
            assign_primary_names(child)


def iso_date() -> bytes:
    return bytes((126, 1, 1, 0, 0, 0, 0))  # 2026-01-01 00:00 UTC


def directory_record(identifier: bytes, extent: int, size: int, is_dir: bool) -> bytes:
    length = 33 + len(identifier) + (1 if len(identifier) % 2 == 0 else 0)
    record = bytearray(length)
    record[0] = length
    record[1] = 0
    record[2:10] = both32(extent)
    record[10:18] = both32(size)
    record[18:25] = iso_date()
    record[25] = 2 if is_dir else 0
    record[26:28] = b"\0\0"
    record[28:32] = both16(1)
    record[32] = len(identifier)
    record[33:33 + len(identifier)] = identifier
    return bytes(record)


def directory_stream(entry: Entry, joliet: bool) -> bytes:
    dot = directory_record(b"\0", entry_extent(entry, joliet), entry_size(entry, joliet), True)
    parent = entry.parent if entry.parent is not None else entry
    dotdot = directory_record(b"\1", entry_extent(parent, joliet), entry_size(parent, joliet), True)
    records = [dot, dotdot]
    for child in entry.children:
        identifier = name_joliet(child) if joliet else child.pvd_name.encode("ascii")
        records.append(directory_record(identifier, entry_extent(child, joliet), entry_size(child, joliet), child.is_dir))
    out = bytearray()
    for record in records:
        offset = len(out) % SECTOR
        if offset + len(record) > SECTOR:
            out.extend(b"\0" * (SECTOR - offset))
        out.extend(record)
    return bytes(out).ljust(sectors(len(out)) * SECTOR, b"\0")


def path_table(directories: list[Entry], joliet: bool, big_endian: bool = False) -> bytes:
    out = bytearray()
    for entry in directories:
        name = b"\0" if entry.parent is None else (name_joliet(entry) if joliet else entry.pvd_name.encode("ascii"))
        parent_number = 1 if entry.parent is None else entry.parent.number
        out.extend(bytes((len(name), 0)))
        out.extend(struct.pack(">I" if big_endian else "<I", entry_extent(entry, joliet)))
        out.extend(struct.pack(">H" if big_endian else "<H", parent_number))
        out.extend(name)
        if len(name) % 2:
            out.append(0)
    return bytes(out)


def root_record(root: Entry, joliet: bool) -> bytes:
    return directory_record(b"\0", entry_extent(root, joliet), entry_size(root, joliet), True)


def descriptor_text(text: str, width: int, joliet: bool) -> bytes:
    if joliet:
        value = text.encode("utf-16-be")
        space = b"\0 "
    else:
        value = text.encode("ascii")
        space = b" "
    if len(value) > width:
        raise ValueError(f"volume descriptor text too long: {text}")
    padding = width - len(value)
    if joliet and padding % 2:
        raise ValueError("Joliet descriptor field is not an even number of bytes")
    return value + space * (padding // len(space))


def volume_descriptor(kind: int, total_sectors: int, root: Entry, pt_size: int,
                      l_path: int, m_path: int, joliet: bool = False) -> bytes:
    data = bytearray(SECTOR)
    data[0:7] = bytes((kind,)) + b"CD001" + b"\1"
    data[8:40] = descriptor_text(SYSTEM_ID.decode("ascii"), 32, joliet)
    data[40:72] = descriptor_text(VOLUME_ID, 32, joliet)
    data[80:88] = both32(total_sectors)
    data[120:124] = both16(1)
    data[124:128] = both16(1)
    data[128:132] = both16(SECTOR)
    data[132:140] = both32(pt_size)
    data[140:144] = struct.pack("<I", l_path)
    data[148:152] = struct.pack(">I", m_path)
    data[156:190] = root_record(root, joliet)
    data[190:318] = descriptor_text("MINIX8 DISTRIBUTION", 128, joliet)
    data[318:446] = descriptor_text("MINIX8 PROJECT", 128, joliet)
    data[446:574] = descriptor_text("MINIX8 CODE CONTRIBUTORS", 128, joliet)
    data[574:702] = descriptor_text("MINIX8 C11 VIRTUAL MACHINE", 128, joliet)
    for offset in (813, 830, 847, 864):
        data[offset:offset + 17] = b"2026010100000000\0"
    data[881] = 1
    if joliet:
        data[88:91] = b"%/E"
    return bytes(data)


def build_iso(source: Path, output: Path) -> None:
    tree = load_tree(source)
    assign_primary_names(tree)
    primary_dirs = tree.dirs()
    joliet_dirs = primary_dirs
    for index, directory in enumerate(primary_dirs, 1):
        directory.number = index

    # Volume descriptors occupy blocks 16–18; each path table starts at a sector.
    p_lba_l, p_mba_l, j_lba_l, j_mba_l = 19, 20, 21, 22
    primary_l = path_table(primary_dirs, False)
    primary_m = path_table(primary_dirs, False, True)
    joliet_l = path_table(joliet_dirs, True)
    joliet_m = path_table(joliet_dirs, True, True)
    if any(len(table) > SECTOR for table in (primary_l, primary_m, joliet_l, joliet_m)):
        raise ValueError("path table exceeds supported one-sector limit")
    cursor = 23

    # Directory sizes are independent of extents. Assign extents to both namespace trees.
    for directory in primary_dirs:
        placeholder = directory_stream(directory, False)
        directory.size = len(placeholder)
        directory.extent = cursor
        cursor += sectors(directory.size)
    for directory in joliet_dirs:
        placeholder = directory_stream(directory, True)
        directory.joliet_size = len(placeholder)
        directory.joliet_extent = cursor
        cursor += sectors(directory.joliet_size)

    primary_l = path_table(primary_dirs, False)
    primary_m = path_table(primary_dirs, False, True)
    joliet_l = path_table(joliet_dirs, True)
    joliet_m = path_table(joliet_dirs, True, True)

    files = tree.files()
    for entry in files:
        entry.extent = cursor
        cursor += sectors(entry.size)
    total_sectors = cursor

    image_size = total_sectors * SECTOR
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as image:
        image.truncate(image_size)

        def put(lba: int, data: bytes) -> None:
            image.seek(lba * SECTOR)
            image.write(data)

        put(16, volume_descriptor(1, total_sectors, tree, len(primary_l), p_lba_l, p_mba_l))
        # Joliet descriptor points at its own directory tree.
        put(17, volume_descriptor(2, total_sectors, tree, len(joliet_l), j_lba_l, j_mba_l, True))
        put(18, bytes((255,)) + b"CD001" + b"\1" + bytes(SECTOR - 7))
        put(p_lba_l, primary_l.ljust(sectors(len(primary_l)) * SECTOR, b"\0"))
        put(p_mba_l, primary_m.ljust(sectors(len(primary_m)) * SECTOR, b"\0"))
        put(j_lba_l, joliet_l.ljust(sectors(len(joliet_l)) * SECTOR, b"\0"))
        put(j_mba_l, joliet_m.ljust(sectors(len(joliet_m)) * SECTOR, b"\0"))

        for directory in primary_dirs:
            put(directory.extent, directory_stream(directory, False))
        for directory in joliet_dirs:
            put(directory.joliet_extent, directory_stream(directory, True))
        for entry in files:
            with entry.path.open("rb") as content:  # type: ignore[union-attr]
                image.seek(entry.extent * SECTOR)
                while chunk := content.read(1024 * 1024):
                    image.write(chunk)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="staged folder to write")
    parser.add_argument("output", type=Path, help="destination ISO file")
    args = parser.parse_args()
    try:
        build_iso(args.source, args.output)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    print(f"ISO9660/Joliet image created: {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
