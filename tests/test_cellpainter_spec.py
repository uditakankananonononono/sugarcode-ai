from sugarcode.modules.cellpainter import *
def test_legacy(): assert profile_perturbation('dna_damage')['signature_vector']
def test_normalize(): assert len(plate_normalize([[2,3]],[[1,1],[1.1,.9]])['normalized'])==1
def test_qc(): assert quality_control([100,105],[.9,.95],[.2,.3])['pass']
def test_batch(): assert abs(sum(batch_correct([[[1],[3]]])['batches'][0][0]))==1
def test_match():
 p=[profile_perturbation('dna_damage'),profile_perturbation('mitochondrial_toxin')]; assert nearest_mechanism(p[0],p)[0]['mechanism']=='dna_damage'
def test_trajectory(): assert len(concentration_trajectory('dna_damage',[1,2],[6,24])['profiles'])==4
def test_report():
 p=[profile_perturbation('dna_damage'),profile_perturbation('mitochondrial_toxin')]; assert 'no image segmentation' in cellpainting_report(p,[[1]*25,[1.1]*25])['model_status']
