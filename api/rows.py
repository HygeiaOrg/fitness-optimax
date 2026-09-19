"""Helpers for reading BigQuery rows defensively.

A BigQuery `Row` raises on an unknown column, and its numeric columns can be
NULL. Both used to surface as an opaque HTTP 500, so every route reads values
through these helpers instead of attribute access.
"""

from datetime import date, datetime
from typing import Any, Optional


def get(row: Any, name: str, default: Any = None) -> Any:
    try:
        value = row.get(name, default)
    except AttributeError:
        value = getattr(row, name, default)
    return default if value is None else value


def as_float(row: Any, name: str, default: Optional[float] = None) -> Optional[float]:
    value = get(row, name)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(row: Any, name: str, default: Optional[int] = None) -> Optional[int]:
    value = get(row, name)
    if value is None:
        return default
    try:
        # BigQuery hands back ROUND()/AVG() results as floats (e.g. 8.0).
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def as_bool(row: Any, name: str, default: bool = False) -> bool:
    value = get(row, name)
    return default if value is None else bool(value)


def as_str(row: Any, name: str, default: str = "") -> str:
    value = get(row, name)
    return default if value is None else str(value)


def as_date(row: Any, name: str) -> Optional[date]:
    value = get(row, name)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
