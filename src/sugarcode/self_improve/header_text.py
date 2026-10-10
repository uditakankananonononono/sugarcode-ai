"""Safe text encoding for generated-module header fields (G01 prep).

AUTHORED, NOT RUN, NOT WIRED. Standalone helper: it imports nothing from the
engine and nothing imports it yet.

Purpose: codegen._HEADER interpolates module_slug and gap_signature raw into a
triple-quoted docstring. These helpers render a value as a JSON string literal
with ensure_ascii=True on a single line, so quotes, backslashes, newlines,
U+2028/U+2029 and non-ASCII text cannot break the docstring or add lines.

This is ENCODING, not validation. Any str is accepted and none is refused:
Unicode ("módulo", "中文", "Démo_1"), the empty string, and unusual slugs all
encode. Slug rules stay where they already live (events GapEventStore._path,
proposal_preflight_r01._identity); this module does not unify or replace them.
Nothing is refused here and no type policy is introduced. A non-str is coerced
with str() BEFORE encoding, which matches what str.format did with the old raw
interpolation (None -> "None", 7 -> "7").
"""
from __future__ import annotations

import json

__all__ = ["encode_header_text", "render_header_fields"]


def encode_header_text(value: str) -> str:
    """Return `value` as one-line, ASCII-only JSON string text (with the quotes)."""
    return json.dumps(str(value), ensure_ascii=True)


def render_header_fields(module_slug: str, gap_signature: str) -> tuple[str, str]:
    """Encode both header fields; use as the values for the Module:/Gap: lines."""
    return encode_header_text(module_slug), encode_header_text(gap_signature)
