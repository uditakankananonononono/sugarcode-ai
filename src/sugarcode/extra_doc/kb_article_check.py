"""Row 449: Knowledge Base Creation - Documents solutions.

PARTIAL: this module only checks an article record for structural
completeness: a title, at least two section bodies, and tags, each
within whole-number length limits. It makes no claim that the article
is accurate, clear, or actually solves anything.

Caps (title 1-80 chars, 2-20 sections of 1-2000 chars, 1-8 tags of
1-30 chars) are this module's own choices, not a domain standard.
"""
from __future__ import annotations

MAX_TITLE = 80
MAX_SECTIONS = 20
MAX_SECTION_LEN = 2000
MAX_TAGS = 8
MAX_TAG_LEN = 30

NOT_CLAIMED = ("accuracy", "clarity", "problem_solved")


def check(title, sections, tags):
    if type(title) is not str or not 1 <= len(title) <= MAX_TITLE:
        raise ValueError(f"title: text of 1 to {MAX_TITLE} characters required")
    if type(sections) is not tuple or not 2 <= len(sections) <= MAX_SECTIONS:
        raise ValueError(f"sections: tuple of 2 to {MAX_SECTIONS} bodies required")
    for i, s in enumerate(sections):
        if type(s) is not str or not 1 <= len(s) <= MAX_SECTION_LEN:
            raise ValueError(f"sections[{i}]: body of 1 to {MAX_SECTION_LEN} characters required")
    if type(tags) is not tuple or not 1 <= len(tags) <= MAX_TAGS:
        raise ValueError(f"tags: tuple of 1 to {MAX_TAGS} entries required")
    for i, t in enumerate(tags):
        if type(t) is not str or not 1 <= len(t) <= MAX_TAG_LEN:
            raise ValueError(f"tags[{i}]: text of 1 to {MAX_TAG_LEN} characters required")
    blank_sections = tuple(i for i in range(len(sections)) if sections[i].strip() == "")
    total_chars = len(title) + sum(len(s) for s in sections)
    return {"kb_article_check_validated": False, "not_claimed": NOT_CLAIMED,
            "section_count": len(sections), "tag_count": len(tags),
            "blank_sections": blank_sections, "total_chars": total_chars,
            "complete": len(blank_sections) == 0}
