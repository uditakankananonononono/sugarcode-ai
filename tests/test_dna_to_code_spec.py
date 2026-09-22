from sugarcode.modules.dna_to_code import *
def test_legacy(): assert translate_concept('PCR')['python']
def test_transcription(): assert execute_transcription('ATGT')=='AUGU'
def test_translation(): assert execute_translation('AUGGCCUAA')=='MA'
def test_mutation(): assert execute_mutation('ATGGCC',3,'T')['mutant_dna']=='ATGTCC'
def test_limits(): assert analogy_limits('crispr')['limits']
def test_report(): assert 'no biological prediction model' in concept_report('transcription','ATG')['model_status']
