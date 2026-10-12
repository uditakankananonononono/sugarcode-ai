import itertools
import pytest
from sugarcode.modules.chemgpt_engine.core import _parse_smiles, assemble_smiles, FRAGMENTS

@pytest.mark.parametrize('value',['C$C','C[N+]C','C[O-]','[NH4+]','C=','C()','C..C','C.C','C#N','C@C','C1','(CC)','C(=)C','C==O','C1C1','',None,True,'C'*10001])
def test_parser_refuses_out_of_subset_without_silent_token_loss(value):
    with pytest.raises(ValueError): _parse_smiles(value)

def test_supported_fragment_pairs_keep_graphs():
    for pair in itertools.product(FRAGMENTS,repeat=2):
        try:smiles=assemble_smiles(list(pair))
        except ValueError:continue
        nodes,edges=_parse_smiles(smiles)
        assert len(nodes)==sum(FRAGMENTS[f][1] for f in pair)
        assert all(0<=e['source']<len(nodes) and 0<=e['target']<len(nodes) for e in edges)
