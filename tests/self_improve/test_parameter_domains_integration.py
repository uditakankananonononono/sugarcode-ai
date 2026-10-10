import pytest
from dataclasses import replace
from sugarcode.self_improve.codegen import synthesize_code
from sugarcode.self_improve.plans import FeaturePlan, CAPABILITY_KINDS
from sugarcode.self_improve.parameter_domains import ParameterDomainError
from sugarcode.self_improve.domain_source import GENERATED_VALIDATOR_SOURCE
from sugarcode.self_improve.planner import FeaturePlanner
from sugarcode.self_improve.detector import CapabilityGap
from pathlib import Path


def plan(kind,params=None):
    return FeaturePlan('m','domain_case',kind,'test','gap',{} if params is None else params)


def generated(kind,params=None):
    ns={};exec(synthesize_code(plan(kind,params)),ns);return ns


def test_embedded_validator_exact_source_parity():
    from sugarcode.self_improve import parameter_domains
    source=Path(parameter_domains.__file__).read_text()
    expected=source[source.index('import math\n'):].replace('from typing import Any\n','').replace(': Any',': object')
    assert GENERATED_VALIDATOR_SOURCE==expected


@pytest.mark.parametrize('kind',CAPABILITY_KINDS)
@pytest.mark.parametrize('bad',[False,[],(),'',0])
def test_actual_generated_runtime_falsey_params_refuse(kind,bad):
    ns=generated(kind)
    with pytest.raises(ValueError):ns['run']([],bad)


@pytest.mark.parametrize('kind',CAPABILITY_KINDS)
def test_actual_synthesis_and_runtime_unknown_keys_refuse(kind):
    with pytest.raises(ParameterDomainError):synthesize_code(plan(kind,{'extra':1}))
    ns=generated(kind)
    with pytest.raises(ValueError):ns['run']([],{'extra':1})


@pytest.mark.parametrize('kind',CAPABILITY_KINDS)
def test_actual_runtime_custom_list_refuses(kind):
    class Hostile(list):
        def __iter__(self):pytest.fail('custom iteration invoked')
    ns=generated(kind)
    with pytest.raises(ValueError):ns['run'](Hostile())


def test_actual_empty_weights_override_repairs_fallback():
    ns=generated('scoring_rule',{'weights':{'alpha':9}})
    assert ns['score_item']('alpha',{})==0
    assert ns['score_item']('alpha')==9
    assert ns['run'](['alpha'],{'weights':{}})['scored'][0]['score']==0
    for weights in ({'alpha':float('nan')},{'a':True},{'A':1,'a':2}):
        with pytest.raises(ValueError):ns['score_item']('alpha',weights)


@pytest.mark.parametrize('kind,params,rows',[
 ('aggregator',{},[{'category':1},{'category':'1'}]),
 ('aggregator',{},[{}, {'category':'<missing>'}]),
 ('aggregator',{'op':'sum'},[{'value':True}]),
 ('aggregator',{'op':'sum'},[{'value':1e308},{'value':1e308}]),
 ('threshold_alert',{},[{'value':'nan'}]),
 ('threshold_alert',{},[{'value':float('inf')}]),
 ('threshold_alert',{},[{'value':True}]),
])
def test_actual_numeric_preflight_refuses_without_partial_result(kind,params,rows):
    ns=generated(kind,params)
    with pytest.raises(ValueError):ns['run'](rows)


def test_actual_threshold_numeric_strings_retained():
    ns=generated('threshold_alert')
    assert ns['run']([{'value':'2'},{'value':'bad'}])['skipped']==1
    assert len(ns['run']([{'value':'2'}])['flagged'])==1


@pytest.mark.parametrize('params',[{'mode':'bad'},{'keywords':('a',)},{'keywords':['A','a']}])
def test_real_post_refiner_domain_gate(params):
    class Refiner:
        def refine(self,p,g):return replace(p,params=params)
    gap=CapabilityGap(module_slug='m',signature='filter gap',detail='',occurrences=2,first_seen=0,last_seen=0,kinds=(),exemplars=(),severity=0.5)
    with pytest.raises(ParameterDomainError):FeaturePlanner(Refiner()).plan(gap)


def test_actual_regex_and_replacement_validate_before_empty_iteration():
    ns=generated('text_transform')
    for params in ({'pattern':'['},{'replacement':r'\9'}):
        with pytest.raises(ValueError):ns['run']([],params)


def test_parameter_numeric_coercion_and_weight_overflow_refuse_at_synthesis():
    for params in ({'threshold':'1'},{'threshold':True},{'weights':{'a':1e308,'b':1e308}}):
        with pytest.raises(ParameterDomainError):synthesize_code(plan('scoring_rule',params))
