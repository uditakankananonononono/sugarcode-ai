from sugarcode.modules.dna_to_code import *
def test_legacy(): assert translate_concept('PCR')['python']
def test_transcription(): assert execute_transcription('ATGT')=='AUGU'
def test_translation(): assert execute_translation('AUGGCCUAA')=='MA'
def test_mutation(): assert execute_mutation('ATGGCC',3,'T')['mutant_dna']=='ATGTCC'
def test_limits(): assert analogy_limits('crispr')['limits']
def test_report(): assert 'no biological prediction model' in concept_report('transcription','ATG')['model_status']
def test_mutation_consequence_terms():
    s='ATGGCCTGGTAA'
    assert execute_mutation(s,0,'C')['consequence']=='start_lost'
    assert execute_mutation(s,9,'C')['consequence']=='stop_lost'
    assert execute_mutation(s,11,'G')['consequence']=='stop_retained_variant'
    assert execute_mutation(s,8,'A')['consequence']=='stop_gained'
    assert execute_mutation(s,5,'T')['consequence']=='synonymous_variant'
    assert execute_mutation(s,4,'A')['consequence']=='missense_variant'
def test_transcription_snippet_uses_template_complement():
    code=translate_concept('transcription')['python']
    assert 'reversed' in code and "'A': 'U'" in code
