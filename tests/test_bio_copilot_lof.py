"""BUG 53 regression: premature stops in loss-of-function genes must reach the
pathogenic band (ClinVar: TP53 R213* uid 43590, BRCA1 Q563* uid 37426), while
oncogene nonsense must NOT be floored (KRAS L168* uid 4915976 Likely benign)."""
from sugarcode.modules.bio_copilot import mutation_to_phenotype


def test_nonsense_lof_genes_floored_to_likely_pathogenic():
    for gene, ref, pos in [("TP53", "R", 213), ("BRCA1", "Q", 563)]:
        r = mutation_to_phenotype(gene, ref, pos, "*")
        assert r["phenotype"] == "likely pathogenic" and r["risk_score"] == 0.75


def test_nonsense_oncogene_not_floored_and_flagged():
    r = mutation_to_phenotype("KRAS", "L", 168, "*")
    assert r["phenotype"] == "uncertain significance" and r["risk_score"] == 0.65
    assert any("oncogene" in f for f in r["inconsistency_flags"])


def test_nonsense_at_hotspot_keeps_hotspot_bonus():
    r = mutation_to_phenotype("TP53", "R", 175, "*")
    assert r["risk_score"] == 0.9 and r["phenotype"] == "likely pathogenic"


def test_missense_calls_unchanged_by_fix():
    assert mutation_to_phenotype("TP53", "P", 72, "R")["risk_score"] == 0.19
    assert mutation_to_phenotype("KRAS", "G", 12, "D")["risk_score"] == 0.82


def test_annotation_node_reports_lof_mechanism():
    assert mutation_to_phenotype("TP53", "R", 213, "*")["computation_graph"][0]["lof_mechanism_gene"] is True
    assert mutation_to_phenotype("KRAS", "L", 168, "*")["computation_graph"][0]["lof_mechanism_gene"] is False
