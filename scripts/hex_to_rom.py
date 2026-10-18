#!/usr/bin/env python3
"""Convert whitespace-separated hexadecimal bytes into a bounded MiniX8 ROM."""
import argparse
import pathlib
import re
import sys

MAX_ROM_SIZE = 65536
MAX_SOURCE_SIZE = 1024 * 1024


def parse_rom(source: str) -> bytes:
    if len(source.encode("utf-8")) > MAX_SOURCE_SIZE:
        raise ValueError(f"fonte excede o limite de {MAX_SOURCE_SIZE} bytes")
    values = []
    for line_number, line in enumerate(source.splitlines(), 1):
        content = line.split("#", 1)[0]
        for token in re.split(r"[\s,]+", content.strip()):
            if not token:
                continue
            candidate = token[2:] if token.lower().startswith("0x") else token
            if not re.fullmatch(r"[0-9a-fA-F]{2}", candidate):
                raise ValueError(f"linha {line_number}: byte hexadecimal inválido: {token!r}")
            values.append(int(candidate, 16))
            if len(values) > MAX_ROM_SIZE:
                raise ValueError(f"ROM excede o limite de {MAX_ROM_SIZE} bytes")
    if not values:
        raise ValueError("ROM vazia: informe ao menos um byte")
    return bytes(values)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path, help="arquivo .hex")
    parser.add_argument("output", type=pathlib.Path, help="destino binário .rom")
    args = parser.parse_args()
    try:
        if not args.input.is_file():
            raise ValueError("a entrada deve ser um arquivo regular")
        if args.input.stat().st_size > MAX_SOURCE_SIZE:
            raise ValueError(f"fonte excede o limite de {MAX_SOURCE_SIZE} bytes")
        data = parse_rom(args.input.read_text(encoding="utf-8"))
        args.output.write_bytes(data)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"hex_to_rom: {error}", file=sys.stderr)
        return 1
    print(f"ROM gravada: {len(data)} bytes → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
