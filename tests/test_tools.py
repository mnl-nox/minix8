#!/usr/bin/env python3
"""Unit tests for the standalone ROM converter."""
import importlib.util
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hex_to_rom", ROOT / "scripts" / "hex_to_rom.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ISO_SPEC = importlib.util.spec_from_file_location("make_iso9660", ROOT / "scripts" / "make_iso9660.py")
ISO_MODULE = importlib.util.module_from_spec(ISO_SPEC)
ISO_SPEC.loader.exec_module(ISO_MODULE)
DEV_SPEC = importlib.util.spec_from_file_location("minix8_devices", ROOT / "tools" / "minix8_devices.py")
DEV_MODULE = importlib.util.module_from_spec(DEV_SPEC)
DEV_SPEC.loader.exec_module(DEV_MODULE)
ASM_SPEC = importlib.util.spec_from_file_location("minix8_as", ROOT / "tools" / "minix8_as.py")
ASM_MODULE = importlib.util.module_from_spec(ASM_SPEC)
sys.modules[ASM_SPEC.name] = ASM_MODULE
ASM_SPEC.loader.exec_module(ASM_MODULE)


class HexToRomTests(unittest.TestCase):
    def test_parses_comments_commas_and_prefixes(self):
        self.assertEqual(MODULE.parse_rom("01, 0x4f # letter\nff"), bytes([1, 0x4F, 0xFF]))

    def test_rejects_invalid_and_empty_input(self):
        for source in ("", "1", "xyz", "0x100"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                MODULE.parse_rom(source)

    def test_enforces_memory_limit(self):
        self.assertEqual(len(MODULE.parse_rom("00 " * 65536)), 65536)
        with self.assertRaisesRegex(ValueError, "excede"):
            MODULE.parse_rom("00 " * 65537)

    def test_limits_source_size_even_when_comments_or_whitespace_only(self):
        with self.assertRaisesRegex(ValueError, "limite"):
            MODULE.parse_rom("#" + "x" * MODULE.MAX_SOURCE_SIZE)


class AssemblerTests(unittest.TestCase):
    def test_labels_and_utf8_string(self):
        source = """start:\n LDA #0x4F\n OUT\n DB \"é\"\n JMP start\n"""
        self.assertEqual(ASM_MODULE.assemble(source), bytes([1, 0x4F, 0x19, 0xC3, 0xA9, 0x0F, 0, 0]))

    def test_cycle_counter_mnemonics(self):
        self.assertEqual(ASM_MODULE.assemble("GETCYC\\nGETCYH"), bytes([0x25, 0x26]))

    def test_utf8_string_may_contain_delimiters(self):
        self.assertEqual(ASM_MODULE.assemble('DB "ação, ok; sim"'), 'ação, ok; sim'.encode())

    def test_memory_operand_and_origin(self):
        self.assertEqual(ASM_MODULE.assemble("LDA 0x1234\nSTA 0xFFFF", 0x100),
                         bytes([0x05, 0x34, 0x12, 0x06, 0xFF, 0xFF]))

    def test_rejects_unknown_or_out_of_range_syntax(self):
        for source in ("EXEC 1", "LDA #256", "JMP 65536", "PUSH B", "MOV A,D,B"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                ASM_MODULE.assemble(source)


class DeviceInventoryTests(unittest.TestCase):
    def test_terminal_control_characters_are_sanitized(self):
        self.assertEqual(DEV_MODULE.safe_text("GPU\x1b[2J雪"), "GPU�[2J雪")

    def test_rejects_duplicate_labels_and_overflow(self):
        with self.assertRaisesRegex(ValueError, "duplicado"):
            ASM_MODULE.assemble("again: NOP\nagain: HLT")
        with self.assertRaisesRegex(ValueError, "64 KiB"):
            ASM_MODULE.assemble("DB " + ",".join(["0"] * 257), origin=0xFF00)


class Iso9660Tests(unittest.TestCase):
    @staticmethod
    def records(data):
        offset = 0
        while offset < len(data):
            length = data[offset]
            if length == 0:
                offset = ((offset // ISO_MODULE.SECTOR) + 1) * ISO_MODULE.SECTOR
                continue
            record = data[offset:offset + length]
            identifier_length = record[32]
            identifier = record[33:33 + identifier_length]
            yield record, identifier
            offset += length

    def test_iso_has_joliet_tree_and_extractable_long_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = pathlib.Path(tmp) / "stage"
            (source / "docs").mkdir(parents=True)
            (source / "START-HERE.txt").write_text("Start here", encoding="utf-8")
            (source / "docs" / "COMMANDS-MANUAL.md").write_text("Manual completo", encoding="utf-8")
            image = pathlib.Path(tmp) / "minix8.iso"
            ISO_MODULE.build_iso(source, image)
            raw = image.read_bytes()

        pvd = raw[16 * ISO_MODULE.SECTOR:17 * ISO_MODULE.SECTOR]
        joliet = raw[17 * ISO_MODULE.SECTOR:18 * ISO_MODULE.SECTOR]
        self.assertEqual(pvd[1:6], b"CD001")
        self.assertEqual(joliet[1:6], b"CD001")
        self.assertEqual(joliet[88:91], b"%/E")
        root_lba = int.from_bytes(joliet[158:162], "little")
        root_size = int.from_bytes(joliet[166:170], "little")
        root = raw[root_lba * ISO_MODULE.SECTOR:root_lba * ISO_MODULE.SECTOR + root_size]
        names = {identifier.decode("utf-16-be"): record for record, identifier in self.records(root)
                 if identifier not in (b"\0", b"\1")}
        self.assertIn("START-HERE.txt;1", names)
        docs_record = names["docs"]
        docs_lba = int.from_bytes(docs_record[2:6], "little")
        docs_size = int.from_bytes(docs_record[10:14], "little")
        docs_data = raw[docs_lba * ISO_MODULE.SECTOR:docs_lba * ISO_MODULE.SECTOR + docs_size]
        docs_entries = {identifier.decode("utf-16-be"): record for record, identifier in self.records(docs_data)
                        if identifier not in (b"\0", b"\1")}
        manual = docs_entries["COMMANDS-MANUAL.md;1"]
        manual_lba = int.from_bytes(manual[2:6], "little")
        manual_size = int.from_bytes(manual[10:14], "little")
        self.assertEqual(raw[manual_lba * ISO_MODULE.SECTOR:manual_lba * ISO_MODULE.SECTOR + manual_size], "Manual completo".encode())


if __name__ == "__main__":
    unittest.main()
