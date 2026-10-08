"""Command line for settle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from settle import __version__
from settle.report import LedgerError, labels, load_ledger, render_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="settle",
        description="Compare two money ledgers and say whether they balance.",
    )
    parser.add_argument("--version", action="version", version=f"settle {__version__}")
    parser.add_argument("left", help="First CSV, with columns id and amount.")
    parser.add_argument("right", help="Second CSV, with columns id and amount.")
    args = parser.parse_args(argv)
    try:
        left_rows = load_ledger(Path(args.left))
        right_rows = load_ledger(Path(args.right))
        left_label, right_label = labels(args.left, args.right)
        sys.stdout.write(render_report(left_label, left_rows, right_label, right_rows))
    except LedgerError as exc:
        print(f"settle: {exc}", file=sys.stderr)
        return 1
    return 0
