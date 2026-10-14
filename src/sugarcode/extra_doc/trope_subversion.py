"""Row 271 Trope Subversion (PARTIAL): structural comparison of a story's beat sequence against a trope's
expected beat sequence. It measures where the story plays the trope straight, inverts a beat (caller-declared
opposite), substitutes another beat, omits a beat or adds extra beats. It does not judge originality, quality or
meaning: labels are compared as normalised strings supplied by the caller."""
from __future__ import annotations

MAX_BEATS = 200
MAX_LABEL = 64
MAX_INVERSIONS = 200
STATUS_NOTE = ("PARTIAL: positional and edit-distance comparison of caller-supplied beat labels only; no "
               "originality, quality, genre or meaning judgement, no story generation")


def _label(v, name):
    if not isinstance(v, str):
        raise ValueError(f"{name}: str required")
    s = v.strip().casefold()
    if not s or len(s) > MAX_LABEL:
        raise ValueError(f"{name}: 1..{MAX_LABEL} characters after trimming required")
    return s


def _beats(v, name):
    if not isinstance(v, (list, tuple)) or not 1 <= len(v) <= MAX_BEATS:
        raise ValueError(f"{name}: list of 1..{MAX_BEATS} beat labels required")
    return [_label(b, f"{name}[{i}]") for i, b in enumerate(v)]


def _inversions(v):
    if v is None:
        return {}
    if not isinstance(v, dict) or len(v) > MAX_INVERSIONS:
        raise ValueError(f"inversions: dict of at most {MAX_INVERSIONS} entries required")
    out = {}
    for k, x in v.items():
        kk, xx = _label(k, "inversions key"), _label(x, "inversions value")
        if kk in out and out[kk] != xx:
            raise ValueError(f"inversions: conflicting opposites for {kk!r}")
        out[kk] = xx
    return out


def _edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def _lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1]))
        prev = cur
    return prev[-1]


def analyze_trope_subversion(expected_beats, story_beats, inversions=None):
    exp, act, inv = _beats(expected_beats, "expected_beats"), _beats(story_beats, "story_beats"), _inversions(inversions)
    rows, counts = [], {"played": 0, "inverted": 0, "substituted": 0, "omitted": 0, "added": 0}
    for i in range(max(len(exp), len(act))):
        e = exp[i] if i < len(exp) else None
        a = act[i] if i < len(act) else None
        if e is None:
            kind = "added"
        elif a is None:
            kind = "omitted"
        elif a == e:
            kind = "played"
        elif inv.get(e) == a or inv.get(a) == e:
            kind = "inverted"
        else:
            kind = "substituted"
        counts[kind] += 1
        rows.append({"position": i, "expected": e, "actual": a, "outcome": kind})
    n = len(exp)
    changed = counts["inverted"] + counts["substituted"] + counts["omitted"]
    if counts["played"] == n and not counts["added"]:
        verdict = "played_straight"
    elif counts["inverted"] == n and not counts["added"]:
        verdict = "full_reversal"
    elif counts["played"] == 0 and counts["inverted"] == 0:
        verdict = "unrelated_to_trope"
    else:
        verdict = "mixed"
    return {"beats": rows, "counts": counts, "expected_length": n, "story_length": len(act),
            "adherence_rate": round(counts["played"] / n, 6), "subversion_rate": round(changed / n, 6),
            "subverted_beats": changed, "edit_distance": _edit_distance(exp, act),
            "common_subsequence_length": _lcs(exp, act), "verdict": verdict, "status_note": STATUS_NOTE}
