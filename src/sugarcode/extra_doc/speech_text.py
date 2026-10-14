"""Row 557 speech synthesis (PARTIAL): the text front end that turns a whole number into words to be spoken.

spell(n) takes a whole number from -1e9 to 1e9 and returns it in English words: "minus " for negatives, "zero",
tens and units joined by a hyphen from twenty-one to ninety-nine, no "and" ("one hundred five"), and the scale
words thousand, million and billion, so 1000000000 is "one billion". It also returns the word count
(whitespace-separated words; a hyphenated pair counts as one). This is text normalisation only; it does not
generate audio, choose a voice, or handle other languages, dates, currency or decimals."""

MAX_ABS = 10**9
STATUS_NOTE = ("PARTIAL: English number-to-words text normalisation only; no audio generation, voice, prosody "
               "or other languages")
ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
        "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
SCALES = [(10**9, "billion"), (10**6, "million"), (10**3, "thousand")]


def _below_thousand(n):
    parts = []
    if n >= 100:
        parts.append(ONES[n // 100] + " hundred")
        n %= 100
    if n >= 20:
        word = TENS[n // 10]
        if n % 10:
            word += "-" + ONES[n % 10]
        parts.append(word)
    elif n > 0:
        parts.append(ONES[n])
    return " ".join(parts)


def _positive(n):
    if n == 0:
        return "zero"
    parts = []
    for size, name in SCALES:
        if n >= size:
            parts.append(_below_thousand(n // size) + " " + name)
            n %= size
    if n:
        parts.append(_below_thousand(n))
    return " ".join(parts)


def spell(n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError("n: integer required")
    if not -MAX_ABS <= n <= MAX_ABS:
        raise ValueError(f"n: must be within -{MAX_ABS} to {MAX_ABS}")
    words = "minus " + _positive(-n) if n < 0 else _positive(n)
    return {"words": words, "word_count": len(words.split()), "status_note": STATUS_NOTE}
