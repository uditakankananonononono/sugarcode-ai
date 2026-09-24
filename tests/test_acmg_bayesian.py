"""acmg_bayesian: Tavtigian et al. 2018 (Genet Med, PMID 29300386, PMC6336098).

Fixtures are the paper's own combining-rule rows (Table 2) and mixed-evidence
rows (Table 3): combined odds of pathogenicity and posterior as printed at
prior 0.10. Each expected value is checked to within one unit of the last
digit the paper prints.
"""
import math
import shutil
from pathlib import Path

import pytest

from sugarcode.modules.acmg_bayesian import (
    NCBIClient, STRENGTH_ODDS, bayesian_acmg, classify_points, evaluate_variant,
    posterior_from_points, summarize_clinvar)
from sugarcode.modules.acmg_bayesian.client import normalize_variant_notation, title_matches

FIXTURE_CACHE = Path(__file__).parent / "fixtures" / "acmg_ncbi_cache"

# (paper row, criteria, printed combined OP, printed posterior, model label)
TABLE2 = [
    ("Path (ia)", ["PVS1", "PS1"], "6548", "0.999", "Pathogenic"),
    ("Path (ib)", ["PVS1", "PM1", "PM2"], "6548", "0.999", "Pathogenic"),
    ("Path (ic)", ["PVS1", "PM1", "PP1"], "3148", "0.997", "Pathogenic"),
    ("Path (id)", ["PVS1", "PP1", "PP2"], "1514", "0.994", "Pathogenic"),
    # Paper: rule (ii) is mathematically only likely pathogenic under the model.
    ("Path (ii)", ["PS1", "PS2"], "350", "0.975", "Likely pathogenic"),
    ("Path (iiia)", ["PS1", "PM1", "PM2", "PM3"], "1514", "0.994", "Pathogenic"),
    ("Path (iiib)", ["PS1", "PM1", "PM2", "PP1", "PP2"], "1514", "0.994", "Pathogenic"),
    ("Path (iiic)", ["PS1", "PM1", "PP1", "PP2", "PP3", "PP4"], "1514", "0.994", "Pathogenic"),
    # Paper: LP rule (i) reaches the pathogenic range under the model.
    ("Likely Path (i)", ["PVS1", "PM1"], "1514", "0.994", "Pathogenic"),
    ("Likely Path (ii)", ["PS1", "PM1"], "81", "0.900", "Likely pathogenic"),
    ("Likely Path (iii)", ["PS1", "PP1", "PP2"], "81", "0.900", "Likely pathogenic"),
    ("Likely Path (iv)", ["PM1", "PM2", "PM3"], "81", "0.900", "Likely pathogenic"),
    ("Likely Path (v)", ["PM1", "PM2", "PP1", "PP2"], "81", "0.900", "Likely pathogenic"),
    ("Likely Path (vi)", ["PM1", "PP1", "PP2", "PP3", "PP4"], "81", "0.900", "Likely pathogenic"),
    ("Likely Benign (i)", ["BS1", "BP1"], "0.03", "0.0028", "Likely benign"),
    ("Likely Benign (ii)", ["BP1", "BP2"], "0.23", "0.025", "Likely benign"),
    ("Benign (ii)", ["BS1", "BS2"], "0.0028", "0.00032", "Benign"),
]
TABLE3 = [
    ("VS + 2 Mod Path + BP5", ["PVS1", "PM2", "PM6", "BP5"], "3148", "0.997", "Pathogenic"),
    ("2 Str Path + BP4", ["PS1", "PS2", "BP4"], "168", "0.949", "Likely pathogenic"),
    ("2 Str Path + BP4 + BP5", ["PS1", "PS2", "BP4", "BP5"], "81", "0.900", "Likely pathogenic"),
    ("2 Str Path + BS1", ["PS1", "PS2", "BS1"], "18.7", "0.675", "Uncertain significance"),
]


def _unit(printed: str) -> float:
    return 10 ** -len(printed.split(".")[1]) if "." in printed else 1.0


@pytest.mark.parametrize("row,criteria,op,post,label", TABLE2 + TABLE3, ids=[r[0] for r in TABLE2 + TABLE3])
def test_paper_table_rows(row, criteria, op, post, label):
    r = bayesian_acmg(criteria)
    assert abs(r["combined_odds_of_pathogenicity"] - float(op)) <= _unit(op)
    assert abs(r["posterior_probability_pathogenic"] - float(post)) <= _unit(post)
    assert r["classification"] == label
    assert r["rejected_evidence"] == []


def test_all_five_likely_pathogenic_rules_at_0900_are_likely_pathogenic():
    lp = [r for r in TABLE2 if r[0] in {f"Likely Path ({x})" for x in ("ii", "iii", "iv", "v", "vi")}]
    assert len(lp) == 5
    for _, criteria, *_ in lp:
        r = bayesian_acmg(criteria)
        assert r["points"] == 6
        # exact 350**0.75 odds: the paper's "OP of 81 ... convert 0.10 to 0.90"
        assert math.isclose(r["combined_odds_of_pathogenicity"], 350 ** 0.75)
        assert r["classification"] == "Likely pathogenic"
        assert r["uncertainty"]["is_vus"] is False


def test_exact_odds_are_350_to_one_over_two_to_k():
    for k, s in enumerate(["very_strong", "strong", "moderate", "supporting"]):
        assert math.isclose(STRENGTH_ODDS[s], 350 ** (1 / 2 ** k))
    # the paper's printed rounded values
    assert round(STRENGTH_ODDS["strong"], 1) == 18.7
    assert round(STRENGTH_ODDS["moderate"], 1) == 4.3
    assert round(STRENGTH_ODDS["supporting"], 2) == 2.08
    assert round(1 / STRENGTH_ODDS["strong"], 3) == 0.053
    assert round(1 / STRENGTH_ODDS["supporting"], 2) == 0.48


def test_point_bands_equal_posterior_bands_except_the_lp_floor():
    for pts in range(-16, 17):
        p = posterior_from_points(pts)
        label = classify_points(pts)
        if p > 0.99:
            assert label == "Pathogenic"
        elif p >= 0.90 or pts == 6:          # 6 points = the paper's 0.900
            assert label == "Likely pathogenic"
        elif p < 0.001:
            assert label == "Benign"
        elif p < 0.10 - 1e-12:
            assert label == "Likely benign"
        else:
            assert label == "Uncertain significance"


def test_ba1_is_stand_alone_override_outside_the_model():
    r = bayesian_acmg(["BA1"])
    assert r["classification"] == "Benign"
    assert r["posterior_excludes_ba1"] is True
    assert r["points"] == 0 and math.isclose(r["posterior_probability_pathogenic"], 0.10)
    assert r["stand_alone_evidence"][0]["code"] == "BA1"
    r = bayesian_acmg(["BA1", "PVS1", "PS1"])
    assert r["classification"] == "Benign"
    assert r["points"] == 12            # posterior of the other evidence, reported separately
    assert r["directional_conflict"] is True
    assert any("BA1 coexists" in x for x in r["uncertainty"]["reasons"])
    r = bayesian_acmg([{"code": "BA1", "strength": "strong"}])
    assert r["classification"] == "Uncertain significance" and len(r["rejected_evidence"]) == 1


def test_no_evidence_and_balanced_evidence_stay_vus():
    assert bayesian_acmg([])["classification"] == "Uncertain significance"
    r = bayesian_acmg(["PP1", "BP1"])
    assert r["points"] == 0 and r["classification"] == "Uncertain significance"


def test_strength_modification_and_rejection():
    r = bayesian_acmg([{"code": "PM2", "strength": "supporting", "provenance": "ClinGen SVI PM2_Supporting"},
                       {"code": "pvs1", "strength": "strong"}, "XX9", {"code": "PS3", "strength": "huge"}])
    codes = {x["code"]: x for x in r["accepted_evidence"]}
    assert codes["PM2"]["points"] == 1 and codes["PM2"]["modified"] is True
    assert codes["PVS1"]["points"] == 4
    assert r["points"] == 5 and r["classification"] == "Uncertain significance"
    assert len(r["rejected_evidence"]) == 2


def test_non_default_prior():
    r = bayesian_acmg(["PS1", "PM1"], prior_probability=0.25)
    assert r["classification_basis"].startswith("posterior bands")
    odds = (0.25 / 0.75) * 350 ** 0.75
    assert math.isclose(r["posterior_probability_pathogenic"], odds / (1 + odds))
    assert r["classification"] == "Likely pathogenic"
    with pytest.raises(ValueError):
        bayesian_acmg([], prior_probability=1.0)


def test_hgvs_normalisation_and_title_matching():
    assert normalize_variant_notation("NM_007294.4:c.68_69delAG") == "c.68_69del"
    assert normalize_variant_notation("c.5266dupC") == "c.5266dup"
    assert normalize_variant_notation("c.100_101delinsTT") == "c.100_101delinsTT"
    assert title_matches("NM_007294.4(BRCA1):c.68_69del (p.Glu23fs)", "c.68_69del")
    assert not title_matches("NM_007294.4(BRCA1):c.68_69delinsT", "c.68_69del")
    assert not title_matches("NM_007294.4(BRCA1):c.68_69dup", "c.68_69del")


def _offline_client(tmp_path):
    cache = tmp_path / "cache"
    shutil.copytree(FIXTURE_CACHE, cache)
    return NCBIClient(cache_dir=cache)


def test_recorded_clinvar_lookup_offline(tmp_path):
    # Recorded live NCBI E-utilities responses (2026-09-24).
    r = evaluate_variant("BRCA1", "NM_007294.4:c.68_69delAG", criteria=["PVS1", "PS3", "PM2"],
                         offline=True, client=_offline_client(tmp_path))
    cv = r["clinvar"]
    assert cv["query"] == 'BRCA1[gene] AND "c.68_69del"'
    assert cv["returned_record_count"] == 2 and cv["exact_record_count"] == 1
    exact = [x for x in cv["records"] if x["exact_notation_in_title"]][0]
    assert exact["variation_id"] == "17662"
    assert exact["review_status"] == "reviewed by expert panel"
    assert exact["url"] == "https://www.ncbi.nlm.nih.gov/clinvar/variation/17662/"
    # the unrelated c.1974G>C record is returned by search but never counted
    assert cv["consensus"] == "Pathogenic" and cv["classification_counts"] == {"Pathogenic": 1}
    assert r["bayesian_acmg"]["points"] == 14 and r["bayesian_acmg"]["classification"] == "Pathogenic"
    lit = r["literature"]
    assert len(lit["articles"]) == 10 and all(a["url"].startswith("https://pubmed.ncbi.nlm.nih.gov/") for a in lit["articles"])
    assert lit["screening_status"].startswith("unscreened")


def test_offline_cache_miss_is_missing_not_inferred(tmp_path):
    r = evaluate_variant("TP53", "NM_000546.6:c.817C>T", offline=True,
                         client=NCBIClient(cache_dir=tmp_path / "empty"))
    assert r["clinvar"]["consensus"] == "Missing" and r["clinvar"]["records"] == []
    assert r["literature"]["status"] == "Missing"
    assert r["bayesian_acmg"]["classification"] == "Uncertain significance"


def test_summary_never_counts_non_matching_records():
    recs = [{"exact_notation_in_title": False, "classification": "Benign", "review_status": "reviewed by expert panel"}]
    s = summarize_clinvar(recs)
    assert s["consensus"] == "Missing" and "1 non-matching" in s["warning"]


def test_registered():
    from omega.registry import REGISTRY
    assert REGISTRY["acmg_bayesian"].subnetwork == "therapeutics"
