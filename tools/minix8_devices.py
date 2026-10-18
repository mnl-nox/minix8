#!/usr/bin/env python3
"""Read-only best-effort inventory of host peripherals; never opens devices."""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


LINUX_CLASSES = {
    "block": "Armazenamento", "net": "Rede", "input": "Entrada",
    "sound": "Áudio", "drm": "Vídeo/DRM", "video4linux": "Vídeo/câmera",
    "tty": "Portas seriais", "bluetooth": "Bluetooth", "ieee80211": "Wi-Fi",
    "hwmon": "Sensores", "backlight": "Tela/retroiluminação",
}


def safe_text(value: object, max_length: int = 512) -> str:
    text = str(value)
    return "".join(char if char.isprintable() else "�" for char in text)[:max_length]


def read_text(path: Path) -> str:
    try:
        return safe_text(path.read_text(encoding="utf-8", errors="replace").strip())
    except OSError:
        return ""


def linux_scan() -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    classes = Path("/sys/class")
    for key, label in LINUX_CLASSES.items():
        base = classes / key
        try:
            devices = sorted(base.iterdir(), key=lambda p: p.name.casefold())
        except OSError:
            continue
        for item in devices:
            if item.name in ("virtual", "."):
                continue
            detail = ""
            for candidate in (item / "device" / "product", item / "device" / "name", item / "name"):
                detail = read_text(candidate)
                if detail:
                    break
            found.append({"tipo": label, "nome": safe_text(item.name), "detalhe": safe_text(detail)})
    for bus, label in (("usb", "USB"), ("pci", "PCI")):
        base = Path("/sys/bus") / bus / "devices"
        try:
            devices = sorted(base.iterdir(), key=lambda p: p.name.casefold())
        except OSError:
            continue
        for item in devices:
            vendor = read_text(item / "vendor")
            product = read_text(item / "product")
            ident = " ".join(part for part in (vendor, product) if part)
            found.append({"tipo": label, "nome": safe_text(item.name), "detalhe": safe_text(ident)})
    return found[:4096]


def walk_system_profiler(value, found: list[dict[str, str]], category: str) -> None:
    if isinstance(value, dict):
        name = value.get("_name") or value.get("_name_local")
        if name:
            found.append({"tipo": safe_text(category), "nome": safe_text(name), "detalhe": safe_text(value.get("_model", ""))})
        for child in value.values():
            walk_system_profiler(child, found, category)
    elif isinstance(value, list):
        for child in value:
            walk_system_profiler(child, found, category)


def macos_scan() -> list[dict[str, str]]:
    found = []
    if not shutil.which("system_profiler"):
        return found
    sections = ("SPUSBDataType", "SPPCIDataType", "SPDisplaysDataType", "SPAudioDataType",
                "SPNetworkDataType", "SPStorageDataType", "SPBluetoothDataType", "SPCameraDataType")
    result = subprocess.run(["system_profiler", "-json", *sections], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=25, check=False)
    if result.returncode:
        return found
    data = json.loads(result.stdout)
    for key, value in data.items():
        walk_system_profiler(value, found, key.removesuffix("DataType"))
    return found[:4096]


def windows_scan() -> list[dict[str, str]]:
    found = []
    powershell = shutil.which("pwsh") or shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        return found
    script = ("Get-PnpDevice -PresentOnly | Select-Object -First 4096 Class,FriendlyName,Status "
              "| ConvertTo-Json -Compress")
    result = subprocess.run([powershell, "-NoProfile", "-NonInteractive", "-Command", script],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=25, check=False)
    if result.returncode or not result.stdout.strip():
        return found
    devices = json.loads(result.stdout)
    if isinstance(devices, dict):
        devices = [devices]
    for item in devices:
        found.append({"tipo": safe_text(item.get("Class") or "Outro"),
                      "nome": safe_text(item.get("FriendlyName") or "Dispositivo sem nome"),
                      "detalhe": safe_text(item.get("Status") or "")})
    return found[:4096]


def scan() -> list[dict[str, str]]:
    system = platform.system()
    if system == "Linux":
        return linux_scan()
    if system == "Darwin":
        return macos_scan()
    if system == "Windows":
        return windows_scan()
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emitir JSON UTF-8")
    args = parser.parse_args()
    try:
        devices = scan()
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        print(f"minix8-devices: inventário parcial: {error}", file=sys.stderr)
        devices = []
    if args.json:
        print(json.dumps({"sistema": safe_text(platform.platform()), "dispositivos": devices}, ensure_ascii=False, indent=2))
    else:
        print(f"Inventário somente leitura · {safe_text(platform.platform())}")
        if not devices:
            print("Nenhum dispositivo foi enumerado; sistema/driver pode não expor dados ao usuário.")
        for item in devices:
            suffix = f" — {item['detalhe']}" if item["detalhe"] else ""
            print(f"[{item['tipo']}] {item['nome']}{suffix}")
        print(f"\n{len(devices)} entradas · descoberta best-effort; não abre nem controla hardware.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
