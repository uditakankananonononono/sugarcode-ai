"""Row 283 typography selection (PARTIAL): readability and pairing arithmetic over supplied type settings.

Checks line-height ratio, measure, size floor, heading-scale steps and font-pair category contrast against
fixed conventional thresholds. No judgement of font beauty, brand fit or reading comfort for any person."""
import math
from fractions import Fraction

CATEGORIES = ("serif", "sans", "mono", "display", "script")
MAX_FONTS = 30
MAX_HEADINGS = 10
MAX_NAME = 40
MIN_BODY_PX = 16
LINE_HEIGHT_RANGE = (Fraction(13, 10), Fraction(17, 10))
MEASURE_RANGE = (45, 75)
MIN_SCALE_STEP = Fraction(6, 5)
XHEIGHT_GAP = Fraction(1, 20)
MAX_PX = 1000
STATUS_NOTE = ("PARTIAL: conventional thresholds for size, line height, measure, heading steps and pairing; "
               "no judgement of beauty, brand fit or reader comfort")


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float, Fraction)):
        raise ValueError(f"{name}: number required")
    if abs(v) > 1e9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return Fraction(v)


def analyze_typography(body_px, line_height_px, measure_chars, heading_px, fonts):
    body = _num(body_px, "body_px", 1, MAX_PX)
    lh = _num(line_height_px, "line_height_px", 1, MAX_PX)
    ms = _num(measure_chars, "measure_chars", 1, 1000)
    if not isinstance(heading_px, (list, tuple)) or len(heading_px) > MAX_HEADINGS:
        raise ValueError(f"heading_px: list of at most {MAX_HEADINGS} sizes required")
    heads = [_num(h, f"heading_px[{i}]", 1, MAX_PX) for i, h in enumerate(heading_px)]
    if not isinstance(fonts, (list, tuple)) or not 1 <= len(fonts) <= MAX_FONTS:
        raise ValueError(f"fonts: list of 1..{MAX_FONTS} entries required")
    fl, seen = [], set()
    for i, f in enumerate(fonts):
        if not isinstance(f, dict):
            raise ValueError(f"fonts[{i}]: dict required")
        n = f.get("name")
        if not isinstance(n, str) or not 1 <= len(n) <= MAX_NAME:
            raise ValueError(f"fonts[{i}]: name must be a string of 1..{MAX_NAME} characters")
        if n in seen:
            raise ValueError(f"fonts[{i}]: duplicate name {n!r}")
        seen.add(n)
        cat = f.get("category")
        if not isinstance(cat, str) or cat not in CATEGORIES:
            raise ValueError(f"fonts[{i}]: category must be one of {list(CATEGORIES)}")
        xh = _num(f.get("x_height"), f"fonts[{i}].x_height", Fraction(1, 5), Fraction(4, 5))
        fl.append((n, cat, xh))
    ratio = lh / body
    steps = [(heads[i], heads[i + 1] / heads[i]) for i in range(len(heads) - 1)]
    pairs = []
    for i in range(len(fl)):
        for j in range(i + 1, len(fl)):
            (na, ca, xa), (nb, cb, xb) = fl[i], fl[j]
            gap = abs(xa - xb)
            if ca == cb:
                verdict = "too_similar" if gap < XHEIGHT_GAP else "same_category_distinct_xheight"
            else:
                verdict = "contrast" if gap < XHEIGHT_GAP else "contrast_xheight_mismatch"
            pairs.append({"a": na, "b": nb, "xheight_gap": float(gap), "verdict": verdict})
    return {
        "line_height_ratio": float(ratio),
        "line_height_ok": LINE_HEIGHT_RANGE[0] <= ratio <= LINE_HEIGHT_RANGE[1],
        "measure_ok": MEASURE_RANGE[0] <= ms <= MEASURE_RANGE[1],
        "body_size_ok": body >= MIN_BODY_PX,
        "heading_steps": [{"from": float(a), "ratio": float(r), "ok": r >= MIN_SCALE_STEP} for a, r in steps],
        "headings_descending_or_flat": any(heads[i] > heads[i + 1] for i in range(len(heads) - 1)),
        "headings_above_body": all(h > body for h in heads),
        "font_pairs": pairs,
        "status_note": STATUS_NOTE,
    }
