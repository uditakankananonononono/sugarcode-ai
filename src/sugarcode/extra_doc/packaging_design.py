"""Row 286 packaging design (PARTIAL): box geometry, shelf fit and sheet layout arithmetic from supplied millimetre sizes.

Reports surface area, volume, best axis-aligned shelf orientation and count, front-face share of the shelf opening,
and tuck-box net fit on a sheet. No judgement of shelf impact, appeal, structural strength or manufacturability."""
from itertools import permutations

MAX_MM = 10000
GLUE_FLAP_MM = 15
STATUS_NOTE = ("PARTIAL: millimetre arithmetic for box area, volume, axis-aligned shelf packing and a rectangular tuck-box "
               "net on a sheet; no judgement of shelf impact, appeal, strength or manufacturability")


def _dims(v, name):
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        raise ValueError(f"{name}: three integers required")
    out = []
    for i, x in enumerate(v):
        if isinstance(x, bool) or not isinstance(x, int):
            raise ValueError(f"{name}[{i}]: integer required")
        if abs(x) > 10 ** 9:
            raise ValueError(f"{name}[{i}]: magnitude above 1000000000")
        if not 1 <= x <= MAX_MM:
            raise ValueError(f"{name}[{i}]: must be within [1, {MAX_MM}]")
        out.append(x)
    return tuple(out)


def analyze_package(box, shelf, sheet):
    """box = (length, width, height); shelf = (width, height, depth); sheet = (width, height). Millimetres."""
    l, w, h = _dims(box, "box")
    sw_, sh_, sd_ = _dims(shelf, "shelf")
    if not isinstance(sheet, (list, tuple)) or len(sheet) != 2:
        raise ValueError("sheet: two integers required")
    sx, sy, _ = _dims(list(sheet) + [1], "sheet")
    best = None
    for a, b, c in sorted(set(permutations((l, w, h)))):
        n_w, n_h, n_d = sw_ // a, sh_ // b, sd_ // c
        count = n_w * n_h * n_d
        if best is None or count > best["count"]:
            best = {"orientation": {"width": a, "height": b, "depth": c}, "count": count,
                    "across": n_w, "high": n_h, "deep": n_d}
    net_w, net_h = 2 * (l + w) + GLUE_FLAP_MM, h + 2 * w
    fit = max((sx // net_w) * (sy // net_h), (sx // net_h) * (sy // net_w))
    front = best["orientation"]["width"] * best["orientation"]["height"]
    return {
        "surface_area_mm2": 2 * (l * w + l * h + w * h),
        "volume_mm3": l * w * h,
        "best_shelf_fit": best,
        "front_face_share": front / (sw_ * sh_),
        "net_mm": {"width": net_w, "height": net_h},
        "nets_per_sheet": fit,
        "net_fits_sheet": fit >= 1,
        "sheet_utilisation": fit * net_w * net_h / (sx * sy),
        "status_note": STATUS_NOTE,
    }
