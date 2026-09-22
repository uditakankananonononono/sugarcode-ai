"""Round-3 splice goldens - 11 more harvested genes (drop 29): CHEK2, PALB2,
MUTYH, F8, DMD, MYH7, PKD1, TSC1, TSC2, HBB, VHL. GJB2 is deliberately
absent: its CDS is a single exon (intronless coding sequence, verified live
on NG_008358.1), so there are no CDS splice junctions to golden; its ClinVar
splice variants are 5'-UTR (c.-23+1G>A, c.-22-2A>C), outside the
CDS-boundary harness - documented in STATUS.

Transcript discipline (all verified live 2026-09-22): ClinVar's cited NM_
per gene came from a --diagnose pass over live ClinVar titles; for the 10
in-record transcripts a paired-CDS probe verified the cited transcript's
CDS spans EXACTLY equal the RefSeqGene canonical CDS (native numbering).
MUTYH's cited NM_001048174 is NOT annotated on NG_008189.1, so its map is
built with the drop-27 cdna_junction_map (NM_001048174.2 CDS aligned to the
genomic record).

Pooled 28-gene totals (hermetic, also reproduced by
scripts/pooled_splice_stats.py): 2,700 pathogenic + 86 benign; ALL 2,405
canonical U2 sites called loss (100%); all 8 canonical AT-AC called loss
with U12 matrices; benign specificity 85/86 (the one FP is the documented
BRCA1 c.594-2A>C).
"""
import json
import re
from pathlib import Path

import pytest

NEW_GENES = ["chek2", "palb2", "mutyh", "f8", "dmd", "myh7", "pkd1", "tsc1",
             "tsc2", "hbb", "vhl"]
FIX = {g: json.loads(Path(f"tests/fixtures/{g}_splice_golden.json").read_text())
       for g in NEW_GENES}
EXPECTED = {"chek2": (28, 3), "palb2": (36, 0), "mutyh": (15, 1), "f8": (18, 0),
            "dmd": (195, 3), "myh7": (8, 2), "pkd1": (77, 6), "tsc1": (55, 0),
            "tsc2": (168, 6), "hbb": (25, 0), "vhl": (16, 2)}


def _k(case):
    return int(re.search(r"[+-](\d+)", case["notation"]).group(1))


def _cls(case):
    from sugarcode.modules.deepsplice import site_class
    return site_class(case["window"], case["site_type"])


@pytest.mark.parametrize("gene", NEW_GENES)
def test_round3_fixture_size_and_canonical_capture(gene):
    path, ben = FIX[gene]["pathogenic"], FIX[gene]["benign"]
    assert (len(path), len(ben)) == EXPECTED[gene]
    canon = [c for c in path if _k(c) <= 2 and _cls(c) in ("GT", "GC", "AG")]
    misses = [c["notation"] for c in canon if c["delta"] > -0.15]
    assert misses == [], f"{gene} canonical misses: {misses}"


def test_mutyh_map_is_cdna_aligned_nm_001048174():
    """MUTYH ClinVar cites NM_001048174 (beta3), absent from NG_008189.1 -
    the fixture must come from the cdna_junction_map path, not a remap."""
    assert "NM_001048174.2" in FIX["mutyh"]["source"]


def test_gjb2_deliberately_absent():
    assert not Path("tests/fixtures/gjb2_splice_golden.json").exists()


def test_pooled_28_gene_golden():
    old = ["brca1", "brca2", "mlh1", "cftr", "msh2", "tp53", "nf1", "apc", "atm",
           "ldlr", "mecp2", "msh6", "pah", "pms2", "pten", "rb1", "scn1a"]
    fix = {g: json.loads(Path(f"tests/fixtures/{g}_splice_golden.json").read_text())
           for g in old + NEW_GENES}
    path = [c for g in fix for c in fix[g]["pathogenic"]]
    ben = [c for g in fix for c in fix[g]["benign"]]
    assert (len(path), len(ben)) == (2700, 86)
    canon_u2 = [c for c in path if _k(c) <= 2 and _cls(c) in ("GT", "GC", "AG")]
    assert len(canon_u2) == 2405
    assert all(c["delta"] <= -0.15 for c in canon_u2)
    atac = [c for c in path if _k(c) <= 2 and _cls(c) in ("AT", "AC")]
    assert len(atac) == 8 and all(c["delta"] <= -0.15 for c in atac)
    tn = sum(1 for c in ben if c["delta"] > -0.15)
    assert (tn, len(ben)) == (85, 86)
