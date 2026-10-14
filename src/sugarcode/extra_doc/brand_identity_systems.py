"""Row 285 brand identity systems (PARTIAL): consistency checks of supplied usages against a supplied palette and font list.

Reports exact palette and font membership, nearest palette colour by RGB distance and WCAG contrast.
No judgement of whether the system is cohesive in a visual or strategic sense."""
import re
from fractions import Fraction

MAX_PALETTE = 12
MAX_FONTS = 10
MAX_USAGES = 100
MAX_NAME = 40
MIN_CONTRAST = Fraction(9, 2)
STATUS_NOTE = ("PARTIAL: exact palette and font membership, nearest-palette distance and WCAG contrast of supplied usages; "
               "no judgement of visual cohesion or brand strategy")
_HEX = re.compile(r"#?([0-9a-fA-F]{6})")


def _hex(v, name):
    m = _HEX.fullmatch(v.strip()) if isinstance(v, str) else None
    if not m:
        raise ValueError(f"{name}: hex color like #rrggbb required")
    h = m.group(1).lower()
    return tuple(int(h[k:k + 2], 16) for k in (0, 2, 4)), "#" + h


def _lum(rgb):
    out = Fraction(0)
    for wgt, c in zip((Fraction(2126, 10000), Fraction(7152, 10000), Fraction(722, 10000)), rgb):
        v = c / 255
        lin = v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        out += wgt * Fraction(lin)
    return out


def _contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + Fraction(1, 20)) / (lo + Fraction(1, 20))


def analyze_brand(palette, fonts, usages):
    if not isinstance(palette, (list, tuple)) or not 1 <= len(palette) <= MAX_PALETTE:
        raise ValueError(f"palette: list of 1..{MAX_PALETTE} hex colors required")
    pal = [_hex(c, f"palette[{i}]") for i, c in enumerate(palette)]
    if len({h for _, h in pal}) != len(pal):
        raise ValueError("palette: duplicate color")
    if not isinstance(fonts, (list, tuple)) or not 1 <= len(fonts) <= MAX_FONTS:
        raise ValueError(f"fonts: list of 1..{MAX_FONTS} names required")
    for i, f in enumerate(fonts):
        if not isinstance(f, str) or not 1 <= len(f) <= MAX_NAME:
            raise ValueError(f"fonts[{i}]: name must be a string of 1..{MAX_NAME} characters")
    if len(set(fonts)) != len(fonts):
        raise ValueError("fonts: duplicate name")
    if not isinstance(usages, (list, tuple)) or not 1 <= len(usages) <= MAX_USAGES:
        raise ValueError(f"usages: list of 1..{MAX_USAGES} entries required")
    rows, seen, ok_count = [], set(), 0
    for i, u in enumerate(usages):
        if not isinstance(u, dict):
            raise ValueError(f"usages[{i}]: dict required")
        k = u.get("id")
        if not isinstance(k, str) or not 1 <= len(k) <= MAX_NAME:
            raise ValueError(f"usages[{i}]: id must be a string of 1..{MAX_NAME} characters")
        if k in seen:
            raise ValueError(f"usages[{i}]: duplicate id {k!r}")
        seen.add(k)
        fg, fgh = _hex(u.get("color"), f"usages[{i}].color")
        bg, bgh = _hex(u.get("background"), f"usages[{i}].background")
        font = u.get("font")
        if not isinstance(font, str):
            raise ValueError(f"usages[{i}]: font string required")
        def nearest(rgb):
            best = min(range(len(pal)), key=lambda j: (sum((a - b) ** 2 for a, b in zip(rgb, pal[j][0])), j))
            return pal[best][1]
        in_pal = {h for _, h in pal}
        ratio = _contrast(fg, bg)
        row = {"id": k, "color_in_palette": fgh in in_pal, "background_in_palette": bgh in in_pal,
               "font_allowed": font in fonts, "contrast": round(float(ratio), 4), "contrast_ok": ratio >= MIN_CONTRAST,
               "nearest_color": None if fgh in in_pal else nearest(fg),
               "nearest_background": None if bgh in in_pal else nearest(bg)}
        row["compliant"] = (row["color_in_palette"] and row["background_in_palette"]
                            and row["font_allowed"] and row["contrast_ok"])
        ok_count += row["compliant"]
        rows.append(row)
    dists = [sum((a - b) ** 2 for a, b in zip(pal[i][0], pal[j][0])) for i in range(len(pal)) for j in range(i + 1, len(pal))]
    return {"usages": rows, "consistency": float(Fraction(ok_count, len(rows))),
            "min_palette_distance_sq": min(dists) if dists else None, "status_note": STATUS_NOTE}
