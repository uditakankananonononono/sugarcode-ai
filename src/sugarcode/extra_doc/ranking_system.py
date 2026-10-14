"""Row 550 ranking system: orders named items by whole-number score, highest first.

items is a list of (name, score) pairs, 1 to 200 of them. name is a non-empty string up to 40 characters, unique
across the list; score is a whole number from -1e9 to 1e9. The result lists the items by score descending, ties
broken by name in code-point order. Each row carries rank (competition ranking: equal scores share a rank and the
next rank skips, 1, 2, 2, 4) and dense_rank (no skips, 1, 2, 2, 3). Ranking orders the supplied scores only; it
does not say whether the scores measure anything worth ranking."""

MAX_ITEMS = 200
MAX_NAME = 40
MAX_SCORE = 10**9
STATUS_NOTE = ("PARTIAL: orders supplied scores only; no judgment of whether the scores measure what matters")


def rank(items):
    if type(items) not in (list, tuple):
        raise ValueError("items: list required")
    if not 1 <= len(items) <= MAX_ITEMS:
        raise ValueError(f"items: 1 to {MAX_ITEMS} entries required")
    seen = set()
    rows = []
    for i, it in enumerate(items):
        if type(it) not in (list, tuple):
            raise ValueError(f"items[{i}]: (name, score) required")
        if len(it) != 2:
            raise ValueError(f"items[{i}]: 2 entries required")
        name, score = it
        if type(name) is not str or not name or len(name) > MAX_NAME:
            raise ValueError(f"items[{i}] name: non-empty string up to {MAX_NAME} characters required")
        if type(score) is not int:
            raise ValueError(f"items[{i}] score: integer required")
        if not -MAX_SCORE <= score <= MAX_SCORE:
            raise ValueError(f"items[{i}] score: must be within -{MAX_SCORE} to {MAX_SCORE}")
        if name in seen:
            raise ValueError(f"items[{i}] name: duplicate")
        seen.add(name)
        rows.append((name, score))
    rows.sort(key=lambda r: (-r[1], r[0]))
    out = []
    dense = 0
    for pos, (name, score) in enumerate(rows):
        if pos == 0 or score != rows[pos - 1][1]:
            comp = pos + 1
            dense += 1
        out.append({"name": name, "score": score, "rank": comp, "dense_rank": dense})
    return {"ranking": out, "status_note": STATUS_NOTE}
