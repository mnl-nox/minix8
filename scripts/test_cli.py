#!/usr/bin/env python3
"""Black-box command-line safety and behavior checks."""
import pathlib
import subprocess
import sys
import tempfile
import unittest


PROGRAM = pathlib.Path(sys.argv.pop(1)).resolve()


class CliTests(unittest.TestCase):
    def run_cli(self, *args, input_text=None):
        return subprocess.run(
            [str(PROGRAM), *map(str, args)],
            input=input_text,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=10,
            check=False,
        )

    def test_rom_outputs_text_and_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "hello.bin"
            rom.write_bytes(bytes([0x01, ord("O"), 0x19, 0x01, ord("i"), 0x19, 0x01, ord("!"), 0x19, 0x1A]))
            result = self.run_cli("--rom", rom)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Oi!", result.stdout)
        self.assertIn("HALT", result.stdout)

    def test_origin_is_also_entry_point(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "origin.bin"
            rom.write_bytes(bytes([0x1A]))
            result = self.run_cli("--rom", rom, "--origin", "0x200")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PC=0201", result.stdout)

    def test_last_ram_byte_can_hold_a_rom(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "last-byte.bin"
            rom.write_bytes(bytes([0x1A]))
            result = self.run_cli("--rom", rom, "--origin", "0xffff")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PC=0000", result.stdout)

    def test_console_input_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "echo.bin"
            rom.write_bytes(bytes([0x18, 0x19, 0x1A]))
            result = self.run_cli("--rom", rom, input_text="Z")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Z", result.stdout)

    def test_utf8_console_bytes_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "utf8.bin"
            rom.write_bytes(bytes([0x18, 0x19, 0x18, 0x19, 0x1A]))
            result = self.run_cli("--rom", rom, input_text="é")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("é", result.stdout)

    def test_unicode_rom_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "mídia-雪.bin"
            rom.write_bytes(bytes([0x1A]))
            result = self.run_cli("--rom", rom)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_terminal_control_bytes_are_escaped_unless_raw_output_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "control.bin"
            rom.write_bytes(bytes([0x01, 0x1B, 0x19, 0x01, 0x7F, 0x19, 0x1A]))
            safe = self.run_cli("--rom", rom)
            raw = self.run_cli("--rom", rom, "--raw-output")
        self.assertIn(r"\x1B", safe.stdout)
        self.assertIn(r"\x7F", safe.stdout)
        self.assertIn("\x1b", raw.stdout)
        self.assertIn("\x7f", raw.stdout)

    def test_bad_arguments_fail_without_running(self):
        cases = [
            (("--origin", "65536"),),
            (("--origin", "0"),),
            (("--steps", "0"),),
            (("--steps", "10000001"),),
            (("--steps", "10oops"),),
            (("--rom", "missing.bin", "--origin", "-1"),),
        ]
        for (args,) in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)

    def test_invalid_opcode_returns_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "bad.bin"
            rom.write_bytes(b"\xff")
            result = self.run_cli("--rom", rom)
        self.assertEqual(result.returncode, 1)
        self.assertIn("opcode FF", result.stderr)

    def test_oversized_rom_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "oversized.bin"
            rom.write_bytes(bytes(65537))
            result = self.run_cli("--rom", rom)
        self.assertEqual(result.returncode, 1)
        # Keep this assertion ASCII-only: Windows may encode redirected stderr
        # with its active code page instead of UTF-8.
        self.assertIn("excede a", result.stderr)

    def test_empty_rom_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "empty.bin"
            rom.write_bytes(b"")
            result = self.run_cli("--rom", rom)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ROM vazia", result.stderr)

    def test_monitor_rejects_invalid_writes_and_preserves_ram_on_bad_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "oversized.bin"
            rom.write_bytes(bytes(65537))
            commands = f"set 0 165\nset 1 256\nload {rom} 0\nmem 0 2\nquit\n"
            result = self.run_cli("--monitor", input_text=commands)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Uso: set", result.stdout)
        self.assertIn("0000: A5 00", result.stdout)

    def test_retro_monitor_aliases_are_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "halt.bin"
            rom.write_bytes(bytes([0x1A]))
            result = self.run_cli("--monitor", "--rom", rom,
                                  input_text="STATUS\nd 0 1\nT 1\nR\nX\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreaterEqual(result.stdout.count("PC=0000"), 1)
        self.assertIn("0000: 1A", result.stdout)
        self.assertIn("HALT", result.stdout)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
