#!/usr/bin/env python3
"""Validate Conventional Commit subjects in a commit range.

Merge commits are deliberately excluded: GitHub-generated merge subjects (for
example, "Merge pull request #123 ...") are not Conventional Commits, while the
non-merge commits introduced by the merge are still checked.
"""
import re
import subprocess
import sys

PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\([a-z0-9][a-z0-9._/-]*\))?!?: .{1,100}$"
)


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check_commits.py <base> <head>", file=sys.stderr)
        return 2

    base, head = sys.argv[1:]
    if not head:
        print("head SHA/ref must not be empty", file=sys.stderr)
        return 2

    # A zero BEFORE_SHA occurs on a branch's first push. Validate the newest
    # non-merge commit in that case, rather than attempting a range from zeros.
    if base and set(base) == {"0"}:
        commit_shas = git_output("rev-list", "--no-merges", "-n", "1", head).splitlines()
    elif not base:
        commit_shas = git_output("rev-list", "--no-merges", "-n", "1", head).splitlines()
    else:
        commit_shas = git_output("rev-list", "--no-merges", "--reverse", f"{base}..{head}").splitlines()

    subjects = [
        git_output("log", "-1", "--format=%s", sha)
        for sha in commit_shas
    ]
    bad = [
        subject for subject in subjects
        if not PATTERN.fullmatch(subject) or len(subject) > 100
    ]

    if bad:
        print("Invalid Conventional Commit subject(s):", file=sys.stderr)
        for subject in bad:
            print(f"  {subject}", file=sys.stderr)
        print("Expected: type(scope optional)!: summary (max. 100 characters).", file=sys.stderr)
        return 1

    print(f"Validated {len(subjects)} non-merge commit subject(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
