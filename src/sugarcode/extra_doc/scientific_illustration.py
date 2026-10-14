"""Row 319 scientific illustration: scale-bar and magnification arithmetic for a figure.

Given pixels per micrometre and the image width, picks the largest 1-2-5 scale-bar length (1 nm to 5000 mm) that
fits within a fraction of the width, and computes figure magnification. Exact Fractions. Says nothing about whether
a drawing accurately depicts any research, specimen or data."""
from fractions import Fraction
import math

PPU_RANGE = (1e-4, 1e6)
WIDTH_RANGE = (10, 100000)
FRACTION_RANGE = (0.05, 0.5)
STATUS_NOTE = ("PARTIAL: scale-bar length and magnification arithmetic only; "
               "no claim that any drawing accurately depicts research")


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name}: number required")
    if abs(v) > 1e9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return Fraction(v)


def _label(v):
    if v < 1:
        return f"{int(v * 1000)} nm"
    if v < 1000:
        return f"{int(v)} um"
    return f"{int(v / 1000)} mm"


def scale_bar(px_per_um, image_width_px, max_fraction=0.25):
    ppu = _num(px_per_um, "px_per_um", *PPU_RANGE)
    w = _num(image_width_px, "image_width_px", *WIDTH_RANGE)
    fr = _num(max_fraction, "max_fraction", *FRACTION_RANGE)
    budget = w * fr
    best = None
    for k in range(-3, 7):
        for m in (1, 2, 5):
            v = Fraction(m) * Fraction(10) ** k
            if v * ppu <= budget and (best is None or v > best):
                best = v
    if best is None:
        raise ValueError("no scale bar fits")
    return {"length_um": best, "bar_px": best * ppu, "label": _label(best), "fraction_of_width": best * ppu / w,
            "status": STATUS_NOTE}


def magnification(drawn_mm, real_um):
    d = _num(drawn_mm, "drawn_mm", 0.001, 100000)
    r = _num(real_um, "real_um", 0.001, 1e9)
    return d * 1000 / r
