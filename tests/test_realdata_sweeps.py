from sugarcode.modules.str_scope.core import find_strs, expansion_call


def test_homopolymer_does_not_hide_compound_repeat():
    # NC_001806.2 (HSV-1) 4125-4173: G-run flank then (GGGGTT)x4
    s = "GGCCCCTCCGGG" + "GGGGTT" * 4 + "GTTGAAGCGGAG"
    hits = [h for h in find_strs(s, 1, 6, 4) if h["unit_len"] == 6]
    assert hits and hits[0]["repeats"] == 4 and hits[0]["canonical_unit"] == "GGGGTT"


def test_adjacent_dinucleotide_runs_both_reported():
    # NG_005905.2 117405-117459: (TA)n directly followed by (CA)7
    s = "ATATGTTATATATATATATA" + "CA" * 7 + "TATATATGTATATATATATA"
    units = {h["canonical_unit"] for h in find_strs(s, 2, 2, 7)}
    assert {"AT", "AC"} <= units


def test_locus_bands_genereviews():
    assert expansion_call(27, 26, "CAG", "HTT")["classification"] == "intermediate range"
    assert expansion_call(38, 26, "CAG", "HTT")["classification"].startswith("reduced-penetrance")
    assert expansion_call(40, 26, "CAG", "HTT")["classification"].startswith("full-penetrance")
    assert expansion_call(26, 26, "CAG", "HTT")["classification"] == "normal range"
    assert expansion_call(80, 44, "CGG", "FMR1")["classification"] == "premutation range"
    assert expansion_call(201, 44, "CGG", "FMR1")["classification"] == "full mutation range"
    # no locus: legacy behaviour unchanged
    assert expansion_call(80, 44, "CGG")["classification"].startswith("expanded")


def test_acmg_clingen_suffix_notation():
    from sugarcode.modules.acmg_bayesian.core import bayesian_acmg
    a = bayesian_acmg(["PVS1_Strong", "PM2_Supporting", "PS4"])
    b = bayesian_acmg([{"code": "PVS1", "strength": "strong"}, {"code": "PM2", "strength": "supporting"}, "PS4"])
    assert a["points"] == b["points"] == 9 and not a["rejected_evidence"]
    assert bayesian_acmg(["PM3_Very Strong", "PP4_Moderate"])["points"] == 10
    assert bayesian_acmg(["BS1_Stand Alone"])["classification"] == "Benign"


def test_clinvar_stars_official_table():
    from sugarcode.modules.openclinvar.core import clinvar_stars
    table = {"no assertion criteria provided": 0, "no classification provided": 0,
             "no classification for the individual variant": 0,
             "criteria provided, conflicting classifications": 1,
             "criteria provided, single submitter": 1,
             "criteria provided, multiple submitters": 2,
             "criteria provided, multiple submitters, no conflicts": 2,
             "reviewed by expert panel": 3, "practice guideline": 4}
    assert {k: clinvar_stars(k) for k in table} == table


def test_hgvs_ranges_crossing_exon_boundaries():
    from sugarcode.modules.openclinvar.core import _consequence_from_hgvs as f
    assert f("NM_007294.4(BRCA1):c.5468-64_5480dup") == "splice_disruption"
    assert f("NM_000249.4(MLH1):c.453+625_545+920delinsT") == "splice_disruption"
    assert f("NM_000546.6(TP53):c.-19_*21del (p.Met1fs)") == "frameshift"
    assert f("NM_007294.4(BRCA1):c.5277+2916_5277+2946delinsGG") == "intronic"
    assert f("c.100+50_101-30del") == "intronic"


def test_power_estimate_matches_normal_power_solver():
    from sugarcode.modules.gene_analysis.core import power_estimate
    # statsmodels NormalIndPower, d = 0.5/0.5 = 1: power 0.5 -> 8, 0.8 -> 16, 0.95 -> 26
    assert power_estimate(0.5, 0.25, 0.5)["replicates_per_group"] == 8
    assert power_estimate(0.5, 0.25, 0.8)["replicates_per_group"] == 16
    assert power_estimate(0.5, 0.25, 0.95)["replicates_per_group"] == 26


def test_qsar_descriptors_rdkit_parity_cases():
    from sugarcode.modules.qsar_bench.chemistry import descriptors
    # tamoxifen-like stereo bonds parse; values match RDKit (MolWt, NonStrict rotors, FractionCSP3)
    d = descriptors("CC/C(=C(/CC)c1ccc(O)cc1)c1ccc(O)cc1")  # diethylstilbestrol
    assert d["heavy_atoms"] == 20 and abs(d["molecular_weight"] - 268.356) < 0.01
    assert d["rotatable_bonds_heuristic"] == 4 and abs(d["fraction_csp3"] - 4 / 18) < 1e-9
    d = descriptors("CN1CCC[C@H]1c1cccnc1")  # nicotine: 1 rotor, not 4
    assert d["rotatable_bonds_heuristic"] == 1
    d = descriptors("O=[N+]([O-])OC")  # bracket atoms get no implicit H
    assert abs(d["molecular_weight"] - 77.039) < 0.01
    d = descriptors("CCCC(CCC)C(=O)[O-].[Na+]")  # sodium valproate
    assert abs(d["molecular_weight"] - 166.196) < 0.01


def test_anm_hessian_rows_sum_to_zero_six_zero_modes():
    import numpy as np
    from sugarcode.modules.evofold_4d.core import anm_modes
    rng = np.random.default_rng(0)
    # compact random C-alpha cloud: connected network -> exactly 6 rigid-body zero modes skipped
    C = np.cumsum(rng.normal(0, 2.2, (40, 3)), axis=0) * 0.5
    out = anm_modes(C.tolist(), 6, 10.0)
    assert out["modes"][0]["index"] == 6
