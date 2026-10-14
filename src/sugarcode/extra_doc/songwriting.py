"""Row 274 songwriting (PARTIAL): meter and rhyme constrained lyric search over a supplied word bank.

Checks stress-pattern tiling, rhyme-scheme agreement and verse/chorus/bridge structure only.
No meaning, imagery, singability, melody or lyrical-quality judgement is made."""
import hashlib
import re

METERS = {
    "iambic4": "01010101",
    "trochaic4": "10101010",
    "anapestic3": "001001001",
    "dactylic2": "100100",
}
SECTIONS = {"verse": "ABAB", "chorus": "AABB", "bridge": "ABBA"}
MAX_BANK = 200
MAX_WORD = 20
MAX_SECTIONS = 12
MAX_SEED = 2 ** 63 - 1
NODE_LIMIT = 100000
STATUS_NOTE = ("PARTIAL: stress-pattern, rhyme-scheme and repeat-structure constraints over the supplied word bank; "
               "no meaning, singability, melody or lyrical-quality judgement")


def _bank(v):
    if not isinstance(v, (list, tuple)) or not 2 <= len(v) <= MAX_BANK:
        raise ValueError(f"bank: list of 2..{MAX_BANK} entries required")
    out, seen = [], set()
    for i, e in enumerate(v):
        if not isinstance(e, dict) or not isinstance(e.get("word"), str):
            raise ValueError(f"bank[{i}]: dict with 'word' required")
        w = e["word"].strip().casefold()
        if not w or len(w) > MAX_WORD or not re.fullmatch(r"[a-z']+", w):
            raise ValueError(f"bank[{i}]: word must be 1..{MAX_WORD} letters a-z (apostrophe allowed)")
        if w in seen:
            raise ValueError(f"bank[{i}]: duplicate word {w!r}")
        seen.add(w)
        st = e.get("stress")
        if not isinstance(st, str) or not re.fullmatch(r"[01]{1,4}", st):
            raise ValueError(f"bank[{i}]: stress must be 1-4 characters of 0/1")
        rk = e.get("rhyme")
        if not isinstance(rk, str) or not rk.strip():
            raise ValueError(f"bank[{i}]: rhyme must be a non-empty string")
        out.append((w, st, rk.strip().casefold()))
    return out


def _rank(seed, tag, line, word):
    return hashlib.sha256(f"{seed}:{tag}:{line}:{word}".encode("utf-8")).hexdigest()


def _section(kind, tag, bank, meter, seed, nodes):
    scheme = SECTIONS[kind]
    keys, used, chosen = {}, {}, [None] * len(scheme)

    def fill(line, rest, words, end):
        nodes[0] += 1
        if nodes[0] > NODE_LIMIT:
            raise ValueError("no song found within the search limit for this bank")
        if rest == "":
            return None if words and words[-1] == end else words
        for w, st, _ in sorted(bank, key=lambda t: _rank(seed, tag, line, t[0])):
            if rest.startswith(st) and not (words and words[-1] == w):
                r = fill(line, rest[len(st):], words + [w], end)
                if r is not None:
                    return r
        return None

    def solve(line):
        if line == len(scheme):
            return True
        letter = scheme[line]
        for w, st, rk in sorted(bank, key=lambda t: _rank(seed, tag, line, t[0])):
            if not meter.endswith(st):
                continue
            if letter in keys:
                if rk != keys[letter] or any(c[-1] == w for c, L in zip(chosen[:line], scheme) if L == letter):
                    continue
                fresh = False
            else:
                if rk in used:
                    continue
                fresh = True
            body = fill(line, meter[:len(meter) - len(st)], [], w)
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
        raise ValueError(f"no {kind} satisfies the meter and rhyme scheme with the supplied bank")
    return [list(c) for c in chosen]


def write_song(structure, bank, meter="iambic4", seed=0):
    if not isinstance(structure, (list, tuple)) or not 1 <= len(structure) <= MAX_SECTIONS:
        raise ValueError(f"structure: list of 1..{MAX_SECTIONS} section names required")
    for i, s in enumerate(structure):
        if not isinstance(s, str) or s not in SECTIONS:
            raise ValueError(f"structure[{i}]: one of {sorted(SECTIONS)} required")
    if not isinstance(meter, str) or meter not in METERS:
        raise ValueError(f"meter: one of {sorted(METERS)} required")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed: int in [0, {MAX_SEED}] required")
    b = _bank(bank)
    pattern = METERS[meter]
    nodes = [0]
    cache, out, count = {}, [], {}
    for kind in structure:
        if kind == "chorus":
            tag = "chorus"
        else:
            count[kind] = count.get(kind, 0) + 1
            tag = f"{kind}{count[kind]}"
        if tag not in cache:
            cache[tag] = _section(kind, tag, b, pattern, seed, nodes)
        out.append({"section": kind, "lines": [" ".join(c) for c in cache[tag]]})
    text = "\n\n".join("\n".join(s["lines"]) for s in out)
    return {"structure": list(structure), "meter": meter, "meter_pattern": pattern, "sections": out,
            "text": text, "seed": seed, "status_note": STATUS_NOTE}
