"""Synthetic partition planning only, never model fitting."""
import pytest


def partition():
    from sugarcode.modules.prime_design.assay_data import plan_pridict2_partition
    return plan_pridict2_partition


def data():
    records=[]
    for group in range(12):
        for repeat in range(2):
            records.append(dict(seq_id=f'{group}_{repeat}',grp_id=str(group),
                outcomes={'HEK':(.2,.7,.1),'K562':None},
                test_folds={'HEK':group%5,'K562':None}))
    return {'records':records,'reuse_status':'DATA_REUSE_UNVERIFIED'}


def test_group_safe_complete_deterministic_and_missing_excluded():
    d=data();p=partition()(d,'HEK',0)
    assert p==partition()(d,'HEK',0)
    groups={k:{d['records'][i]['grp_id'] for i in p[k]} for k in ('train','validation','test')}
    assert all(groups[a].isdisjoint(groups[b]) for a,b in [('train','test'),('train','validation'),('validation','test')])
    assert sorted(p['train']+p['validation']+p['test'])==list(range(24))
    assert groups['test']=={'0','5','10'}
    assert p['validation'] and p['train']
    assert p['fitting_permitted'] is False
    assert partition()(d,'K562',0)['excluded_missing']==list(range(24))


def test_row_order_does_not_change_validation_groups():
    d=data();a=partition()(d,'HEK',0);d['records'].reverse();b=partition()(d,'HEK',0)
    ids_a={data()['records'][i]['seq_id'] for i in a['validation']}
    ids_b={d['records'][i]['seq_id'] for i in b['validation']}
    assert ids_a==ids_b


@pytest.mark.parametrize('cell,fold,fraction', [('wrong',0,.1),('HEK',True,.1),('HEK',5,.1),('HEK',0,0),('HEK',0,1),('HEK',0,float('nan'))])
def test_bad_partition_parameters(cell,fold,fraction):
    with pytest.raises(ValueError):partition()(data(),cell,fold,validation_fraction=fraction)


def test_mutated_group_fold_leakage_rejected():
    d=data();d['records'][1]['test_folds']['HEK']=2
    with pytest.raises(ValueError):partition()(d,'HEK',0)


def test_missing_label_cannot_have_fold():
    d=data();d['records'][0]['test_folds']['K562']=1
    with pytest.raises(ValueError):partition()(d,'K562',0)
