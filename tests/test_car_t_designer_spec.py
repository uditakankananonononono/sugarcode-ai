from sugarcode.modules.car_t_designer import *
def test_legacy(): assert design_car('CD19')['construct']['scfv']=='FMC63'
def test_selectivity(): assert antigen_selectivity(100,1)['selective']
def test_logic(): assert logic_gate_response(.8,.2,'A_NOT_B')['active']
def test_logic_and(): assert not logic_gate_response(.8,.2,'AND')['active']
def test_exhaustion(): assert exhaustion_trajectory([0,14],1,'CD28')['exhaustion_fraction'][1] > exhaustion_trajectory([0,14],1,'4-1BB')['exhaustion_fraction'][1]
def test_kill(): assert killing_curve([1,10])['target_kill_fraction'][1] > killing_curve([1,10])['target_kill_fraction'][0]
def test_scope(): assert 'not clinically validated' in car_report('BCMA')['validation_scope']
def test_indication_mismatch_flagged():
 assert 'indication_note' in design_car('CD19',indication='multiple myeloma')
 assert 'indication_note' not in design_car('CD19',indication='B-ALL')
def test_placeholder_scfv_flagged():
 r=design_car('CLDN18.2')
 assert r['construct']['scfv']=='generic_high_affinity' and 'scfv_note' in r['construct']
 assert 'scfv_note' not in design_car('CD19')['construct']
def test_toxicity_labeled_class_level():
 assert 'model' in design_car('CD19')['toxicity_prediction']
