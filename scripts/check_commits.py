#!/usr/bin/env python3
"""Validate Conventional Commit subjects for a Git commit range."""
import re
import subprocess
import sys

PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\([a-z0-9][a-z0-9._/-]*\))?!?: .{1,100}$"
)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check_commits.py <base> <head>", file=sys.stderr)
        return 2
    base, head = sys.argv[1:]
    if base == "0" * len(base):
        base = ""
    args = ["git", "log", "--format=%s", f"{base}..{head}"] if base else ["git", "log", "-1", "--format=%s", head]
    subjects = subprocess.check_output(args, text=True).splitlines()
    bad = [subject for subject in subjects if not PATTERN.fullmatch(subject) or len(subject) > 100]
    if bad:
        print("Invalid Conventional Commit subject(s):", file=sys.stderr)
        for subject in bad:
            print(f"  {subject}", file=sys.stderr)
        print("Expected: type(scope optional)!: summary (max. 100 characters).", file=sys.stderr)
        return 1
    print(f"Validated {len(subjects)} commit subject(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
