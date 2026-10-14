"""Row 297 facial animation: prototype matching of supplied action-unit intensities.

Scores a face pose against a fixed table of simplified action-unit prototypes by cosine similarity.
The table is a coarse convention, not a validated emotion model. No claim about what any face conveys to a viewer."""
import math
from fractions import Fraction

PROTOTYPES = {
    "happiness": (6, 12),
    "sadness": (1, 4, 15),
    "surprise": (1, 2, 5, 26),
    "anger": (4, 5, 7, 23),
    "fear": (1, 2, 4, 5, 20, 26),
    "disgust": (9, 15, 16),
}
KNOWN_AUS = tuple(sorted({a for v in PROTOTYPES.values() for a in v}))
MAX_INTENSITY = 5
MATCH_COS_SQ = Fraction(9, 25)          # cosine 0.6
STATUS_NOTE = ("PARTIAL: cosine match of supplied action-unit intensities to a coarse fixed prototype table; "
               "not a validated emotion model, no claim about viewer perception")


def _intensity(v, name):
    if isinstance(v, bool) or not isinstance(v, (int, float, Fraction)):
        raise ValueError(f"{name}: number required")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not 0 <= v <= MAX_INTENSITY:
        raise ValueError(f"{name}: must be within [0, {MAX_INTENSITY}]")
    return Fraction(v)


def match_expression(aus):
    if not isinstance(aus, dict) or not 1 <= len(aus) <= len(KNOWN_AUS):
        raise ValueError(f"aus: dict of 1..{len(KNOWN_AUS)} action-unit intensities required")
    x = {}
    for k, v in aus.items():
        if isinstance(k, bool) or not isinstance(k, int) or k not in KNOWN_AUS:
            raise ValueError(f"aus: unknown action unit {k!r}; known {list(KNOWN_AUS)}")
        x[k] = _intensity(v, f"aus[{k}]")
    norm_sq = sum(v * v for v in x.values())
    scores = []
    for name, proto in PROTOTYPES.items():
        dot = sum(x.get(a, Fraction(0)) for a in proto)
        if norm_sq == 0:
            cos_sq, cos = Fraction(0), 0.0
        else:
            cos_sq = dot * dot / (norm_sq * len(proto))
            cos = math.sqrt(float(cos_sq))
        scores.append({"emotion": name, "cosine": cos, "cos_sq": cos_sq,
                       "mean_intensity": float(dot / len(proto))})
    scores.sort(key=lambda s: (-s["cos_sq"], s["emotion"]))
    best = scores[0]
    label = best["emotion"] if best["cos_sq"] >= MATCH_COS_SQ else "neutral_or_ambiguous"
    return {"label": label,
            "scores": [{"emotion": s["emotion"], "cosine": s["cosine"], "mean_intensity": s["mean_intensity"]} for s in scores],
            "status_note": STATUS_NOTE}
