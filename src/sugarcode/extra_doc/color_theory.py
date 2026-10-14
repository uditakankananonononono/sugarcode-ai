"""Row 281 color theory application (PARTIAL): hue, contrast and harmony arithmetic over supplied hex colors.

Labels such as warm, cool or energetic come from fixed numeric thresholds documented below.
They are conventional heuristics, not a model of how any viewer feels."""
import re

MAX_COLORS = 12
HARMONY_TOLERANCE = 15
ANALOGOUS_MAX = 30
CHROMA_MIN = 0.1
AA_RATIO = 4.5
AAA_RATIO = 7
STATUS_NOTE = ("PARTIAL: hue, saturation, lightness, WCAG contrast and hue-gap arithmetic with threshold labels; "
               "emotional labels are conventional heuristics, no claim about any viewer's response")
_HEX = re.compile(r"#?([0-9a-fA-F]{6})")
_EFFECT = {("warm", "vivid"): "energetic", ("warm", "mid"): "friendly", ("warm", "muted"): "cozy",
           ("cool", "vivid"): "fresh", ("cool", "mid"): "calm", ("cool", "muted"): "serene",
           ("green-ish", "vivid"): "lively", ("green-ish", "mid"): "natural", ("green-ish", "muted"): "restful"}


def _parse(v, i):
    if not isinstance(v, str):
        raise ValueError(f"colors[{i}]: hex string like #rrggbb required")
    m = _HEX.fullmatch(v.strip())
    if not m:
        raise ValueError(f"colors[{i}]: hex string like #rrggbb required")
    h = m.group(1).lower()
    return tuple(int(h[k:k + 2], 16) for k in (0, 2, 4)), "#" + h


def _hsl(rgb):
    r, g, b = (c / 255 for c in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    d = mx - mn
    if d == 0:
        return 0.0, 0.0, l
    s = d / (1 - abs(2 * l - 1))
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60.0, s, l


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _temperature(h, s):
    if s < CHROMA_MIN:
        return "neutral"
    if h < 75 or h >= 330:
        return "warm"
    if 165 <= h < 270:
        return "cool"
    return "green-ish"


def _vividness(s):
    return "vivid" if s >= 0.6 else "muted" if s <= 0.25 else "mid"


def _relation(h1, s1, h2, s2):
    if s1 < CHROMA_MIN or s2 < CHROMA_MIN:
        return "achromatic"
    d = abs(h1 - h2)
    d = min(d, 360 - d)
    if d <= ANALOGOUS_MAX:
        return "analogous"
    if abs(d - 120) <= HARMONY_TOLERANCE:
        return "triadic"
    if abs(d - 180) <= HARMONY_TOLERANCE:
        return "complementary"
    return "none"


def analyze_palette(colors):
    if not isinstance(colors, (list, tuple)) or not 2 <= len(colors) <= MAX_COLORS:
        raise ValueError(f"colors: list of 2..{MAX_COLORS} hex strings required")
    parsed = [_parse(c, i) for i, c in enumerate(colors)]
    rows = []
    for rgb, hx in parsed:
        h, s, l = _hsl(rgb)
        temp = _temperature(h, s)
        eff = _EFFECT.get((temp, _vividness(s))) if temp != "neutral" else (
            "dark" if l < 0.3 else "light" if l > 0.7 else "balanced")
        rows.append({"hex": hx, "rgb": list(rgb), "hue": round(h, 4), "saturation": round(s, 4),
                     "lightness": round(l, 4), "temperature": temp, "effect": eff})
    pairs = []
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            ratio = contrast_ratio(parsed[i][0], parsed[j][0])
            hi, si, _ = _hsl(parsed[i][0])
            hj, sj, _ = _hsl(parsed[j][0])
            pairs.append({"a": parsed[i][1], "b": parsed[j][1], "relation": _relation(hi, si, hj, sj),
                          "contrast": round(ratio, 4), "aa": ratio >= AA_RATIO, "aaa": ratio >= AAA_RATIO})
    return {"colors": rows, "pairs": pairs, "status_note": STATUS_NOTE}
