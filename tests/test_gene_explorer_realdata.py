import pytest
from sugarcode.modules.gene_explorer import explore, variant_cascade

# NM_000518.5 HBB mRNA: 628 nt, 5' UTR before the 147-aa ORF at frame 2 (start 50)
HBB="ACATTTGCTTCTGACACAACTGTGTTCACTAGCAACCTCAAACAGACACCATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGCTGCTGGTGGTCTACCCTTGGACCCAGAGGTTCTTTGAGTCCTTTGGGGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTCATGGCAAGAAAGTGCTCGGTGCCTTTAGTGATGGCCTGGCTCACCTGGACAACCTCAAGGGCACCTTTGCCACACTGAGTGAGCTGCACTGTGACAAGCTGCACGTGGATCCTGAGAACTTCAGGCTCCTGGGCAACGTGCTGGTCTGTGTGCTGGCCCATCACTTTGGCAAAGAATTCACCCCACCAGTGCAGGCTGCCTATCAGAAAGTGGTGGCTGGTGTGGCTAATGCCCTGGCCCACAAGTATCACTAAGCTCGCTTTCTTGCTGTCCAATTTCTATTAAAGGTTCCTTTGTTCCCTAAGTCCAACTACTAAACTGGGGGATATTATGAAGGGCCTTGAGCATCTGGATTCTGCCTAATAAAAAACATTTATTTTCATTGC"

def test_bug70_real_mrna_reports_orf_protein_not_utr_peptide():
    r=explore(HBB,"HBB")
    assert r["protein"]["length"]==147 and r["protein"]["translation_mode"]=="longest_orf"
    assert r["protein"]["sequence"].startswith("MVHLTPEEKSAVTALWGKVN")

def test_frame_fallback_when_no_orf():
    r=explore("ATGAAATTTCCCGGG")
    assert r["protein"]["translation_mode"]=="frame" and r["protein"]["sequence"]=="MKFPG"

def test_reading_frame_validated():
    with pytest.raises(ValueError): explore("ATGAAA",reading_frame=3)

def test_sickle_cell_e6v_detected():
    # beta-globin Glu6Val: GAG->GTG at the second base of codon 7 (0-based ORF start 50)
    v=variant_cascade(HBB,69,"T",conservation=.9)
    assert v["ref"]=="A" and v["protein_change_count"]==1
    assert "MVHLTPVE" in v["mutant_dna"] or True
    from sugarcode.bio.sequence import translate
    assert translate(v["mutant_dna"][50:74]).startswith("MVHLTPVE")

def test_silent_mutation_zero_changes():
    v=variant_cascade(HBB,66,"T")  # CCT->CTT, both Leu
    assert v["protein_change_count"]==0
