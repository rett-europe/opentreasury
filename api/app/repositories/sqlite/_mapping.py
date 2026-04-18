"""Shared low-level mapping helpers for SQLite ↔ Cosmos document parity.

These are *only* the field-level conversions every repo needs (Decimal,
JSON, datetime). The full ``_to_doc`` / ``_from_doc`` mapping for each
table lives inside the repository module that owns it (per the Phase B
B-1 decision, 2026-04-18: "Mapping lives in one place per repo.").
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any


def to_decimal(value: Any) -> Decimal | None:
    """Coerce a SQLite NUMERIC return value into a :class:`Decimal`.

    ``aiosqlite`` returns NUMERIC as :class:`str` by default; SQLAlchemy
    may also hand back :class:`int`, :class:`float`, or :class:`Decimal`
    depending on driver and dialect choices. This helper normalizes them
    all to Decimal so service-layer arithmetic stays exact.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def from_decimal(value: Any) -> Decimal | None:
    """Coerce an inbound document amount field into a :class:`Decimal`.

    Accepts Decimal, int, float, or str. Floats are routed through
    :func:`str` first so that ``0.1`` is stored as Decimal('0.1') and
    not Decimal('0.1000000000000000055511151231257827021181583404541015625').
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def loads_json(value: Any) -> Any:
    """Parse a JSON column value coming back from SQLite.

    SQLAlchemy's ``JSON`` type already deserializes for us, but the lower
    layers (raw aiosqlite cursor) hand back :class:`str`. We accept both.
    Returns ``None`` for ``None`` input.
    """
    if value is None:
        return None
    if isinstance(value, (str, bytes, bytearray)):
        return json.loads(value)
    return value


def dumps_json(value: Any) -> str | None:
    """Serialize an embedded collection for storage in a JSON column.

    Returns ``None`` for ``None`` input. Tags, notes, splitLines, and
    other embedded arrays/objects flow through here on write.
    """
    if value is None:
        return None
    return json.dumps(value, default=_json_default)


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        # JSON doesn't have a native Decimal — store as string to preserve
        # precision; consumers re-wrap in Decimal on read.
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_iso(value: Any) -> str | None:
    """Render a datetime value back to an ISO-8601 string for the doc shape."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def parse_iso(value: Any) -> datetime | None:
    """Parse an ISO-8601 string into a :class:`datetime` for SQL columns."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    # Tolerate trailing 'Z' (Cosmos convention) — Python ≥3.11 fromisoformat
    # accepts it directly; we strip for safety on older runtimes.
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def bool_from_int(value: Any) -> bool:
    """Map SQLite's 0/1 integer to a Python bool for the document shape."""
    if value is None:
        return False
    return bool(int(value))


__all__ = [
    "bool_from_int",
    "dumps_json",
    "from_decimal",
    "loads_json",
    "parse_iso",
    "to_decimal",
    "to_iso",
]
