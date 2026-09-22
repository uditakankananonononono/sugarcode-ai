import math
import numpy as np
from sugarcode.modules.neuro_pipeline import *
def test_legacy_train_lesion_rsa():
 r=train(epochs=100); assert r['train_accuracy']>.8 and lesion_study(r['model'])['lesions'] and math.isfinite(rsa(r['model'])['rsa_correlation'])
def test_multimodal_alignment_has_shared_similarity():
 x=np.arange(24).reshape(6,4); r=align_modalities({'rna':x,'image':x[:,::-1]},2); assert r['embeddings'] and 'rna:image' in r['cross_modal_cosine']
def test_spiking_refractory_changes_trace():
 r=spiking_dynamics(np.ones((5,2)),threshold=1,refractory_steps=1); assert r['spikes'][0]==[1,1] and r['spikes'][1]==[0,0]
def test_predictive_coding_reduces_error():
 r=predictive_coding([[1,2],[2,3]]); assert r['prediction_error'][-1]<r['prediction_error'][0]
def test_continual_update_reports_drift():
 m=MLP(2,3,1); X=np.array([[0,0],[1,1]],float); y=np.array([[0],[1]],float); r=continual_update(m,X,y,epochs=2); assert r['parameter_drift']>0 and len(r['loss_curve'])==2
def test_functional_graph_uses_weights():
 m=MLP(2,3,1); assert functional_connectivity(m,0)['edges'] and functional_connectivity(m,100)['edges']==[]
def test_causal_intervention_records_individual_effects():
 m=MLP(2,3,1); X=np.array([[0,1],[2,1]],float); r=causal_intervention(m,X,0); assert len(r['individual_effects'])==2 and r['average_causal_effect']
def test_physics_cotraining_balances_targets():
 m=MLP(2,3,1); X=np.array([[0,0],[1,1]],float); y=np.array([[0],[1]],float); r=physics_cotraining(m,X,y,1-y,epochs=2); assert r['physics_mse']>=0 and r['data_mse']>=0
def test_feedback_reduces_uncertainty_with_evidence():
 assert feedback_reward_update(1,1,[1]*20)['uncertainty']<feedback_reward_update(1,1,[])['uncertainty']
def test_report_complete_and_honest():
 r=pipeline_report(); assert r['connectivity'] and r['causal'] and r['feedback'] and 'no biological foundation model' in r['model_status']
def test_diagnostics_honest_finite():
 d=neuro_diagnostics(); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
