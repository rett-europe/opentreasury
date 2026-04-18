"""Accessibility-safe soft color palette for bank accounts (issue #20).

Each color is a soft pastel hex value chosen so that dark text (e.g. #1f2937)
placed on top of it meets WCAG AA contrast (≥ 4.5:1). Keeping the list short
(10 entries) is intentional: it is more than enough to distinguish accounts
for a typical NGO and avoids overwhelming the user.
"""

ACCOUNT_COLORS: tuple[str, ...] = (
    "#7BB3F0",  # soft blue
    "#88C9B9",  # soft teal
    "#A3D977",  # soft green
    "#F5D76E",  # soft yellow
    "#F5B375",  # soft orange
    "#F28B82",  # soft red
    "#F4A6C7",  # soft pink
    "#B39DDB",  # soft purple
    "#B0BEC5",  # soft gray
    "#A5DCE7",  # soft cyan
)

ALLOWED_ACCOUNT_COLORS = frozenset(c.upper() for c in ACCOUNT_COLORS)


def is_valid_account_color(value: str) -> bool:
    """Return True when the given hex color is part of the allowed palette."""
    return isinstance(value, str) and value.upper() in ALLOWED_ACCOUNT_COLORS
