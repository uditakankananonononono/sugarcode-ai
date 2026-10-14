import pytest
from sugarcode.extra_doc.performance_testing607 import measure_sort as run


def test_clock_spy_exact_duration_aggregation_and_no_mutation(monkeypatch):
    import sugarcode.extra_doc.performance_testing607 as m
    ticks=iter([100,107,200,202,300,311])
    monkeypatch.setattr(m.time,'perf_counter_ns',lambda:next(ticks))
    values=[3,-1,3,0]
    assert run(values,3)=={'sorted_values':[-1,0,3,3],'durations_ns':[7,2,11],
                          'minimum_ns':2,'maximum_ns':11,'mean_ns_fraction':'20/3','repetitions':3}
    assert values==[3,-1,3,0]
    with pytest.raises(StopIteration):next(ticks)


def test_backward_clock_refused(monkeypatch):
    import sugarcode.extra_doc.performance_testing607 as m
    ticks=iter([2,1]);monkeypatch.setattr(m.time,'perf_counter_ns',lambda:next(ticks))
    with pytest.raises(RuntimeError,match='^monotonic clock moved backward$'):run([1],1)


@pytest.mark.parametrize('bad',[None,(),True,{},'x'])
def test_outer_type(bad):
    with pytest.raises(TypeError,match='^exact integer list required$'):run(bad,1)


@pytest.mark.parametrize('n',[0,257])
def test_value_cap_before_scan(n):
    with pytest.raises(ValueError,match='^value count must be 1..256$'):run([None]*n,1)


@pytest.mark.parametrize('bad',[None,True,1.0,'1',[],{}])
def test_repetition_type(bad):
    with pytest.raises(TypeError,match='^exact nonbool repetition integer required$'):run([1],bad)


@pytest.mark.parametrize('bad',[0,33])
def test_repetition_cap(bad):
    with pytest.raises(ValueError,match='^repetition count must be 1..32$'):run([1],bad)


@pytest.mark.parametrize('bad',[None,True,1.0,'1',[],{}])
def test_each_element_type(bad):
    for position in (0,1,2):
        values=[1,2,3];values[position]=bad
        with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(values,1)


@pytest.mark.parametrize('bad',[-1000001,1000001])
def test_element_cap(bad):
    with pytest.raises(ValueError,match='^integer outside declared range$'):run([bad],1)


def test_validation_before_clock_and_cap_endpoints(monkeypatch):
    import sugarcode.extra_doc.performance_testing607 as m
    monkeypatch.setattr(m.time,'perf_counter_ns',lambda:pytest.fail('clock before validation'))
    with pytest.raises(TypeError):run([None],1)
    monkeypatch.setattr(m.time,'perf_counter_ns',lambda:0)
    assert run([-1000000,1000000]*128,32)['durations_ns']==[0]*32
    assert run([1],1)['mean_ns_fraction']=='0'


def test_real_clock_measurement_shape_without_speed_claim():
    result=run(list(reversed(range(16))),2)
    assert result['sorted_values']==list(range(16))
    assert len(result['durations_ns'])==2 and all(type(n) is int and n>=0 for n in result['durations_ns'])


def test_every_repetition_executes_sort_inside_timed_interval(monkeypatch):
    import builtins
    import sugarcode.extra_doc.performance_testing607 as module
    events=[]
    def clock():
        events.append('clock')
        return 0
    def sort(values):
        events.append('sort')
        return builtins.sorted(values)
    monkeypatch.setattr(module.time,'perf_counter_ns',clock)
    monkeypatch.setattr(module,'sorted',sort,raising=False)
    assert run([3,1,2],4)['sorted_values']==[1,2,3]
    assert events==['clock','sort','clock']*4
    assert events.count('sort')==4
