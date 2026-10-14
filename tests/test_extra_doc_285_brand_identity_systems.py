import decimal
import random
import pytest
from sugarcode.extra_doc import brand_identity_systems as b

A = b.analyze_brand
PAL = ["#000000", "#ffffff", "#ff0000"]


def U(i, fg, bg, font="Sans"):
    return {"id": i, "color": fg, "background": bg, "font": font}


def test_constants():
    from fractions import Fraction
    assert (b.MAX_PALETTE, b.MAX_FONTS, b.MAX_USAGES, b.MAX_NAME, b.MIN_CONTRAST) == (12, 10, 100, 40, Fraction(9, 2))
    assert b.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal():
    r = A(PAL, ["Sans", "Serif"], [U("a", "#000000", "#ffffff"), U("b", "#FF0000", "#ffffff", "Comic"), U("c", "#fe0101", "#ffffff"),
                                    U("d", "#777777", "#ffffff"), U("e", "#ffffff", "#ffffff")])
    a, bb, c, d, e = r["usages"]
    assert a == {"id": "a", "color_in_palette": True, "background_in_palette": True, "font_allowed": True,
                 "contrast": 21.0, "contrast_ok": True, "nearest_color": None, "nearest_background": None, "compliant": True}
    assert bb["font_allowed"] is False and bb["color_in_palette"] is True and bb["compliant"] is False
    assert bb["contrast"] == pytest.approx(3.9984, abs=1e-4) and bb["contrast_ok"] is False
    assert c["color_in_palette"] is False and c["nearest_color"] == "#ff0000" and c["compliant"] is False
    assert d["nearest_color"] == "#000000" and d["contrast_ok"] is False         # (119^2*3 to black) < to white (136^2*3); 4.48 < 4.5
    assert e["contrast"] == 1.0 and e["contrast_ok"] is False and e["compliant"] is False
    assert r["consistency"] == 0.2
    assert r["min_palette_distance_sq"] == 255 ** 2                                # red to black is 255^2; red to white is 2*255^2; black to white 3*255^2


def test_min_distance_hand():
    assert A(["#000000", "#010203"], ["F"], [U("a", "#000000", "#010203", "F")])["min_palette_distance_sq"] == 1 + 4 + 9
    assert A(["#000000"], ["F"], [U("a", "#000000", "#000000", "F")])["min_palette_distance_sq"] is None


def test_nearest_ties_and_order():
    # equidistant palette colours: the earlier palette entry wins
    r = A(["#000000", "#0000fe"], ["F"], [U("a", "#00007f", "#000000", "F")])
    assert r["usages"][0]["nearest_color"] == "#000000"      # 127^2 vs 127^2 tie -> first
    r = A(["#0000fe", "#000000"], ["F"], [U("a", "#00007f", "#000000", "F")])
    assert r["usages"][0]["nearest_color"] == "#0000fe"
    r = A(["#000000", "#0000fe"], ["F"], [U("a", "#000080", "#000000", "F")])
    assert r["usages"][0]["nearest_color"] == "#0000fe"
    r = A(["#000000", "#ffffff"], ["F"], [U("a", "#101010", "#f0f0f0", "F")])
    assert (r["usages"][0]["nearest_color"], r["usages"][0]["nearest_background"]) == ("#000000", "#ffffff")


def test_contrast_decimal_oracle():
    D = decimal.Decimal
    rng = random.Random(285)
    with decimal.localcontext() as ctx:
        ctx.prec = 60
        def lum(rgb):
            tot = D(0)
            for w, v in zip(("0.2126", "0.7152", "0.0722"), rgb):
                v = D(v) / 255
                tot += D(w) * (v / D("12.92") if v <= D("0.04045") else ((v + D("0.055")) / D("1.055")) ** D("2.4"))
            return tot
        for _ in range(120):
            f = tuple(rng.randrange(256) for _ in range(3)); g = tuple(rng.randrange(256) for _ in range(3))
            la, lb = lum(f), lum(g)
            want = (max(la, lb) + D("0.05")) / (min(la, lb) + D("0.05"))
            r = A(["#000000"], ["F"], [U("a", "#%02x%02x%02x" % f, "#%02x%02x%02x" % g, "F")])["usages"][0]
            assert r["contrast"] == round(float(want), 4) and r["contrast_ok"] == (want >= D("4.5"))


def test_normalisation_and_validation():
    r = A(["FF0000", " #00FF00 "], ["F"], [U("a", "ff0000", "#00ff00", "F")])
    assert r["usages"][0]["color_in_palette"] and r["usages"][0]["background_in_palette"]
    for bad, m in [([], "1..12"), ("x", "1..12"), (["#fff"], r"palette\[0\]: hex"), ([5], r"palette\[0\]: hex"),
                   (["#000000", "000000"], "duplicate color")]:
        with pytest.raises(ValueError, match=m):
            A(bad, ["F"], [U("a", "#000000", "#000000")])
    assert len(A(["#%02x0000" % i for i in range(12)], ["F"], [U("a", "#000000", "#000000")])["usages"]) == 1
    with pytest.raises(ValueError, match="1..12"):
        A(["#%02x0000" % i for i in range(13)], ["F"], [U("a", "#000000", "#000000")])
    for bad, m in [([], "1..10"), ("x", "1..10"), ([""], "name must"), (["x" * 41], "name must"), ([3], "name must"), (["a", "a"], "duplicate name")]:
        with pytest.raises(ValueError, match=m):
            A(PAL, bad, [U("a", "#000000", "#000000")])
    assert A(PAL, ["x" * 40], [U("a", "#000000", "#000000")])["consistency"] == 0.0
    assert len(A(PAL, [f"f{i}" for i in range(10)], [U("a", "#000000", "#000000")])["usages"]) == 1
    with pytest.raises(ValueError, match="1..10"):
        A(PAL, [f"f{i}" for i in range(11)], [U("a", "#000000", "#000000")])
    for us, m in [([], "1..100"), ("x", "1..100"), ([5], r"usages\[0\]: dict"), ([U("", "#000000", "#000000")], "id must"),
                  ([U("x" * 41, "#000000", "#000000")], "id must"), ([U("a", "zz", "#000000")], r"usages\[0\].color: hex"),
                  ([U("a", "#000000", None)], r"usages\[0\].background: hex"),
                  ([{"id": "a", "color": "#000000", "background": "#000000"}], "font string required"),
                  ([U("a", "#000000", "#000000"), U("a", "#000000", "#000000")], "duplicate id")]:
        with pytest.raises(ValueError, match=m):
            A(PAL, ["Sans"], us)
    many = [U(f"u{i}", "#000000", "#ffffff") for i in range(101)]
    with pytest.raises(ValueError, match="1..100"):
        A(PAL, ["Sans"], many)
    assert A(PAL, ["Sans"], many[:100])["consistency"] == 1.0
    assert A(PAL, ["Sans"], [U("x" * 40, "#000000", "#ffffff")])["consistency"] == 1.0


def test_contrast_exactly_at_threshold_is_ok(monkeypatch):
    from fractions import Fraction
    monkeypatch.setattr(b, "_contrast", lambda x, y: Fraction(9, 2))
    assert A(PAL, ["Sans"], [U("a", "#000000", "#ffffff")])["usages"][0]["contrast_ok"] is True
    monkeypatch.setattr(b, "_contrast", lambda x, y: Fraction(449, 100))
    assert A(PAL, ["Sans"], [U("a", "#000000", "#ffffff")])["usages"][0]["contrast_ok"] is False


def test_consistency_fraction():
    us = [U("a", "#000000", "#ffffff"), U("b", "#000000", "#ffffff"), U("c", "#000000", "#ffffff", "X")]
    assert A(PAL, ["Sans"], us)["consistency"] == pytest.approx(2 / 3)


def test_distances_use_differences_not_sums_for_non_black_palettes():
    # (1,2,3) vs (3,5,7): 2^2 + 3^2 + 4^2 = 29 (a sum instead of a difference would give 152)
    r = A(["#010203", "#030507"], ["F"], [U("a", "#010203", "#030507", "F")])
    assert r["min_palette_distance_sq"] == 29
    # (16,32,48) vs (64,80,96): 3 * 48^2 = 6912 ; vs (255,0,0) far away
    r = A(["#102030", "#405060", "#ff0000"], ["F"], [U("a", "#102030", "#405060", "F")])
    assert r["min_palette_distance_sq"] == 3 * 48 ** 2
    # nearest uses the same difference: usage (2,4,6) is 14 from (1,2,3) and 3 from (3,5,7)
    r = A(["#010203", "#030507"], ["F"], [U("a", "#020406", "#010203", "F")])
    assert r["usages"][0]["nearest_color"] == "#030507" and r["usages"][0]["nearest_background"] is None
    # asymmetric: usage (200,10,10) vs palette (190,20,20) and (250,0,0): 100+100+100=300 vs 2500+100+100 -> first
    r = A(["#be1414", "#fa0000"], ["F"], [U("a", "#c80a0a", "#be1414", "F")])
    assert r["usages"][0]["nearest_color"] == "#be1414"
