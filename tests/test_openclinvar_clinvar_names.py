"""ClinVar-style variant names (transcript + gene + c. core + protein change)
must parse to the right consequence and build a query ClinVar resolves.
Regression for the mega27-01 held-out validation: before this fix every one
of 500 real ClinVar names parsed to 'unknown' and the live query never hit."""
import pytest
from sugarcode.modules.openclinvar import core as oc
from sugarcode.bio import entrez


@pytest.mark.parametrize("name,expected", [
    ("NM_000038.6(APC):c.1668T>C (p.Asp556=)", "synonymous"),
    ("NM_000834.5(GRIN2B):c.3685G>A (p.Val1229Met)", "missense"),
    ("NM_000546.6(TP53):c.916C>T (p.Arg306Ter)", "nonsense"),
    ("NM_007294.4(BRCA1):c.5266dup (p.Gln1756fs)", "frameshift"),
    ("NM_000492.4(CFTR):c.1521_1523del (p.Phe508del)", "inframe_indel"),
    ("NM_007294.4(BRCA1):c.594-2A>C", "splice_disruption"),
    ("NM_000038.6(APC):c.*100A>G", "utr"),
    ("NM_024844.5(NUP85):c.361+25G>A", "intronic"),
    ("NM_024844.5(NUP85):c.361+18G>A", None),   # splice region stays undetermined
    ("p.Arg518Ser", "missense"),
    ("p.(Arg273His)", "missense"),
    ("c.68_69delAG", "frameshift"),
])
def test_consequence_from_clinvar_names(name, expected):
    assert oc._consequence_from_hgvs(name) == expected


def test_normalize_splits_levels():
    n = oc.normalize_hgvs("NM_000038.6(APC):c.1668T>C (p.Asp556=)")
    assert n == {"raw": "NM_000038.6(APC):c.1668T>C (p.Asp556=)", "transcript": "NM_000038.6",
                 "gene": "APC", "c": "c.1668T>C", "p": "p.Asp556="}


def test_interpret_variant_no_longer_unknown():
    r = oc.interpret_variant("TP53", "NM_000546.6(TP53):c.916C>T (p.Arg306Ter)")
    assert r["consequence"] == "nonsense"
    assert r["classification"] == "pathogenic"
    r = oc.interpret_variant("APC", "NM_000038.6(APC):c.1668T>C (p.Asp556=)")
    assert r["consequence"] == "synonymous" and "benign" in r["classification"]


def test_clinvar_query_drops_protein_suffix():
    assert entrez.clinvar_query("APC", "NM_000038.6(APC):c.1668T>C (p.Asp556=)") == '"NM_000038.6:c.1668T>C"'
    # bare notation keeps the historical gene-scoped phrase form
    assert entrez.clinvar_query("BRCA1", "c.5266dup") == 'BRCA1[gene] AND "c.5266dup"'
