"""Regression: mmCIF tokenizer/loop parser on constructs found in every real RCSB file (0/30 parsed before; 30/30 identical to gemmi after)."""
from sugarcode.bio import pdb as P

CIF = """data_TEST
loop_
_pdbx_audit_revision_item.ordinal
_pdbx_audit_revision_item.revision_ordinal
_pdbx_audit_revision_item.data_content_type
_pdbx_audit_revision_item.item
1 4 'Structure model' _database_2.pdbx_DOI
2 4 'Structure model' _database_2.pdbx_database_accession
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.auth_asym_id
_atom_site.auth_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.pdbx_PDB_model_num
HETATM 1 O "O5'" . NAG A 401 ? 1.000 2.000 3.000 1.00 20.00 1
HETATM 2 C C1' . NAG A 401 ? 1.500 2.500 3.500 1.00 21.00 1
"""


def test_primes_and_unquoted_item_values():
    s = P.parse_mmcif(CIF)
    assert [a["name"] for a in s["atoms"]] == ["O5'", "C1'"]
    assert s["atoms"][1]["x"] == 1.5


def test_split_cif_line_quotes():
    assert P._split_cif_line("a 'it''s' \"C1'\" O5' # c") == ["a", "it''s", "C1'", "O5'"]
