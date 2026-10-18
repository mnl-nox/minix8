#!/usr/bin/env python3
"""Behavior checks for the standalone boot-image ROM converter."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

PROGRAM = pathlib.Path(sys.argv.pop(1)).resolve()


class HexRomTests(unittest.TestCase):
    def test_valid_input_and_comments(self):
        with tempfile.TemporaryDirectory() as temp:
            source = pathlib.Path(temp) / "program.hex"
            target = pathlib.Path(temp) / "program.rom"
            source.write_text("# header\n01, 0x4f 19\nff # tail\n", encoding="ascii")
            result = subprocess.run([str(PROGRAM), str(source), str(target)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(target.read_bytes(), bytes((1, 0x4F, 0x19, 0xFF)))

    def test_unicode_file_names(self):
        with tempfile.TemporaryDirectory() as temp:
            source = pathlib.Path(temp) / "entrada-ação.hex"
            target = pathlib.Path(temp) / "saída-雪.rom"
            source.write_text("1A", encoding="utf-8")
            result = subprocess.run([str(PROGRAM), str(source), str(target)], text=True,
                                    encoding="utf-8", errors="replace", capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(target.read_bytes(), b"\x1a")

    def test_rejects_invalid_without_creating_output(self):
        with tempfile.TemporaryDirectory() as temp:
            source = pathlib.Path(temp) / "bad.hex"
            target = pathlib.Path(temp) / "bad.rom"
            source.write_text("01 GG 02", encoding="ascii")
            result = subprocess.run([str(PROGRAM), str(source), str(target)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(target.exists())

    def test_size_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            source = pathlib.Path(temp) / "large.hex"
            target = pathlib.Path(temp) / "large.rom"
            source.write_text("00 " * 65537, encoding="ascii")
            result = subprocess.run([str(PROGRAM), str(source), str(target)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("exceeds 65536", result.stderr)
            self.assertFalse(target.exists())

    def test_source_size_limit_applies_to_comments_too(self):
        with tempfile.TemporaryDirectory() as temp:
            source = pathlib.Path(temp) / "large.hex"
            target = pathlib.Path(temp) / "large.rom"
            source.write_bytes(b"#" + b"x" * (1024 * 1024))
            result = subprocess.run([str(PROGRAM), str(source), str(target)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("input exceeds", result.stderr)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
