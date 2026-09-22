"""Drop 27: splice evidence inside openclinvar interpret_variant_live
(stack unification: rarenet panel has had it since drop 25)."""
import pytest

import sugarcode.modules.openclinvar.core as oc


def _mocks(monkeypatch, sa):
    """Neutralize live lookups; inject the splice assessment."""
    monkeypatch.setattr(oc.gnomad if hasattr(oc, "gnomad") else oc, "gene_constraint",
                        lambda g, offline=False: {"lof_constrained": False}) \
        if False else None
    from sugarcode.bio import gnomad, entrez
    monkeypatch.setattr(gnomad, "gene_constraint",
                        lambda g, offline=False: {"lof_constrained": False})
    monkeypatch.setattr(entrez, "clinvar_exact", lambda g, v, offline=False: [])
    import sugarcode.modules.deepsplice as ds
    monkeypatch.setattr(ds, "live_splice_assessment", lambda g, n, offline=False: sa)


def test_natural_site_loss_evidence(monkeypatch):
    _mocks(monkeypatch, {"status": "natural_site", "site_type": "donor", "delta": -0.25,
                         "consequence": "loss", "source": "fixture"})
    r = oc.interpret_variant_live("BRCA1", "c.212+1G>A")
    ev = next(e for e in r["evidence"] if e["rule"] == "SPLICE_PWM_LOSS")
    assert ev["weight"] == 0.4 and "1,802" in ev["detail"]
    assert r["splice_assessment"]["status"] == "natural_site"
    assert r["clinvar_live"]["status"].startswith("no live ClinVar")


def test_weakened_and_non_discriminating_weights(monkeypatch):
    _mocks(monkeypatch, {"status": "natural_site", "site_type": "donor", "delta": -0.08,
                         "source": "fixture"})
    r = oc.interpret_variant_live("G", "c.100+3A>G")
    assert next(e for e in r["evidence"] if e["rule"] == "SPLICE_PWM_WEAKENED")["weight"] == 0.1
    _mocks(monkeypatch, {"status": "natural_site", "site_type": "donor", "delta": -0.01,
                         "source": "fixture"})
    r = oc.interpret_variant_live("G", "c.100+4A>G")
    ev = next(e for e in r["evidence"] if e["rule"] == "SPLICE_PWM")
    assert ev["weight"] == 0.0 and "non-discriminating" in ev["detail"]


def test_cryptic_new_vs_weak(monkeypatch):
    _mocks(monkeypatch, {"status": "cryptic_scan",
                         "strong_findings": [{"type": "new_cryptic_site"}],
                         "verdict": "NEW cryptic donor site created (0.66 -> 0.92)"})
    r = oc.interpret_variant_live("CFTR", "c.3718-2477C>T")
    assert next(e for e in r["evidence"] if e["rule"] == "SPLICE_CRYPTIC_NEW")["weight"] == 0.3
    _mocks(monkeypatch, {"status": "cryptic_scan", "strong_findings": [],
                         "verdict": "3 weak site-strength perturbation(s)"})
    r = oc.interpret_variant_live("CFTR", "c.3718-1000C>T")
    ev = next(e for e in r["evidence"] if e["rule"] == "SPLICE_CRYPTIC")
    assert ev["weight"] == 0.0


def test_atypical_site_class_named(monkeypatch):
    _mocks(monkeypatch, {"status": "atypical_site_class", "site_class": "AT",
                         "detail": "minor spliceosome"})
    r = oc.interpret_variant_live("SCN1A", "c.383+1A>G")
    ev = next(e for e in r["evidence"] if e["rule"] == "SPLICE_SITE_CLASS")
    assert ev["weight"] == 0.0 and "not applicable" in ev["detail"]


def test_missense_untouched_and_failure_named(monkeypatch):
    _mocks(monkeypatch, {"status": "should not be called"})
    r = oc.interpret_variant_live("TP53", "p.Arg273His")
    assert "splice_assessment" not in r  # not a splice notation: never attempted

    def boom(g, n, offline=False):
        raise RuntimeError("network down")
    import sugarcode.modules.deepsplice as ds
    monkeypatch.setattr(ds, "live_splice_assessment", boom)
    r = oc.interpret_variant_live("BRCA1", "c.212+1G>A")
    assert r["splice_assessment"]["status"].startswith("lookup failed")


# --- (a) cdna_junction_map: transcript-isoform maps via CDS alignment --------

def _synth(ex1_end="CAG", intron1_head="GTGAGT", ex2_head="GT"):
    """Synthetic 3-exon gene. EX1 ends with ex1_end; intron starts
    intron1_head; EX2 starts ex2_head (set to make the exact-match
    extension overshoot the true boundary)."""
    import sugarcode.bio.splice as sp
    EX1 = "ACGTCAGTACGTCAGTACGTCAGTACGTCAGTACGT" + ex1_end
    IN1 = intron1_head + "T" * 22 + "AG"
    EX2 = ex2_head + "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCT"[:40 - len(ex2_head)]
    IN2 = "GT" + "C" * 28 + "AG"
    EX3 = "TTGGCCTTGGAACTTGGCCTTGGAACTTGGCCTTGGAAC"
    GSEQ = "A" * 50 + EX1 + IN1 + EX2 + IN2 + EX3 + "G" * 50
    CDNA = "TTATCGATTCGGTTAACCGG" + EX1 + EX2 + EX3 + "CCGGTAACCGGTTAAGGCCTTAA"
    cds_a = 21
    cds_b = 20 + len(EX1) + len(EX2) + len(EX3)
    e1a = 51; e1b = 50 + len(EX1)
    e2a = e1b + len(IN1) + 1; e2b = e2a + len(EX2) - 1
    e3a = e2b + len(IN2) + 1; e3b = e3a + len(EX3) - 1
    recs = {
        "NG_TEST": {"sequence": GSEQ, "features": [
            {"key": "mRNA", "spans": [(e1a, e1b), (e2a, e2b), (e3a, e3b)],
             "strand": 1, "qualifiers": {"transcript_id": "NM_OLD.1"}}]},
        "NM_TEST.1": {"sequence": CDNA, "features": [
            {"key": "CDS", "spans": [(cds_a, cds_b)], "strand": 1, "qualifiers": {}}]},
    }
    return sp, recs, {"EX1": EX1, "EX2": EX2, "EX3": EX3, "IN1": IN1, "IN2": IN2,
                      "e": (e1a, e1b, e2a, e2b, e3a, e3b)}


def _patch_records(monkeypatch, sp, recs):
    monkeypatch.setattr(sp, "refseqgene_accession", lambda g: "NG_TEST")
    monkeypatch.setattr(sp._entrez, "_get",
                        lambda ep, params, offline=False, **kw:
                        params["id"].encode())
    monkeypatch.setattr(sp, "_parse_gb", lambda txt: recs[txt])


def test_cdna_map_basic(monkeypatch):
    sp, recs, x = _synth(ex2_head="AC")   # unambiguous boundary
    _patch_records(monkeypatch, sp, recs)
    jm = sp.cdna_junction_map("GENE", "NM_TEST.1")
    assert jm["status"] == "ok" and jm["coverage"] == 1.0
    n1, n2 = len(x["EX1"]), len(x["EX2"])
    assert jm["donors"][n1] == x["EX1"][-3:] + x["IN1"][:6]
    assert jm["acceptors"][n1 + 1] == x["IN1"][-14:] + x["EX2"][:1]
    assert jm["donors"][n1 + n2] == x["EX2"][-3:] + x["IN2"][:6]
    assert [e["length"] for e in jm["exons"]] == [len(x["EX1"]), len(x["EX2"]), len(x["EX3"])]


def test_cdna_map_refines_overshot_boundary(monkeypatch):
    """EX2 starts with GT and the intron starts GTGAGT, so exact-match
    extension overshoots the true exon1|exon2 boundary by 2 nt. Refinement
    must snap it back to the canonical donor/acceptor."""
    sp, recs, x = _synth()
    _patch_records(monkeypatch, sp, recs)
    jm = sp.cdna_junction_map("GENE", "NM_TEST.1")
    n1 = len(x["EX1"])
    assert jm["donors"][n1] == "CAGGTGAGT"   # true boundary, canonical donor
    assert jm["acceptors"][n1 + 1][12:14] == "AG"


def test_cdna_map_reports_alternative_boundaries(monkeypatch):
    """Annotation's mRNA ends exon 1 six nt earlier than the cDNA aligns it
    (alternative donor). Reported as an alternative boundary, not fatal."""
    sp, recs, x = _synth()
    e1a, e1b, e2a, e2b, e3a, e3b = x["e"]
    recs["NG_TEST"]["features"][0]["spans"] = [(e1a, e1b - 6), (e2a, e2b), (e3a, e3b)]
    _patch_records(monkeypatch, sp, recs)
    jm = sp.cdna_junction_map("GENE", "NM_TEST.1")
    assert jm["status"] == "ok"
    alt = jm["alternative_splice_boundaries"]
    assert any("end@" in b["annotated"] for b in alt)


def test_cdna_map_failures_are_loud(monkeypatch):
    sp, recs, x = _synth()
    # no CDS feature
    recs2 = dict(recs)
    recs2["NM_TEST.1"] = {"sequence": recs["NM_TEST.1"]["sequence"], "features": []}
    _patch_records(monkeypatch, sp, recs2)
    assert "no CDS" in sp.cdna_junction_map("GENE", "NM_TEST.1")["status"]
    # CDS that does not align at all
    recs3 = dict(recs)
    recs3["NM_TEST.1"] = {"sequence": "G" * 200, "features": [
        {"key": "CDS", "spans": [(1, 180)], "strand": 1, "qualifiers": {}}]}
    _patch_records(monkeypatch, sp, recs3)
    assert "does not align" in sp.cdna_junction_map("GENE", "NM_TEST.1")["status"]
