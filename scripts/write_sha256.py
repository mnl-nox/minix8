#!/usr/bin/env python3
"""Write a portable SHA-256 sidecar for a file artifact."""
import hashlib
import pathlib
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: write_sha256.py FILE", file=sys.stderr)
        return 2
    path = pathlib.Path(sys.argv[1])
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    pathlib.Path(str(path) + ".sha256").write_text(f"{digest.hexdigest()}  {path.name}\n", encoding="ascii")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
