#!/usr/bin/env python3
"""Optional retro desktop front end for the MiniX8 command-line emulator."""
from __future__ import annotations

import argparse
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path


BG = "#11150f"
PANEL = "#20271c"
INK = "#0b1009"
GREEN = "#c0f477"
DIM = "#7f9863"
TEXT = "#e2ebd5"
ORANGE = "#e5a56c"
FONT = ("Courier New", 10, "bold")


class MiniX8GUI:
    def __init__(self, root: tk.Tk, binary: str, rom: str | None) -> None:
        self.root = root
        self.binary = binary
        self.rom: str | None = None
        self.process: subprocess.Popen[str] | None = None
        self.events: queue.Queue[tuple[int, str, str]] = queue.Queue(maxsize=256)
        self.device_reports: queue.Queue[str] = queue.Queue(maxsize=1)
        self.generation = 0
        self.ready = False
        self.last_output = ""
        self.memory_rows: list[str] = []
        self.capture_memory = False
        self.generated_rom_dir: tempfile.TemporaryDirectory[str] | None = None

        root.title("MINIX8  /  PERSONAL COMPUTER SYSTEM  /  1987")
        root.geometry("1080x740")
        root.minsize(820, 600)
        root.configure(bg=BG)
        root.option_add("*Font", FONT)
        self._build()
        self._start(rom)
        root.after(35, self._poll_events)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def _build(self) -> None:
        header = tk.Frame(self.root, bg=BG, padx=18, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="▣  MINIX8", bg=BG, fg=GREEN, font=("Courier New", 20, "bold")).pack(side="left")
        tk.Label(header, text="PERSONAL COMPUTER SYSTEM  ·  8-BIT  ·  1987", bg=BG, fg=DIM).pack(side="right", pady=8)

        toolbar = tk.Frame(self.root, bg=PANEL, padx=12, pady=9, highlightthickness=1, highlightbackground=GREEN)
        toolbar.pack(fill="x", padx=18, pady=(0, 12))
        self._button(toolbar, "LOAD ROM", self.choose_rom).pack(side="left", padx=(0, 7))
        self._button(toolbar, "RESET", self.reset).pack(side="left", padx=4)
        self._button(toolbar, "STEP ▶|", lambda: self.command("step 1")).pack(side="left", padx=4)
        self._button(toolbar, "RUN ▶▶", self.run).pack(side="left", padx=4)
        self._button(toolbar, "CPU INPUT", self.cpu_input).pack(side="left", padx=4)
        self._button(toolbar, "DEVICES", self.show_devices).pack(side="left", padx=4)
        tk.Label(toolbar, text="BUDGET", bg=PANEL, fg=DIM).pack(side="left", padx=(18, 5))
        self.budget = tk.StringVar(value="1000")
        tk.Entry(toolbar, textvariable=self.budget, width=9, bg=INK, fg=GREEN, insertbackground=GREEN,
                 relief="flat", highlightthickness=1, highlightbackground=DIM).pack(side="left", ipady=5)
        tk.Button(toolbar, text="REFRESH RAM", command=self.refresh_memory, bg=BG, fg=GREEN,
                  activebackground=GREEN, activeforeground=BG, relief="flat", padx=10, pady=6).pack(side="right")

        content = tk.Frame(self.root, bg=BG, padx=18)
        content.pack(fill="both", expand=True)
        left = tk.Frame(content, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right = tk.Frame(content, bg=BG, width=285)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._panel_title(left, "SYSTEM MONITOR  /  OUTPUT")
        terminal_shell = tk.Frame(left, bg=INK, highlightthickness=2, highlightbackground=DIM)
        terminal_shell.pack(fill="both", expand=True)
        self.terminal = tk.Text(terminal_shell, bg=INK, fg=GREEN, insertbackground=GREEN, wrap="word",
                                relief="flat", padx=12, pady=12, font=("Courier New", 11), state="disabled")
        scrollbar = tk.Scrollbar(terminal_shell, command=self.terminal.yview, bg=PANEL)
        self.terminal.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.terminal.pack(fill="both", expand=True)
        input_row = tk.Frame(left, bg=BG, pady=8)
        input_row.pack(fill="x")
        tk.Label(input_row, text="minix8>", bg=BG, fg=GREEN).pack(side="left", padx=(2, 8))
        self.command_text = tk.StringVar()
        entry = tk.Entry(input_row, textvariable=self.command_text, bg=INK, fg=TEXT, insertbackground=GREEN,
                         relief="flat", highlightthickness=1, highlightbackground=DIM)
        entry.pack(side="left", fill="x", expand=True, ipady=7)
        entry.bind("<Return>", lambda _event: self.send_command())
        tk.Button(input_row, text="SEND", command=self.send_command, bg=GREEN, fg=BG,
                  activebackground=TEXT, relief="flat", padx=12).pack(side="left", padx=(7, 0), ipady=5)

        self._panel_title(right, "CPU REGISTERS")
        self.reg_text = tk.Text(right, height=8, bg=INK, fg=GREEN, relief="flat", padx=12, pady=12,
                                font=("Courier New", 11, "bold"), state="disabled")
        self.reg_text.pack(fill="x", pady=(0, 14))
        self._panel_title(right, "MEMORY  /  0000")
        self.memory_text = tk.Text(right, bg=INK, fg=TEXT, relief="flat", padx=10, pady=10,
                                   font=("Courier New", 9), state="disabled", height=16)
        self.memory_text.pack(fill="both", expand=True)

        self.status = tk.StringVar(value="WAITING FOR EMULATOR…")
        footer = tk.Frame(self.root, bg=GREEN, padx=18, pady=7)
        footer.pack(fill="x", padx=18, pady=(12, 14))
        tk.Label(footer, textvariable=self.status, bg=GREEN, fg=BG, anchor="w").pack(side="left", fill="x", expand=True)
        self.rom_label = tk.Label(footer, text="NO ROM", bg=GREEN, fg=BG, anchor="e")
        self.rom_label.pack(side="right")

    @staticmethod
    def _button(parent: tk.Widget, label: str, action) -> tk.Button:
        return tk.Button(parent, text=label, command=action, bg=BG, fg=GREEN, activebackground=GREEN,
                         activeforeground=BG, relief="flat", padx=11, pady=7, cursor="hand2")

    @staticmethod
    def _panel_title(parent: tk.Widget, title: str) -> None:
        tk.Label(parent, text=f"── {title} ──", bg=BG, fg=DIM, anchor="w").pack(fill="x", pady=(4, 8))

    def _start(self, rom: str | None = None) -> None:
        self._stop()
        self.generation += 1
        token = self.generation
        self.last_output = ""
        self._set_text(self.terminal, "")
        self._set_text(self.reg_text, "A  00     B  00\nC  00     D  00\nPC 0000   SP FFFF\nFL ---\nCYCLES 0\nREADY")
        self._set_text(self.memory_text, "Press REFRESH RAM to inspect 0000–007F.")
        args = [self.binary, "--monitor"]
        if rom:
            args = [self.binary, "--rom", rom, "--monitor"]
            self.rom = rom
        else:
            self.rom = None
        try:
            self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                            errors="replace", bufsize=0)
        except OSError as error:
            messagebox.showerror("MiniX8 não iniciou", str(error))
            self.status.set("EXECUTÁVEL NÃO ENCONTRADO")
            return
        self.ready = False
        self.rom_label.configure(text=Path(rom).name if rom else "NO ROM")
        self.status.set("EMULATOR STARTING…")
        for stream_name, stream in (("stdout", self.process.stdout), ("stderr", self.process.stderr)):
            threading.Thread(target=self._read_stream, args=(token, stream_name, stream), daemon=True).start()

    def _read_stream(self, token: int, name: str, stream) -> None:
        line = ""
        prompt = ""
        try:
            while True:
                char = stream.read(1)
                if not char:
                    if line:
                        self.events.put((token, name, line))
                    break
                line += char
                if name == "stdout":
                    prompt = (prompt + char)[-8:]
                    if prompt.endswith("minix8> "):
                        line = line[:-8]
                        if line:
                            self.events.put((token, name, line))
                        self.events.put((token, "prompt", ""))
                        line = ""
                        prompt = ""
                if char == "\n":
                    self.events.put((token, name, line))
                    line = ""
                    prompt = ""
                elif len(line) >= 4096:
                    self.events.put((token, name, line))
                    line = ""
        except (OSError, ValueError):
            pass
        self.events.put((token, "exit", ""))

    def _poll_events(self) -> None:
        try:
            report = self.device_reports.get_nowait()
        except queue.Empty:
            report = None
        if report is not None:
            self._open_report("MINIX8 / HOST DEVICE INVENTORY", report)
            self.status.set("DEVICE INVENTORY READY · READ ONLY")
        while True:
            try:
                token, kind, data = self.events.get_nowait()
            except queue.Empty:
                break
            if token != self.generation:
                continue
            if kind == "prompt":
                self.ready = True
                self.status.set("READY  ·  64K RAM  ·  CPU HALTED OR WAITING")
                if self.capture_memory:
                    self._set_text(self.memory_text, "\n".join(self.memory_rows) or "NO DATA")
                    self.capture_memory = False
            elif kind == "exit":
                if self.process and self.process.poll() is not None:
                    self.ready = False
                    self.status.set(f"EMULATOR EXITED · CODE {self.process.returncode}")
            else:
                self._append_output(data, error=(kind == "stderr"))
                if self.capture_memory and re.match(r"^[0-9A-F]{4}:\s", data):
                    self.memory_rows.append(data.rstrip())
                match = re.search(r"A=([0-9A-F]{2}) B=([0-9A-F]{2}) C=([0-9A-F]{2}) D=([0-9A-F]{2})\s+PC=([0-9A-F]{4}) SP=([0-9A-F]{4})\s+FLAGS=(...)\s+CICLOS=(\d+)(?: (HALT))?", data)
                if match:
                    a, b, c, d, pc, sp, flags, cycles, halted = match.groups()
                    self._set_text(self.reg_text, f"A  {a}     B  {b}\nC  {c}     D  {d}\nPC {pc}   SP {sp}\nFL {flags}\nCYCLES {cycles}\n{'HALTED' if halted else 'RUNNING'}")
                    if not halted:
                        self.status.set("CPU RUNNING / STEP COMPLETE")
        self.root.after(35, self._poll_events)

    def _append_output(self, text: str, error: bool = False) -> None:
        if not text:
            return
        self.last_output = (self.last_output + text)[-24000:]
        self.terminal.configure(state="normal")
        self.terminal.insert("end", text, "error" if error else "normal")
        self.terminal.tag_configure("error", foreground=ORANGE)
        if len(self.last_output) > 24000:
            self.terminal.delete("1.0", "end")
            self.terminal.insert("1.0", self.last_output)
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    @staticmethod
    def _set_text(widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def command(self, command: str) -> None:
        if not self.process or not self.ready or not self.process.stdin:
            self.status.set("WAIT FOR MONITOR PROMPT OR LOAD A ROM")
            return
        try:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            self.ready = False
            self.status.set(f"COMMAND SENT  ·  {command.upper()}")
        except (BrokenPipeError, OSError):
            self.status.set("EMULATOR INPUT CLOSED")

    def send_command(self) -> None:
        command = self.command_text.get().strip()
        if not command:
            return
        if command.lower().startswith("load "):
            self.status.set("USE LOAD ROM FOR FILES WITH SPACES OR PLATFORM PATHS")
        else:
            self.command(command)
        self.command_text.set("")

    def choose_rom(self) -> None:
        path = filedialog.askopenfilename(title="Select MiniX8 ROM or source", filetypes=[("ROM/source", "*.rom *.bin *.hex *.asm"), ("All files", "*.*")])
        if path:
            extension = Path(path).suffix.lower()
            if extension in (".hex", ".asm"):
                new_rom_dir = tempfile.TemporaryDirectory(prefix="minix8-rom-")
                converted = Path(new_rom_dir.name) / "program.rom"
                converter = (Path(__file__).resolve().parent / "minix8_as.py" if extension == ".asm"
                             else Path(__file__).resolve().parents[1] / "scripts" / "hex_to_rom.py")
                result = subprocess.run([sys.executable, str(converter), path, str(converted)],
                                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
                if result.returncode:
                    messagebox.showerror("ROM conversion failed", (result.stderr or result.stdout)[:4000])
                    new_rom_dir.cleanup()
                    return
                if self.generated_rom_dir:
                    self.generated_rom_dir.cleanup()
                self.generated_rom_dir = new_rom_dir
                path = str(converted)
            self._start(path)

    def show_devices(self) -> None:
        script = Path(__file__).resolve().with_name("minix8_devices.py")
        self.status.set("SCANNING HOST DEVICE INVENTORY…")
        def scan() -> None:
            try:
                result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                                        encoding="utf-8", errors="replace", timeout=30, check=False)
                report = (result.stdout + result.stderr)[:50000]
            except (OSError, subprocess.TimeoutExpired) as error:
                report = f"Inventário indisponível: {error}"
            try:
                self.device_reports.put_nowait(report or "Nenhum dispositivo enumerado.")
            except queue.Full:
                pass
        threading.Thread(target=scan, daemon=True).start()

    def _open_report(self, title: str, report: str) -> None:
        window = tk.Toplevel(self.root)
        window.title(title)
        window.configure(bg=BG)
        shell = tk.Frame(window, bg=BG)
        shell.pack(fill="both", expand=True, padx=10, pady=10)
        scroll = tk.Scrollbar(shell)
        text = tk.Text(shell, width=90, height=28, bg=INK, fg=GREEN, wrap="none", yscrollcommand=scroll.set)
        scroll.configure(command=text.yview)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.insert("1.0", report or "Nenhum dispositivo enumerado.")
        text.configure(state="disabled")

    def run(self) -> None:
        try:
            count = int(self.budget.get(), 10)
            if not 1 <= count <= 1_000_000_000:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid run budget", "Enter an instruction limit from 1 to 1,000,000,000.")
            return
        self.command(f"run {count}")

    def refresh_memory(self) -> None:
        self.memory_rows.clear()
        self.capture_memory = True
        self.command("mem 0 128")

    def cpu_input(self) -> None:
        if not self.process or not self.process.stdin or self.ready:
            self.status.set("RUN THE ROM FIRST; CPU INPUT IS FOR AN IN INSTRUCTION")
            return
        value = simpledialog.askstring("CPU INPUT", "Enter one character for the next IN instruction:", parent=self.root)
        if value:
            character = value[0]
            try:
                self.process.stdin.write(character + "\n")
                self.process.stdin.flush()
                self.status.set("UTF-8 INPUT SENT · MULTI-BYTE CHARACTERS USE MULTIPLE IN INSTRUCTIONS")
            except (BrokenPipeError, OSError):
                self.status.set("EMULATOR INPUT CLOSED")

    def reset(self) -> None:
        self._start(self.rom)

    def _stop(self) -> None:
        if not self.process:
            return
        try:
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=0.5)
        except (subprocess.TimeoutExpired, OSError):
            self.process.kill()
        self.process = None

    def close(self) -> None:
        self._stop()
        if self.generated_rom_dir:
            self.generated_rom_dir.cleanup()
        self.root.destroy()


def find_binary(candidate: str | None) -> str:
    if candidate:
        return candidate
    name = "minix8.exe" if os.name == "nt" else "minix8"
    local = Path(__file__).resolve().parents[1] / name
    return str(local) if local.is_file() else (shutil.which(name) or name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", help="path to the compiled minix8 executable")
    parser.add_argument("--rom", help="ROM file to load at startup")
    args = parser.parse_args()
    root = tk.Tk()
    MiniX8GUI(root, find_binary(args.binary), args.rom)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
