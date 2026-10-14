"""Row 707 Naming Conventions (PARTIAL): classifying supplied identifiers by their spelling style.

names is a list of 1..100 strings of 1..64 characters. Styles are decided by this module's own rules, tried in
this order, on ASCII letters, digits and underscore only:
  lowercase    a-z/0-9 only, starting with a letter, e.g. "name2";
  snake_case   lowercase pieces joined by single underscores, e.g. "user_id" (digits allowed in pieces);
  UPPER_SNAKE  A-Z/0-9 pieces starting with a letter, joined by single underscores or one piece, e.g. "MAX_SIZE";
  camelCase    starts with a lowercase letter and has at least one capital, no underscore, e.g. "userId";
  PascalCase   starts with a capital, has a lowercase letter, no underscore, e.g. "UserId";
  other        everything else, including any non-ASCII character, leading, trailing or doubled underscores.
check(names, expected) reports each name's style, the indexes whose style is not the expected one, and the
count per style. These rules and ranges are this module's own choices, not a language standard. It classifies
spellings only. It reads no code and says nothing about whether any name is good or consistent in a project."""
import re

MAX_NAMES, MAX_LEN = 100, 64
STYLES = ("lowercase", "snake_case", "UPPER_SNAKE", "camelCase", "PascalCase", "other")
NOT_CLAIMED = ("quality of any name", "project style guide", "meaning of the identifiers",
               "language rules", "runtime behaviour")
_RULES = (("lowercase", re.compile(r"[a-z][a-z0-9]*")),
          ("snake_case", re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")),
          ("UPPER_SNAKE", re.compile(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*")),
          ("camelCase", re.compile(r"[a-z][a-z0-9]*(?:[A-Z][A-Za-z0-9]*)+")),
          ("PascalCase", re.compile(r"[A-Z][A-Za-z0-9]*[a-z][A-Za-z0-9]*")))


def check(names, expected):
    if type(names) is not list or not 1 <= len(names) <= MAX_NAMES:
        raise ValueError(f"names: list of 1 to {MAX_NAMES} required")
    for i, n in enumerate(names):
        if type(n) is not str or not 1 <= len(n) <= MAX_LEN:
            raise ValueError(f"names[{i}]: string of 1 to {MAX_LEN} characters required")
    if type(expected) is not str or expected not in STYLES:
        raise ValueError(f"expected: one of {', '.join(STYLES)} required")
    styles = [next((s for s, rx in _RULES if rx.fullmatch(n)), "other") for n in names]
    return {"styles": styles, "mismatches": [i for i, s in enumerate(styles) if s != expected],
            "style_counts": [styles.count(s) for s in STYLES],
            "naming_validated": False, "not_claimed": NOT_CLAIMED}
