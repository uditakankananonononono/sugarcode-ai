"""Uncurated compounds stay in the ranking, are marked, and rank after curated ones."""
from sugarcode.modules.organoid_screen.core import screen

COMPOUNDS = ["zzz_uncurated_a", "cisplatin", "olaparib", "zzz_uncurated_b"]
IC50_BEFORE = {"olaparib": 1.211, "zzz_uncurated_a": 1.842, "zzz_uncurated_b": 1.842, "cisplatin": 2.791}
DEFAULT_SOURCE = "default (kill 0.4, 1.0 uM base)"


def test_rows_marked_curated_first_and_values_unchanged():
    r = screen("colon", COMPOUNDS, ["TP53"])
    rows = r["ranking"]
    assert [x["compound"] for x in rows] == ["olaparib", "cisplatin", "zzz_uncurated_a", "zzz_uncurated_b"]
    assert {x["compound"]: x["curated"] for x in rows} == {
        "olaparib": True, "cisplatin": True, "zzz_uncurated_a": False, "zzz_uncurated_b": False}
    assert {x["compound"]: x["ic50_uM"] for x in rows} == IC50_BEFORE
    assert all(("curve_source" in x) == (not x["curated"]) for x in rows)
    assert all(x["curve_source"] == DEFAULT_SOURCE for x in rows if not x["curated"])
    assert r["hit"] == "olaparib"
    assert r["uncurated_compounds"] == ["zzz_uncurated_a", "zzz_uncurated_b"]
    assert r["screened"] == 4


def test_all_curated_input_keeps_ic50_order():
    r = screen("colon", ["cisplatin", "olaparib"], [])
    assert [x["compound"] for x in r["ranking"]] == sorted(
        ["cisplatin", "olaparib"], key=lambda c: {x["compound"]: x["ic50_uM"] for x in r["ranking"]}[c])
    assert all(x["curated"] for x in r["ranking"])
