#!/usr/bin/env python3
"""Assemble the documented MiniX8 instruction set into a bounded flat ROM."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REGS = {"A": 0, "B": 1, "C": 2, "D": 3}
SIMPLE = {
    "NOP": (0x00, 1), "ADD": (0x09, 1), "SUB": (0x0A, 1),
    "AND": (0x0B, 1), "OR": (0x0C, 1), "XOR": (0x0D, 1),
    "CMP": (0x0E, 1), "RET": (0x15, 1), "PUSH": (0x16, 1),
    "POP": (0x17, 1), "IN": (0x18, 1), "OUT": (0x19, 1),
    "HLT": (0x1A, 1), "INC": (0x1B, 1), "DEC": (0x1C, 1),
    "SHL": (0x1D, 1), "SHR": (0x1E, 1),
}
IMM = {"LDA": 1, "LDB": 2, "LDC": 3, "LDD": 4}
MEM = {"LDA": 0x05, "STA": 0x06, "LDB": 0x07, "STB": 0x08}
BRANCH = {"JMP": 0x0F, "JZ": 0x10, "JNZ": 0x11, "JC": 0x12, "JNC": 0x13, "CALL": 0x14}
MOV = {("A", "B"): 0x1F, ("B", "A"): 0x20, ("A", "C"): 0x21,
       ("C", "A"): 0x22, ("A", "D"): 0x23, ("D", "A"): 0x24}
LABEL_PREFIX = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s*(.*))?$")


class AssemblyError(ValueError):
    pass


@dataclass
class Line:
    number: int
    label: str | None
    operation: str | None
    operand: str
    address: int
    size: int


def split_source(text: str, origin: int) -> tuple[list[Line], dict[str, int], int]:
    lines: list[Line] = []
    symbols: dict[str, int] = {}
    pc = origin
    for number, raw in enumerate(text.splitlines(), 1):
        source = strip_comment(raw).strip()
        if not source:
            continue
        label = None
        match = LABEL_PREFIX.fullmatch(source)
        if match:
            label, rest = match.group(1), match.group(2) or ""
            if label in symbols:
                raise AssemblyError(f"linha {number}: rótulo duplicado: {label}")
            symbols[label] = pc
            source = rest.strip()
        if not source:
            lines.append(Line(number, label, None, "", pc, 0))
            continue
        fields = source.split(None, 1)
        op = fields[0]
        operand = fields[1] if len(fields) == 2 else ""
        op = op.upper()
        operand = operand.strip()
        if op in SIMPLE:
            size = 1
        elif op in IMM:
            size = 2 if operand.startswith("#") else 3
        elif op in MEM or op in BRANCH:
            size = 3
        elif op == "MOV":
            size = 1
        elif op in ("DB", ".BYTE"):
            size = len(parse_data(operand, number))
        else:
            raise AssemblyError(f"linha {number}: instrução desconhecida: {op}")
        if pc + size > 0x10000:
            raise AssemblyError(f"linha {number}: programa ultrapassa o espaço de 64 KiB")
        lines.append(Line(number, label, op, operand, pc, size))
        pc += size
    return lines, symbols, pc


def parse_number(token: str, symbols: dict[str, int], number: int) -> int:
    if token in symbols:
        return symbols[token]
    try:
        value = int(token, 0)
    except ValueError as exc:
        raise AssemblyError(f"linha {number}: valor ou rótulo inválido: {token}") from exc
    return value


def parse_data(value: str, number: int) -> bytes:
    parts = split_csv(value, number)
    if not value or any(not p for p in parts):
        raise AssemblyError(f"linha {number}: DB exige valores separados por vírgula")
    out = bytearray()
    for part in parts:
        if part.startswith('"') and part.endswith('"'):
            try:
                decoded = json.loads(part)
            except json.JSONDecodeError as exc:
                raise AssemblyError(f"linha {number}: string DB inválida") from exc
            if not isinstance(decoded, str):
                raise AssemblyError(f"linha {number}: DB aceita string entre aspas")
            out.extend(decoded.encode("utf-8"))
        else:
            try:
                byte = int(part, 0)
            except ValueError as exc:
                raise AssemblyError(f"linha {number}: byte inválido: {part}") from exc
            if not 0 <= byte <= 255:
                raise AssemblyError(f"linha {number}: byte fora de 0..255: {part}")
            out.append(byte)
    return bytes(out)


def split_csv(value: str, number: int) -> list[str]:
    parts: list[str] = []
    start = 0
    quoted = escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == "," and not quoted:
            parts.append(value[start:index].strip())
            start = index + 1
    if quoted or escaped:
        raise AssemblyError(f"linha {number}: string sem fechamento")
    parts.append(value[start:].strip())
    return parts


def strip_comment(line: str) -> str:
    quoted = escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == ";" and not quoted:
            return line[:index]
    return line


def encode(lines: list[Line], symbols: dict[str, int]) -> bytes:
    output = bytearray()
    for line in lines:
        if line.operation is None:
            continue
        op, operand, number = line.operation, line.operand, line.number
        if op in SIMPLE:
            opcode, _ = SIMPLE[op]
            if op in ("PUSH", "POP", "IN", "OUT", "INC", "DEC", "SHL", "SHR") and operand.upper() not in ("", "A"):
                raise AssemblyError(f"linha {number}: {op} usa o registrador A")
            if op not in ("PUSH", "POP", "IN", "OUT", "INC", "DEC", "SHL", "SHR") and operand:
                raise AssemblyError(f"linha {number}: {op} não recebe operando")
            output.append(opcode)
        elif op in IMM:
            if operand.startswith("#"):
                value = parse_number(operand[1:].strip(), symbols, number)
                if not 0 <= value <= 255:
                    raise AssemblyError(f"linha {number}: imediato fora de 0..255")
                output.extend((IMM[op], value))
            else:
                value = parse_number(operand, symbols, number)
                if not 0 <= value <= 0xFFFF:
                    raise AssemblyError(f"linha {number}: endereço fora de 0..65535")
                output.extend((MEM[op], value & 255, value >> 8))
        elif op in MEM or op in BRANCH:
            value = parse_number(operand, symbols, number)
            if not 0 <= value <= 0xFFFF:
                raise AssemblyError(f"linha {number}: endereço fora de 0..65535")
            opcode = MEM[op] if op in MEM else BRANCH[op]
            output.extend((opcode, value & 255, value >> 8))
        elif op == "MOV":
            regs = [x.strip().upper() for x in operand.split(",")]
            if len(regs) != 2 or tuple(regs) not in MOV:
                raise AssemblyError(f"linha {number}: combinação MOV inválida")
            output.append(MOV[tuple(regs)])
        else:
            output.extend(parse_data(operand, number))
    return bytes(output)


def assemble(text: str, origin: int = 0) -> bytes:
    if len(text) > 2 * 1024 * 1024 or len(text.encode("utf-8")) > 2 * 1024 * 1024:
        raise AssemblyError("fonte excede o limite de 2 MiB")
    if not 0 <= origin <= 0xFFFF:
        raise AssemblyError("origem fora de 0..65535")
    lines, symbols, _ = split_source(text, origin)
    result = encode(lines, symbols)
    if len(result) > 65536 - origin:
        raise AssemblyError("ROM excede a memória disponível a partir da origem")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--origin", type=lambda v: int(v, 0), default=0)
    args = parser.parse_args()
    try:
        if not args.input.is_file():
            raise AssemblyError("a entrada deve ser um arquivo regular")
        if args.input.stat().st_size > 2 * 1024 * 1024:
            raise AssemblyError("fonte excede o limite de 2 MiB")
        rom = assemble(args.input.read_text(encoding="utf-8"), args.origin)
        args.output.write_bytes(rom)
    except (OSError, UnicodeError, AssemblyError) as error:
        print(f"minix8-as: {error}", file=sys.stderr)
        return 1
    print(f"ROM gravada: {len(rom)} bytes em {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
