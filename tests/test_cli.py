"""The compare command is the product. These tests run it."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = """\
MATCHED 2  150.00
MISMATCH inv-3  payments.csv 40.00  deposits.csv 40.50
ONLY payments.csv  inv-9  12.00
ONLY deposits.csv  inv-8  5.00
BALANCE no
"""


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "settle", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class SettleCommandTest(unittest.TestCase):
    def test_sample_ledgers_match_the_readme(self) -> None:
        result = run(["fixtures/payments.csv", "fixtures/deposits.csv"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, SAMPLE)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(SAMPLE.strip(), readme)
        self.assertNotIn("40.00", result.stdout.splitlines()[0])

    def test_same_files_print_the_same_report_twice(self) -> None:
        args = ["fixtures/payments.csv", "fixtures/deposits.csv"]
        first = run(args)
        second = run(args)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertIn("BALANCE no", first.stdout)

    def test_equal_ledgers_balance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            left = Path(tmp) / "left.csv"
            right = Path(tmp) / "right.csv"
            left.write_text("amount,id\n20.00,b\n5.50,a\n", encoding="utf-8")
            right.write_text("id,amount\na,5.50\nb,20.00\n", encoding="utf-8")
            result = run([str(left), str(right)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "MATCHED 2  25.50\nBALANCE yes\n")

    def test_duplicate_id_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "left.csv"
            other = Path(tmp) / "right.csv"
            path.write_text("id,amount\na,1.00\na,2.00\n", encoding="utf-8")
            other.write_text("id,amount\na,1.00\n", encoding="utf-8")
            result = run([str(path), str(other)])
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate id a", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_refunds_match_when_both_sides_are_negative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            left = Path(tmp) / "left.csv"
            right = Path(tmp) / "right.csv"
            left.write_text("id,amount\nref, -4.00\n", encoding="utf-8")
            right.write_text("id,amount\nref,-4.00\n", encoding="utf-8")
            result = run([str(left), str(right)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("MATCHED 1  -4.00", result.stdout)
        self.assertIn("BALANCE yes", result.stdout)


if __name__ == "__main__":
    unittest.main()
