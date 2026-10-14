"""Row 561 information extraction: pulling dates and percentages out of plain text by fixed patterns.

text is a string of 1 to 3000 characters. A date is the exact shape YYYY-MM-DD (ASCII digits, two hyphens) with no
ASCII digit immediately before or after it, whose year is 1 to 9999, month 1 to 12 and day valid in the Gregorian
calendar for that month and year (so 2024-02-29 is found and 2023-02-29 is not). A percentage is a maximal run of 1
to 3 ASCII digits directly followed by "%"; a longer run is ignored. extract(text) returns the dates as
(position, text, year, month, day) in order and the percentages as (position, value). Positions are 0-based
character offsets of the first digit. Fixed patterns find what is written in this shape; they do not understand
other date formats, relative dates, or what a number refers to."""

MAX_TEXT = 3000
STATUS_NOTE = ("PARTIAL: fixed YYYY-MM-DD and N% patterns only; no other formats, no relative dates and no "
               "understanding of what the numbers refer to")
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _digit(c):
    return "0" <= c <= "9"


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def extract(text):
    if not isinstance(text, str):
        raise ValueError("text: string required")
    if not 1 <= len(text) <= MAX_TEXT:
        raise ValueError(f"text: 1 to {MAX_TEXT} characters required")
    n = len(text)
    dates = []
    for i in range(n - 9):
        chunk = text[i:i + 10]
        shape = all(_digit(chunk[k]) for k in (0, 1, 2, 3, 5, 6, 8, 9)) and chunk[4] == "-" and chunk[7] == "-"
        if not shape:
            continue
        if i > 0 and _digit(text[i - 1]):
            continue
        if i + 10 < n and _digit(text[i + 10]):
            continue
        y, m, d = int(chunk[0:4]), int(chunk[5:7]), int(chunk[8:])
        if not (y >= 1 and 1 <= m <= 12):
            continue
        last = DAYS[m - 1] + (1 if m == 2 and _leap(y) else 0)
        if 1 <= d <= last:
            dates.append((i, chunk, y, m, d))
    percents = []
    i = 0
    while i < n:
        if not _digit(text[i]):
            i += 1
            continue
        j = i
        while j < n and _digit(text[j]):
            j += 1
        if j - i <= 3 and j < n and text[j] == "%":
            percents.append((i, int(text[i:j])))
        i = j
    return {"dates": dates, "percentages": percents, "status_note": STATUS_NOTE}
