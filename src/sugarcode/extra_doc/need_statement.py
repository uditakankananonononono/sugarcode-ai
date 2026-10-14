"""Row 721 Assertiveness : check that a statement has the three caller-given parts, each non-blank.

parts is a tuple of exactly 3 str: (situation, need, request). Each is 1..200 characters, must contain at least
one ASCII letter or digit, and must not start or end with an ASCII space, tab or newline. The result gives the
character length of each part and the joined sentence "<situation> | <need> | <request>". Lengths and caps are
this module's own choices. It only checks the presence and shape of three strings. It does not judge whether
the words are clear, polite, firm or assertive, and understands no language."""
import re

MAX_PART = 200
LABELS = ("situation", "need", "request")
NOT_CLAIMED = ("clarity of the words", "assertiveness or tone", "politeness", "language meaning",
               "whether the need is met")
_ALNUM = re.compile(r"[A-Za-z0-9]")


def build(parts):
    if type(parts) is not tuple or len(parts) != 3:
        raise ValueError("parts: tuple of 3 str required")
    for label, p in zip(LABELS, parts):
        if type(p) is not str or not 1 <= len(p) <= MAX_PART:
            raise ValueError(f"{label}: str of 1 to {MAX_PART} characters required")
    for label, p in zip(LABELS, parts):
        if p[0] in " \t\n" or p[-1] in " \t\n":
            raise ValueError(f"{label}: no leading or trailing space, tab or newline")
        if _ALNUM.search(p) is None:
            raise ValueError(f"{label}: at least one ASCII letter or digit required")
    return {"lengths": tuple(len(p) for p in parts), "sentence": " | ".join(parts),
            "need_statement_validated": False, "not_claimed": NOT_CLAIMED}
