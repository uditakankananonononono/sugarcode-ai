import pytest
import json
from sugarcode.self_improve.approval_retention_plan import (
    RetentionLimits,InvalidRetentionPlan,prepare_current_policy_plan,replay_retention_plan)


def limits():
    return RetentionLimits(max_source_values=50000,max_source_bytes=4000000,
        max_active_values=10000,max_active_bytes=4000000,max_archive_values=10000,
        max_archive_bytes=4000000,max_manifest_bytes=4000000,max_depth=64)


@pytest.mark.parametrize('status',['approved','rejected','pending',None])
def test_terminal_age_or_status_never_makes_selection_eligible(status):
    state={'old':{'status':status,'requested_at':0}}
    with pytest.raises(InvalidRetentionPlan):prepare_current_policy_plan(state,archive_ids=('old',),limits=limits())
    assert state=={'old':{'status':status,'requested_at':0}}


def test_empty_policy_preserves_full_state_no_shards():
    state={'id':{'status':'approved','payload':{'full':['values',1]},'unknown':True}}
    plan=prepare_current_policy_plan(state,archive_ids=(),limits=limits())
    assert plan.archives==()
    assert json.loads(plan.active_json)==state
    assert json.loads(plan.manifest_json)['roles']=={'id':'unknown'}
    assert replay_retention_plan(manifest_json=plan.manifest_json,active_json=plan.active_json,retrieved={},limits=limits())==state


def test_capacity_refusal_does_not_make_exception_to_empty_eligibility():
    state={str(i):{'status':'rejected','payload':[1]*10} for i in range(1000)}
    with pytest.raises(InvalidRetentionPlan):prepare_current_policy_plan(state,archive_ids=(),limits=limits())
    assert len(state)==1000
