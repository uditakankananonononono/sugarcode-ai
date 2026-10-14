import colorsys
import itertools
import random
import pytest
from sugarcode.extra_doc import color_theory as c

A = c.analyze_palette


def test_constants():
    assert (c.MAX_COLORS, c.HARMONY_TOLERANCE, c.ANALOGOUS_MAX, c.CHROMA_MIN, c.AA_RATIO, c.AAA_RATIO) == (12, 15, 30, 0.1, 4.5, 7)
    assert c._EFFECT == {("warm", "vivid"): "energetic", ("warm", "mid"): "friendly", ("warm", "muted"): "cozy",
                         ("cool", "vivid"): "fresh", ("cool", "mid"): "calm", ("cool", "muted"): "serene",
                         ("green-ish", "vivid"): "lively", ("green-ish", "mid"): "natural", ("green-ish", "muted"): "restful"}
    assert c.STATUS_NOTE.startswith("PARTIAL")


def test_contrast_hand_literals():
    r = A(["#000000", "#ffffff"])
    assert r["pairs"][0]["contrast"] == 21.0 and r["pairs"][0]["aa"] and r["pairs"][0]["aaa"]
    assert c.contrast_ratio((0, 0, 0), (0, 0, 0)) == 1.0
    # pure red luminance 0.2126 -> (1.05)/(0.2626)
    assert c.contrast_ratio((255, 255, 255), (255, 0, 0)) == pytest.approx(1.05 / 0.2626, abs=1e-12)
    assert c.luminance((0, 255, 0)) == pytest.approx(0.7152) and c.luminance((0, 0, 255)) == pytest.approx(0.0722)
    # #767676 on white: well-known 4.54 AA pass; #777777 4.48 fail
    assert A(["#767676", "#ffffff"])["pairs"][0]["aa"] is True
    assert A(["#777777", "#ffffff"])["pairs"][0]["aa"] is False
    assert A(["#777777", "#ffffff"])["pairs"][0]["contrast"] == pytest.approx(4.4781, abs=1e-3)
    # #595959 on white is 7.0 (AAA) ; #5a5a5a 6.9 is not
    assert A(["#595959", "#ffffff"])["pairs"][0]["aaa"] is True
    assert A(["#5f5f5f", "#ffffff"])["pairs"][0]["aaa"] is False


def test_hsl_matches_stdlib_oracle_on_random_colors():
    rng = random.Random(281)
    for _ in range(300):
        rgb = tuple(rng.randint(0, 255) for _ in range(3))
        hx = "#%02x%02x%02x" % rgb
        row = A([hx, "#000000"])["colors"][0]
        h, l, s = colorsys.rgb_to_hls(*(x / 255 for x in rgb))
        assert row["hue"] == pytest.approx(h * 360, abs=2e-4) or abs(row["hue"] - h * 360) > 359.99
        assert row["saturation"] == pytest.approx(s, abs=1e-4)
        assert row["lightness"] == pytest.approx(l, abs=1e-4)
        assert row["rgb"] == list(rgb) and row["hex"] == hx


def test_relations_hand_literals():
    red, orange, green, blue, cyan = "#ff0000", "#ff8000", "#00ff00", "#0000ff", "#00ffff"
    def rel(a, b):
        return A([a, b])["pairs"][0]["relation"]
    assert rel(red, cyan) == "complementary"                  # hue 0 vs 180
    assert rel(red, "#ff7f00") == "analogous"                 # hue 29.88
    assert rel(red, orange) == "none"                         # hue 30.12 is just past the 30 limit
    assert rel(red, green) == "triadic" and rel(red, blue) == "triadic"     # 120 and 240 (gap 120)
    assert rel("#ff0000", "#80ff00") == "none"                # 0 vs 90: none (not within 15 of 120)
    assert rel(red, "#808080") == "achromatic" and rel("#808080", red) == "achromatic"
    # circular gap: hue 350 vs 10 is 20 apart -> analogous
    assert rel("#ff0055", "#ff2a00") == "analogous"


def test_relation_rule_over_all_hues_against_stdlib_hue():
    seen = set()
    for hue in range(360):
        r, g, b = colorsys.hls_to_rgb(hue / 360, 0.5, 1.0)
        hx = "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))
        real = colorsys.rgb_to_hls(round(r * 255) / 255, round(g * 255) / 255, round(b * 255) / 255)[0] * 360
        d = min(abs(real), 360 - abs(real))
        want = "analogous" if d <= 30 else "triadic" if abs(d - 120) <= 15 else "complementary" if abs(d - 180) <= 15 else "none"
        got = A(["#ff0000", hx])["pairs"][0]["relation"]
        assert got == want, (hue, got, want)
        seen.add(got)
    assert seen == {"analogous", "triadic", "complementary", "none"}


def test_temperature_and_effect_hand_literals():
    def row(hx):
        return A([hx, "#000000"])["colors"][0]
    assert (row("#ff0000")["temperature"], row("#ff0000")["effect"]) == ("warm", "energetic")
    assert (row("#0000ff")["temperature"], row("#0000ff")["effect"]) == ("cool", "fresh")
    assert (row("#00ff00")["temperature"], row("#00ff00")["effect"]) == ("green-ish", "lively")
    assert row("#000000")["temperature"] == "neutral" and row("#000000")["effect"] == "dark"
    assert row("#ffffff")["effect"] == "light" and row("#808080")["effect"] == "balanced"
    assert row("#cc8080")["effect"] == "friendly"            # s=0.4 mid, h=0 warm
    assert row("#b39999")["effect"] == "cozy"                # s=0.2 muted warm
    assert row("#5c7ae6")["effect"] == "fresh" and row("#6680cc")["effect"] == "calm"
    assert row("#8c9db3")["effect"] == "serene"
    assert row("#80b380")["effect"] == "natural" and row("#99b399")["effect"] == "restful"


def test_temperature_over_all_hues_against_stdlib_hue():
    got_all = set()
    for hue in range(360):
        r, g, b = colorsys.hls_to_rgb(hue / 360, 0.5, 1.0)
        rgb = tuple(round(x * 255) for x in (r, g, b))
        real = colorsys.rgb_to_hls(*(x / 255 for x in rgb))[0] * 360
        want = "warm" if real < 75 or real >= 330 else "cool" if 165 <= real < 270 else "green-ish"
        got = A(["#%02x%02x%02x" % rgb, "#000000"])["colors"][0]["temperature"]
        assert got == want, (hue, got, want)
        got_all.add(got)
    assert got_all == {"warm", "cool", "green-ish"}
    def temp_s(s):
        r, g, b = colorsys.hls_to_rgb(0, 0.5, s)
        return A(["#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255)), "#000000"])["colors"][0]["temperature"]
    assert temp_s(0.12) == "warm" and temp_s(0.08) == "neutral"


def test_vividness_boundaries_via_effect():
    # saturation exactly 0.6 vivid, 0.25 muted (hue 0 warm)
    def eff(s):
        r, g, b = colorsys.hls_to_rgb(0, 0.5, s)
        return A(["#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255)), "#000000"])["colors"][0]["effect"]
    assert eff(0.61) == "energetic" and eff(0.58) == "friendly" and eff(0.27) == "friendly" and eff(0.23) == "cozy"


def test_normalisation_and_validation():
    r = A(["FF0000", " #00FFFF "])
    assert [x["hex"] for x in r["colors"]] == ["#ff0000", "#00ffff"]
    for bad in ["#fff", "#gggggg", "", "#ff00000", 5, None, "##ff0000", "ff 0000"]:
        with pytest.raises(ValueError, match=r"colors\[1\]: hex string"):
            A(["#000000", bad])
    with pytest.raises(ValueError, match=r"colors\[0\]"):
        A([5, "#000000"])
    for bad in [[], ["#000000"], "x", 3]:
        with pytest.raises(ValueError, match="2..12"):
            A(bad)
    twelve = ["#%02x0000" % (i * 10) for i in range(12)]
    assert len(A(twelve)["pairs"]) == 66
    with pytest.raises(ValueError, match="2..12"):
        A(twelve + ["#000000"])
    assert [(p["a"], p["b"]) for p in A(["#010101", "#020202", "#030303"])["pairs"]] == [
        ("#010101", "#020202"), ("#010101", "#030303"), ("#020202", "#030303")]


def test_pair_flags_boundaries():
    # constructed greys: find via oracle that contrast straddles 4.5 and 7 with the stdlib-free formula in this test
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    def ratio(g):
        return 1.05 / (lin(g) + 0.05)
    for g in range(60, 140):
        r = A(["#%02x%02x%02x" % (g, g, g), "#ffffff"])["pairs"][0]
        assert r["aa"] == (ratio(g) >= 4.5) and r["aaa"] == (ratio(g) >= 7)
        assert r["contrast"] == pytest.approx(ratio(g), abs=1e-4)


def test_grey_hue_and_saturation_are_zero_and_low_branch_linearisation():
    row = A(["#808080", "#000000"])["colors"][0]
    assert row["hue"] == 0.0 and row["saturation"] == 0.0 and row["lightness"] == pytest.approx(0.502, abs=1e-4)
    assert c.luminance((10, 10, 10)) == pytest.approx(10 / 255 / 12.92, abs=1e-12)          # below the 0.04045 knee
    assert c.luminance((11, 11, 11)) == pytest.approx(((11 / 255 + 0.055) / 1.055) ** 2.4, abs=1e-12)   # above the knee
    assert c.luminance((255, 255, 255)) == pytest.approx(1.0, abs=1e-12)


def test_rounding_to_four_places_exact():
    row = A(["#123456", "#000000"])["colors"][0]
    h, l, s = colorsys.rgb_to_hls(18 / 255, 52 / 255, 86 / 255)
    assert (row["hue"], row["saturation"], row["lightness"]) == (round(h * 360, 4), round(s, 4), round(l, 4))
    assert row["hue"] == 210.0
    p = A(["#123456", "#ffffff"])["pairs"][0]
    assert p["contrast"] == round(1.05 / (c.luminance((18, 52, 86)) + 0.05), 4)
    assert len(repr(p["contrast"]).split(".")[1]) <= 4


def test_threshold_helpers_exact_boundaries():
    t, vv, rel = c._temperature, c._vividness, c._relation
    assert (t(74.999, 1), t(75, 1), t(329.999, 1), t(330, 1), t(0, 1)) == ("warm", "green-ish", "green-ish", "warm", "warm")
    assert (t(164.999, 1), t(165, 1), t(269.999, 1), t(270, 1)) == ("green-ish", "cool", "cool", "green-ish")
    assert t(10, 0.1) == "warm" and t(10, 0.0999) == "neutral"
    assert (vv(0.6), vv(0.5999), vv(0.2501), vv(0.25), vv(0)) == ("vivid", "mid", "mid", "muted", "muted")
    assert rel(0, 1, 30, 1) == "analogous" and rel(0, 1, 30.001, 1) == "none" and rel(30, 1, 0, 1) == "analogous"
    assert rel(0, 1, 105, 1) == "triadic" and rel(0, 1, 104.999, 1) == "none"
    assert rel(0, 1, 135, 1) == "triadic" and rel(0, 1, 135.001, 1) == "none"
    assert rel(0, 1, 165, 1) == "complementary" and rel(0, 1, 164.999, 1) == "none"
    assert rel(0, 1, 195, 1) == "complementary" and rel(0, 1, 195.001, 1) == "none"
    assert rel(350, 1, 10, 1) == "analogous" and rel(10, 1, 350, 1) == "analogous"
    assert rel(0, 0.1, 100, 0.1) == "none" and rel(0, 0.0999, 100, 1) == "achromatic" and rel(0, 1, 100, 0.0999) == "achromatic"
    assert rel(0, 1, 240, 1) == "triadic" and rel(240, 1, 0, 1) == "triadic"


def test_lightness_labels_for_neutrals():
    def eff(g):
        return A(["#%02x%02x%02x" % (g, g, g), "#ff0000"])["colors"][0]["effect"]
    assert [eff(g) for g in (76, 77, 178, 179)] == ["dark", "balanced", "balanced", "light"]
    # lightness exactly 0.3 / 0.7 with low saturation: (80,73,73) -> (153/510)=0.3 ; (183,176,176)? mx+mn=359 -> l=0.70392 light
    assert A(["#504949", "#000000"])["colors"][0]["effect"] == "balanced"


def test_outputs_rounded_to_exactly_four_places_over_samples():
    rng = random.Random(2810)
    saw_long = 0
    for _ in range(80):
        rgb = tuple(rng.randint(0, 255) for _ in range(3))
        other = tuple(rng.randint(0, 255) for _ in range(3))
        r = A(["#%02x%02x%02x" % rgb, "#%02x%02x%02x" % other])
        h, l, s = colorsys.rgb_to_hls(*(x / 255 for x in rgb))
        row = r["colors"][0]
        assert row["saturation"] == round(s, 4) and row["lightness"] == round(l, 4)
        assert row["hue"] == pytest.approx(round(h * 360, 4), abs=1.5e-4)
        for k in ("hue", "saturation", "lightness"):
            assert row[k] == round(row[k], 4)
        assert r["pairs"][0]["contrast"] == round(r["pairs"][0]["contrast"], 4)
        saw_long += len(repr(row["saturation"]).split(".")[1]) == 4
    assert saw_long > 20


def test_lightness_exactly_point_seven():
    assert A(["#b4b1b1", "#000000"])["colors"][0]["effect"] == "balanced"     # (180+177)/510 = 0.7


def test_knee_value_takes_the_linear_branch():
    # at the knee the linear branch gives 0.0031308049535603713, the power branch 0.0031308072830676845: they differ at 1e-9
    knee = 0.04045 * 255
    assert knee / 255 == 0.04045
    assert c._lin(knee) == 0.04045 / 12.92
    assert c._lin(knee) != ((0.04045 + 0.055) / 1.055) ** 2.4
    assert c._lin(knee + 0.01) == ((0.04045 + 0.01 / 255 + 0.055) / 1.055) ** 2.4


def test_relations_with_non_red_references():
    def rel(a, b):
        return A([a, b])["pairs"][0]["relation"]
    # same hue is gap 0 (analogous): a sum instead of a difference would give 120 (triadic) or 240 for these
    for hx in ("#ffff00", "#00ff00", "#0000ff", "#00ffff", "#ff00ff"):
        assert rel(hx, hx) == "analogous"
    assert rel("#ffff00", "#ff0000") == "none"          # 60 apart
    assert rel("#ffff00", "#00ff00") == "none"          # 60 apart
    assert rel("#ffff00", "#0000ff") == "complementary"  # 60 vs 240 = 180
    assert rel("#00ff00", "#ff00ff") == "complementary"  # 120 vs 300
    assert rel("#00ff00", "#0000ff") == "triadic"       # 120 vs 240
    assert rel("#0000ff", "#00ff00") == "triadic"


def test_exact_ratio_flag_semantics(monkeypatch):
    monkeypatch.setattr(c, "contrast_ratio", lambda a, b: 4.5)
    row = A(["#000000", "#ffffff"])["pairs"][0]
    assert row["aa"] is True and row["aaa"] is False
    monkeypatch.setattr(c, "contrast_ratio", lambda a, b: 7)
    row = A(["#000000", "#ffffff"])["pairs"][0]
    assert row["aa"] is True and row["aaa"] is True
    monkeypatch.setattr(c, "contrast_ratio", lambda a, b: 4.4999)
    assert A(["#000000", "#ffffff"])["pairs"][0]["aa"] is False
    monkeypatch.setattr(c, "contrast_ratio", lambda a, b: 6.9999)
    assert A(["#000000", "#ffffff"])["pairs"][0]["aaa"] is False
