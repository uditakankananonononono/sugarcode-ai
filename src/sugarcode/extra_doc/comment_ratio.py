"""Row 706 Code Comments : counting blank, comment-only and other lines in supplied source lines.

lines is a list of 1..500 strings of up to 200 characters each, with no newline characters. A line is blank
when str.strip() leaves nothing (so Unicode spaces such as U+00A0 count as blank), a comment line when the first
character after str.lstrip() is "#" (the ASCII number sign only), and a code line otherwise; a trailing comment
after code does not make a line a comment line. comment_share is comments / (comments + code) as an exact
reduced fraction, or None when there are no comment or code lines. These ranges are this module's own choices.
It counts characters in supplied text. It parses no language, reads no files and says nothing about whether
the comments are useful or correct."""
from math import gcd

MAX_LINES, MAX_LINE = 500, 200
NOT_CLAIMED = ("usefulness of any comment", "correctness of any comment", "language syntax",
               "documentation quality", "runtime behaviour")


def count(lines):
    if type(lines) is not list or not 1 <= len(lines) <= MAX_LINES:
        raise ValueError(f"lines: list of 1 to {MAX_LINES} required")
    for i, s in enumerate(lines):
        if type(s) is not str or len(s) > MAX_LINE or "\n" in s or "\r" in s:
            raise ValueError(f"lines[{i}]: string of 0 to {MAX_LINE} characters without line breaks required")
    blank = sum(1 for s in lines if not s.strip())
    comment = sum(1 for s in lines if s.lstrip().startswith("#"))
    code = len(lines) - blank - comment
    share = None
    if comment or code:
        g = gcd(comment, code)
        share = (comment // g, (comment + code) // g)
    return {"blank": blank, "comment": comment, "code": code, "comment_share": share,
            "comments_validated": False, "not_claimed": NOT_CLAIMED}
