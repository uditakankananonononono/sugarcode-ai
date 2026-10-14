"""Row 346 transcreation (PARTIAL): measurable constraints on a recreated line of copy against its source.

Checks a candidate against the source: protected strings kept verbatim, required phrases present, forbidden terms
absent, length ratio and a character cap, and a lexical overlap (Jaccard of word sets with protected words removed)
used as a crude 'near literal' signal. The overlap is a lexical proxy, not a translation or creativity measure.
No judgment of whether the copy is persuasive, idiomatic or culturally right."""
from fractions import Fraction
import re

MAX_TEXT = 5000
MAX_ITEMS = 50
MAX_ITEM_LEN = 100
NEAR_LITERAL = Fraction(3, 4)
STATUS_NOTE = ("PARTIAL: measurable constraints and a lexical-overlap proxy only; no judgment of persuasiveness, "
               "idiom or cultural fit")


def _text(v, name):
    if not isinstance(v, str):
        raise ValueError(f"{name}: text required")
    if not v.strip():
        raise ValueError(f"{name}: must not be empty")
    if len(v) > MAX_TEXT:
        raise ValueError(f"{name}: longer than {MAX_TEXT} characters")
    return v


def _items(v, name):
    if not isinstance(v, (list, tuple)):
        raise ValueError(f"{name}: list required")
    if len(v) > MAX_ITEMS:
        raise ValueError(f"{name}: more than {MAX_ITEMS} items")
    out = []
    for x in v:
        if not isinstance(x, str) or not x.strip():
            raise ValueError(f"{name}: non-empty strings required")
        if len(x) > MAX_ITEM_LEN:
            raise ValueError(f"{name}: item longer than {MAX_ITEM_LEN} characters")
        out.append(x)
    return out


def _words(s, drop):
    return {w for w in re.findall(r"\w+", s.lower()) if w not in drop}


def check(source, candidate, protected=(), required=(), forbidden=(), max_chars=None):
    src = _text(source, "source")
    cand = _text(candidate, "candidate")
    prot = _items(protected, "protected")
    req = _items(required, "required")
    forb = _items(forbidden, "forbidden")
    if max_chars is not None:
        if isinstance(max_chars, bool) or not isinstance(max_chars, int):
            raise ValueError("max_chars: whole number required")
        if not 1 <= max_chars <= MAX_TEXT:
            raise ValueError(f"max_chars: must be within [1, {MAX_TEXT}]")
    drop = set()
    for p in prot:
        drop |= set(re.findall(r"\w+", p.lower()))
    a, b = _words(src, drop), _words(cand, drop)
    union = a | b
    overlap = Fraction(len(a & b), len(union)) if union else Fraction(0)
    missing = [p for p in prot if p not in cand]
    absent = [r for r in req if r.lower() not in cand.lower()]
    found = [f for f in forb if f.lower() in cand.lower()]
    too_long = max_chars is not None and len(cand) > max_chars
    return {"overlap": overlap, "verdict": "near_literal" if overlap >= NEAR_LITERAL else "recreated",
            "length_ratio": Fraction(len(cand), len(src)), "missing_protected": missing,
            "missing_required": absent, "forbidden_found": found, "too_long": too_long,
            "ok": not (missing or absent or found or too_long), "status": STATUS_NOTE}
