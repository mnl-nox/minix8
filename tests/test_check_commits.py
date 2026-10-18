"""Regression tests for Conventional Commit range validation."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CHECKER = Path(__file__).resolve().parents[1] / "scripts" / "check_commits.py"


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=repo, text=True, stderr=subprocess.PIPE
    ).strip()


class CheckCommitsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "CI Test")
        git(self.repo, "config", "user.email", "ci-test@example.invalid")
        (self.repo / "file.txt").write_text("base\n", encoding="utf-8")
        git(self.repo, "add", "file.txt")
        git(self.repo, "commit", "-m", "chore: initialize test repository")
        self.base = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.temp.cleanup()

    def commit(self, message: str, content: str):
        (self.repo / "file.txt").write_text(content, encoding="utf-8")
        git(self.repo, "add", "file.txt")
        git(self.repo, "commit", "-m", message)
        return git(self.repo, "rev-parse", "HEAD")

    def check(self, base: str, head: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(CHECKER), base, head],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_merge_commit_subject_is_ignored_but_work_commits_are_checked(self):
        git(self.repo, "checkout", "-q", "-b", "feature")
        feature = self.commit("fix(core): handle edge case", "feature\n")
        git(self.repo, "checkout", "-q", "main")
        main = self.commit("docs: explain test fixture", "main\n")
        git(self.repo, "merge", "--no-ff", "feature", "-m", "Merge pull request #42 from example/feature")

        result = self.check(self.base, "HEAD")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 2 non-merge commit(s).", result.stdout)

    def test_invalid_non_merge_subject_still_fails(self):
        bad = self.commit("bad subject", "invalid\n")
        result = self.check(self.base, bad)
        self.assertEqual(result.returncode, 1)
        self.assertIn("bad subject", result.stderr)

    def test_zero_before_sha_validates_latest_non_merge_commit(self):
        self.commit("fix(cli): handle empty argument", "fixed\n")
        zero = "0" * 40
        result = self.check(zero, "HEAD")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 1 non-merge commit(s).", result.stdout)


if __name__ == "__main__":
    unittest.main()
