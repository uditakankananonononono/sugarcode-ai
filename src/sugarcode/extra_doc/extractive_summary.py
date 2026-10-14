"""Row 559 text summarization (PARTIAL): choosing the sentences that carry the most frequent words.

text is a string of 1 to 5000 characters. A token is a maximal run of ASCII letters and digits, lower-cased; a
sentence is the stretch of text between the characters . ! ? that holds at least one token, stripped of
surrounding whitespace and with its closing mark kept when it has one. The score of a sentence is the sum, over
its distinct tokens, of how often that token occurs in the whole text. summarize(text, count) with count 1 to 10
returns the count highest-scoring sentences (ties go to the earlier sentence), shown in their original order,
with their scores. It extracts existing sentences; it does not rewrite, condense meaning, or check that the chosen
sentences are the important ones."""

MAX_TEXT = 5000
MAX_COUNT = 10
STATUS_NOTE = ("PARTIAL: extractive selection by word frequency only; no rewriting, no understanding of "
               "importance or meaning")


def _is_tok(c):
    return ("a" <= c <= "z") or ("A" <= c <= "Z") or ("0" <= c <= "9")


def _tokens(chunk):
    out = []
    cur = []
    for c in chunk + " ":
        if _is_tok(c):
            cur.append(c.lower())
        elif cur:
            out.append("".join(cur))
            cur = []
    return out


def summarize(text, count=1):
    if isinstance(count, bool) or not isinstance(count, int):
        raise ValueError("count: integer required")
    if not 1 <= count <= MAX_COUNT:
        raise ValueError(f"count: must be within 1 to {MAX_COUNT}")
    if not isinstance(text, str):
        raise ValueError("text: string required")
    if not 1 <= len(text) <= MAX_TEXT:
        raise ValueError(f"text: 1 to {MAX_TEXT} characters required")
    chunks = []
    start = 0
    for i, c in enumerate(text):
        if c in ".!?":
            chunks.append(text[start:i + 1])
            start = i + 1
    chunks.append(text[start:])
    sentences = [(ch.strip(), _tokens(ch)) for ch in chunks]
    sentences = [(s, t) for s, t in sentences if t]
    freq = {}
    for _, toks in sentences:
        for t in toks:
            freq[t] = freq.get(t, 0) + 1
    scored = [(sum(freq[t] for t in set(toks)), idx, s) for idx, (s, toks) in enumerate(sentences)]
    best = sorted(scored, key=lambda x: (-x[0], x[1]))[:count]
    best.sort(key=lambda x: x[1])
    return {"sentences": [{"index": idx, "score": sc, "text": s} for sc, idx, s in best],
            "total_sentences": len(sentences), "status_note": STATUS_NOTE}
