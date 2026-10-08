"""Real candidate pytest, local approval, activation and dispatch."""
import pytest
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.plans import Candidate,FeaturePlan
from sugarcode.self_improve.gate import APPROVED

def rig(tmp_path):
 from sugarcode.self_improve.activation_guard import ActivationGuard
 e=SelfImprovementEngine(module_id=1,module_slug='software-test',state_dir=tmp_path/'state')
 p=FeaturePlan(module_slug='software-test',name='normalize_text',kind='text_transform',description='normalize whitespace',gap_signature='whitespace')
 c=Candidate(p,'def run(items, params=None):\n return {"items": [" ".join(x.split()) for x in items]}\n','from feature import run\ndef test_real():\n assert run(["a   b"]) == {"items": ["a b"]}\n')
 e._candidates[c.key]=c
 return e,c,ActivationGuard(e,tmp_path/'guard.sqlite')
def test_actual_evaluate_activate_dispatch_and_replay(tmp_path):
 e,c,g=rig(tmp_path);g.evaluate(c.key);aid=g.propose(c.key);e.gate.decide(aid,APPROVED)
 g.activate(c.key,aid);assert e.dispatch(c.plan.name,['a   b'])=={'items':['a b']}
 with pytest.raises(PermissionError):g.activate(c.key,aid)
def test_no_evaluation_or_changed_tests_refused(tmp_path):
 e,c,g=rig(tmp_path)
 with pytest.raises(PermissionError):g.propose(c.key)
 g.evaluate(c.key);aid=g.propose(c.key);e.gate.decide(aid,APPROVED)
 proposal=e.registry.get_proposal(c.key)
 from pathlib import Path
 Path(proposal['test_file']).write_text('def test_other():pass')
 with pytest.raises(PermissionError):g.activate(c.key,aid)
def test_wrong_action_approval_cannot_rollback(tmp_path):
 e,c,g=rig(tmp_path);g.evaluate(c.key);aid=g.propose(c.key);e.gate.decide(aid,APPROVED);g.activate(c.key,aid)
 with pytest.raises(PermissionError):g.rollback(c.plan.name,aid)
 rollback=g.request_rollback(c.plan.name);e.gate.decide(rollback,APPROVED);g.rollback(c.plan.name,rollback)
