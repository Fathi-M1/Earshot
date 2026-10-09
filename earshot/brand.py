"""Brand + design tokens — the single source of truth for the product name.

The name is a variable (CLAUDE.md / 01 §intro): every UI string, tile, title and
CLI help must read ``brand.name`` / ``brand.display_name`` here, which come from
``design/tokens.json``. Never hard-code "Earshot" anywhere else.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# earshot/brand.py -> repo root is one level up; design/ lives at the root.
REPO_ROOT = Path(__file__).resolve().parent.parent
TOKENS_PATH = REPO_ROOT / "design" / "tokens.json"


@lru_cache(maxsize=1)
def tokens() -> dict[str, Any]:
    """Parsed design/tokens.json (cached)."""
    with TOKENS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _brand() -> dict[str, Any]:
    return tokens().get("brand", {})


@lru_cache(maxsize=1)
def name() -> str:
    """Package/identifier name, e.g. ``earshot``."""
    return _brand().get("name", "earshot")


@lru_cache(maxsize=1)
def display_name() -> str:
    """Display name shown to users, e.g. ``Earshot``."""
    return _brand().get("displayName", name().capitalize())


def color(token: str) -> str:
    """A hex color from the token palette, e.g. ``color("forest")``."""
    return tokens()["color"][token]


def state_tile(state: str) -> dict[str, Any]:
    """Tile spec (base/band/ink/label/shape/word) for a listening state."""
    return tokens()["state"][state]


if __name__ == "__main__":  # quick manual check
    print(f"name={name()} display={display_name()} tokens={TOKENS_PATH}")
