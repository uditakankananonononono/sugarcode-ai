from sugarcode.modules.epi_edit import chromatin_landscape, design_epigenome_edit
from sugarcode.modules.openclinvar import interpret_variant, parse_vcf_line, clinical_summary

SEQ = ("AATT" * 100) + ("CAGG" * 60) + ("TTAA" * 100)


def test_landscape_track():
    L = chromatin_landscape(SEQ, promoter_span=(400, 600))
    assert L["track"] and L["promoter_region"]
    assert all(0 <= t["accessibility"] <= 1 for t in L["track"])


def test_crispri_design():
    r = design_epigenome_edit(SEQ, (400, 500), mode="CRISPRi")
    assert r["non_permanent"]
    assert r["predicted_effect"]["direction"] == "repression"
    assert r["predicted_effect"]["fold_change"] <= 1.0


def test_interpret_known_variant():
    r = interpret_variant("CFTR", "p.Phe508del")
    assert r["classification"] == "pathogenic"
    assert "plain_language" in r


def test_interpret_common_benign():
    r = interpret_variant("GENE", "c.100A>G", consequence="missense", allele_frequency=0.2)
    assert r["classification"] in ("benign", "likely_benign")


def test_vcf_parse():
    v = parse_vcf_line("chr7\t117559590\t.\tATC\tA\t100\tPASS\tDP=50")
    assert v["chrom"] == "chr7" and v["ref"] == "ATC"


def test_clinical_summary_report():
    s = clinical_summary("BRCA1", "c.68_69delAG")
    assert "Discuss" in s["patient_report"]["what_it_means"]
