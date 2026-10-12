"""Every returned educational source block must run in a clean namespace."""
import pytest
from sugarcode.modules.dna_to_code.core import translate_concept

def snippet(name):
    namespace = {}
    exec(translate_concept(name)['python'], namespace)
    return namespace

@pytest.mark.parametrize('name,function,args,expected',[
    ('transcription','transcribe',('TAC',),'GUA'),
    ('translation','translate',('AUGGCUUAA',),['M','A']),
    ('pcr','pcr',('ACGT',('AC','GT'),2),['ACGT']*4),
    ('crispr','crispr_edit',('ACGT'*5+'AGG','ACGT'*5,'C'),
     ('ACGT'*5+'AGG')[:17]+'C'+('ACGT'*5+'AGG')[17:]),
    ('mutation','point_mutation',('ATGGCTTAA',5,'C'),
     {'silent':True,'missense':False,'nonsense':False}),
])
def test_returned_sources_call_without_ambient_helpers(name,function,args,expected):
    ns=snippet(name)
    assert ns[function](*args)==expected

def test_promoter_example_is_also_executable():
    assert snippet('gene_regulation')['Promoter']().expression_rate()==1.0

@pytest.mark.parametrize('name,function,args',[
    ('transcription','transcribe',('file:///etc/passwd',)),
    ('transcription','transcribe',('',)),
    ('transcription','transcribe',('A'*10001,)),
    ('translation','translate',('AUGG',)),
    ('translation','translate',('ATG',)),
    ('pcr','pcr',('ACGT',('AC','GT'),30)),
    ('pcr','pcr',('ACGT',('AC','GT'),True)),
    ('pcr','pcr',('ACGT',('AC','bad'),0)),
    ('mutation','point_mutation',('ATG',3,'A')),
    ('mutation','point_mutation',('ATG',True,'A')),
    ('mutation','point_mutation',('ATG',1,'XX')),
    ('crispr','crispr_edit',('ACGT'*5+'AGG','ACGT','C')),
])
def test_snippet_refuses_unsupported_inputs(name,function,args):
    with pytest.raises(ValueError): snippet(name)[function](*args)

def test_crispr_string_address_missing_or_ambiguous_never_silently_edits():
    ns=snippet('crispr')
    guide='ACGT'*5
    for seq in [guide+'AAA',(guide+'AGG')*2]:
        with pytest.raises(ns['OffTargetRisk']): ns['crispr_edit'](seq,guide,'A')

def test_translation_complete_code_stop_and_lowercase():
    ns=snippet('translation')
    assert len(ns['CODON_TABLE'])==64
    assert ns['translate']('augugguaa')==['M','W']
    assert ns['translate']('UAA')==[]

def test_pcr_bounded_default_and_literal_flanks():
    ns=snippet('pcr')
    assert len(ns['pcr']('ACGT',('AC','GT')))==16
    assert ns['pcr']('ACGT',('GG','TT'),2)==['ACGT']
    assert len(ns['pcr']('ACGT',('AC','GT'),10))==1024

def test_mutation_examples_are_coding_frame_string_comparisons():
    ns=snippet('mutation')
    assert ns['point_mutation']('ATGGCTTAA',3,'T')['missense']
    assert ns['point_mutation']('ATGTGGTAA',4,'A')['nonsense']
    assert ns['compile_protein']('atggcttaa')=='MA'

def test_every_returned_source_has_scope_and_only_fixed_local_helpers():
    for name in ('transcription','translation','pcr','crispr','gene_regulation','mutation'):
        packet=translate_concept(name)
        assert 'educational string analogy only' in packet['scope']
        assert 'no biological prediction' in packet['python']
        assert 'open(' not in packet['python']
        assert 'http' not in packet['python']


def test_public_concepts_strings_are_the_same_executable_examples():
    from sugarcode.modules.dna_to_code.core import CONCEPTS
    for name,record in CONCEPTS.items():
        assert record['code']==translate_concept(name)['python']
        namespace={};exec(record['code'],namespace)
        assert namespace['_sequence']('acgt','ACGT')=='ACGT'
