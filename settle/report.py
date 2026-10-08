"""Match two ledgers on id and say whether the amounts agree."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

CENT = Decimal("0.01")


class LedgerError(Exception):
    """A ledger cannot be compared."""


@dataclass(frozen=True)
class Row:
    id: str
    amount: Decimal


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def format_money(value: Decimal) -> str:
    return f"{money(value):.2f}"


def load_ledger(path: Path) -> list[Row]:
    if not path.is_file():
        raise LedgerError(f"{path} not found")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise LedgerError(f"{path}: {exc.strerror}") from exc
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise LedgerError(f"{path}: missing header")
    fields = [(name or "").strip() for name in reader.fieldnames]
    if any(name == "" for name in fields):
        raise LedgerError(f"{path}: header has an empty column")
    required = {"id", "amount"}
    present = set(fields)
    missing = sorted(required - present)
    if missing:
        raise LedgerError(f"{path}: missing column {missing[0]}")
    extra = sorted(present - required)
    if extra:
        raise LedgerError(f"{path}: unexpected column {extra[0]}")
    rows: list[Row] = []
    seen: set[str] = set()
    for raw in reader:
        values = {key.strip(): (value or "").strip() for key, value in raw.items() if key}
        if not any(values.values()):
            continue
        try:
            item_id = values["id"]
            if item_id == "" or any(char in item_id for char in "\n\r"):
                raise LedgerError("id is empty")
            if item_id in seen:
                raise LedgerError(f"duplicate id {item_id}")
            seen.add(item_id)
            amount_text = values["amount"]
            if amount_text == "":
                raise LedgerError("amount is empty")
            try:
                amount = Decimal(amount_text)
            except InvalidOperation as exc:
                raise LedgerError("amount is not a number") from exc
            if not amount.is_finite():
                raise LedgerError("amount is not a number")
            try:
                cents = amount.quantize(CENT)
            except InvalidOperation as exc:
                raise LedgerError("amount is not a number") from exc
            if amount != cents:
                raise LedgerError("amount has more than 2 decimal places")
        except LedgerError as exc:
            raise LedgerError(f"{path}: row {reader.line_num}: {exc}") from exc
        rows.append(Row(item_id, amount))
    return rows


def labels(left: str, right: str) -> tuple[str, str]:
    left_name = Path(left).name
    right_name = Path(right).name
    if left_name == right_name:
        return left, right
    return left_name, right_name


def render_report(left_label: str, left_rows: list[Row], right_label: str, right_rows: list[Row]) -> str:
    left = {row.id: row.amount for row in left_rows}
    right = {row.id: row.amount for row in right_rows}
    matched_ids = sorted(set(left) & set(right))
    matched_total = sum((left[item_id] for item_id in matched_ids if left[item_id] == right[item_id]), Decimal(0))
    matched_count = sum(1 for item_id in matched_ids if left[item_id] == right[item_id])
    lines = [f"MATCHED {matched_count}  {format_money(matched_total)}"]
    for item_id in matched_ids:
        if left[item_id] != right[item_id]:
            lines.append(
                f"MISMATCH {item_id}  {left_label} {format_money(left[item_id])}  "
                f"{right_label} {format_money(right[item_id])}"
            )
    for item_id in sorted(set(left) - set(right)):
        lines.append(f"ONLY {left_label}  {item_id}  {format_money(left[item_id])}")
    for item_id in sorted(set(right) - set(left)):
        lines.append(f"ONLY {right_label}  {item_id}  {format_money(right[item_id])}")
    balanced = len(lines) == 1
    lines.append("BALANCE yes" if balanced else "BALANCE no")
    return "\n".join(lines) + "\n"
