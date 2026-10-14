"""Row 273 Poetry Generation (PARTIAL): constraint-satisfying verse built only from a caller-supplied lexicon, for
fixed forms (syllable count per line plus an end-rhyme scheme). A backtracking search with seeded, hash-ranked
candidate order finds words whose syllable counts sum to each line target and whose end words rhyme as the scheme
demands (same letter: same rhyme key and distinct words; different letters: different keys).
Syllables and rhyme keys come from caller-supplied values when given, else from a spelling heuristic (vowel groups,
silent final e) that is wrong for many English words. No meaning, imagery or quality is judged or created."""
from __future__ import annotations
import hashlib
import re

FORMS = {
    "haiku": ((5, 7, 5), "ABC"),
    "couplet": ((10, 10), "AA"),
    "limerick": ((9, 9, 6, 6, 9), "AABBA"),
    "quatrain": ((8, 8, 8, 8), "ABAB"),
    "sonnet": ((10,) * 14, "ABABCDCDEFEFGG"),
}
MAX_LEXICON = 400
MAX_WORD = 24
MAX_SEED = 2 ** 63 - 1
NODE_LIMIT = 200000
STATUS_NOTE = ("PARTIAL: syllable and rhyme constraints satisfied over the supplied lexicon with heuristic spelling "
               "rules where counts are not supplied; no meaning, imagery, originality or quality judgement")
_VOWELS = "aeiouy"


def estimate_syllables(word):
    w = re.sub(r"[^a-z]", "", word.casefold())
    if not w:
        return 0
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if len(w) > 2 and w.endswith("e") and not w.endswith(("le", "ee", "ye")) and w[-2] not in _VOWELS:
        n -= 1
    return max(n, 1)


def rhyme_key(word):
    w = re.sub(r"[^a-z]", "", word.casefold())
    if len(w) > 2 and w.endswith("e") and w[-2] not in _VOWELS:
        w = w[:-1]
    m = list(re.finditer(r"[aeiouy]+", w))
    return w[m[-1].start():] if m else w


def _lexicon(v):
    if not isinstance(v, (list, tuple)) or not 2 <= len(v) <= MAX_LEXICON:
        raise ValueError(f"lexicon: list of 2..{MAX_LEXICON} entries required")
    out, seen = [], set()
    for i, e in enumerate(v):
        if isinstance(e, str):
            e = {"word": e}
        if not isinstance(e, dict) or not isinstance(e.get("word"), str):
            raise ValueError(f"lexicon[{i}]: word string or dict with 'word' required")
        w = e["word"].strip().casefold()
        if not w or len(w) > MAX_WORD or not re.fullmatch(r"[a-z']+", w):
            raise ValueError(f"lexicon[{i}]: word must be 1..{MAX_WORD} letters a-z (apostrophe allowed)")
        if w in seen:
            raise ValueError(f"lexicon[{i}]: duplicate word {w!r}")
        seen.add(w)
        syl = e.get("syllables", estimate_syllables(w))
        if isinstance(syl, bool) or not isinstance(syl, int) or not 1 <= syl <= 6:
            raise ValueError(f"lexicon[{i}]: syllables must be an int in [1, 6]")
        rk = e.get("rhyme", rhyme_key(w))
        if not isinstance(rk, str) or not rk.strip():
            raise ValueError(f"lexicon[{i}]: rhyme must be a non-empty string")
        out.append((w, syl, rk.strip().casefold()))
    return out


def _rank(seed, line, word):
    return hashlib.sha256(f"{seed}:{line}:{word}".encode("utf-8")).hexdigest()


def generate_verse(form, lexicon, seed=0):
    if not isinstance(form, str) or form not in FORMS:
        raise ValueError(f"form: one of {sorted(FORMS)} required")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed: int in [0, {MAX_SEED}] required")
    lex = _lexicon(lexicon)
    targets, scheme = FORMS[form]
    nodes = [0]
    keys, used = {}, {}          # scheme letter -> rhyme key; rhyme key -> letter (distinct letters, distinct keys)
    chosen = [None] * len(targets)

    def fill(line, remaining, words, end):
        nodes[0] += 1
        if nodes[0] > NODE_LIMIT:
            raise ValueError("no verse found within the search limit for this lexicon")
        if remaining == 0:
            return None if words and words[-1] == end else words
        for w, s, _ in sorted(lex, key=lambda t: _rank(seed, line, t[0])):
            if s <= remaining and not (words and words[-1] == w):
                r = fill(line, remaining - s, words + [w], end)
                if r is not None:
                    return r
        return None

    def solve(line):
        if line == len(targets):
            return True
        letter = scheme[line]
        for w, s, rk in sorted(lex, key=lambda t: _rank(seed, line, t[0])):
            if letter in keys:
                if rk != keys[letter] or any(c[-1] == w for c, L in zip(chosen[:line], scheme) if L == letter):
                    continue
                fresh = False
            else:
                if rk in used:
                    continue
                fresh = True
            nodes[0] += 1
            if nodes[0] > NODE_LIMIT:
                raise ValueError("no verse found within the search limit for this lexicon")
            body = fill(line, targets[line] - s, [], w)
            if body is None:
                continue
            if fresh:
                keys[letter], used[rk] = rk, letter
            chosen[line] = body + [w]
            if solve(line + 1):
                return True
            chosen[line] = None
            if fresh:
                del keys[letter], used[rk]
        return False

    if not solve(0):
        raise ValueError("no verse satisfies this form with the supplied lexicon")
    syl = {w: s for w, s, _ in lex}
    lines = [" ".join(c) for c in chosen]
    groups = {}
    for i, c in enumerate(chosen):
        groups.setdefault(scheme[i], []).append(c[-1])
    return {"form": form, "lines": lines, "syllables_per_line": [sum(syl[w] for w in c) for c in chosen],
            "target_syllables": list(targets), "rhyme_scheme": scheme, "rhyme_groups": groups,
            "rhyme_keys": dict(keys), "text": "\n".join(lines), "seed": seed, "status_note": STATUS_NOTE}
