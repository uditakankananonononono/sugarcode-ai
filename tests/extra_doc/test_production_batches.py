import itertools
import re
import pytest
from sugarcode.extra_doc.production_batches import batches
class Number(int): pass

def oracle(units,batch_size,duration):
    count = (units+batch_size-1)//batch_size
    sizes=[]; finishes=[]
    for i in range(count):
        left=units-i*batch_size
        sizes.append(left if left<batch_size else batch_size)
        finishes.append(duration*(i+1))
    return {'production_batches_validated':False,
            'not_claimed':('machine_assignment','real_schedule','feasibility'),
            'sizes':tuple(sizes),'finish_slots':tuple(finishes),
            'batch_count':count,'total_duration':duration*count}

def test_oracle():
    for args in itertools.product(range(1,16), range(1,10), (1,2,100)):
        assert batches(*args)==oracle(*args)

def test_caps():
    for args in itertools.product((1,9999,10000),(1,999,1000),(1,99,100)):
        assert batches(*args)==oracle(*args)

def test_types_and_bounds_and_order():
    for pos,(name,cap) in enumerate((('units',10000),('batch_size',1000),('duration',100))):
        for bad in (0,-1,cap+1,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            args=[1,1,1]; args[pos]=bad
            with pytest.raises(ValueError) as exc: batches(*args)
            assert re.fullmatch(re.escape(f'{name}: whole number 1 to {cap} required'),str(exc.value))
        args=[1]*3
        for later in range(pos,3): args[later]=None
        with pytest.raises(ValueError) as exc: batches(*args)
        assert re.fullmatch(re.escape(f'{name}: whole number 1 to {cap} required'),str(exc.value))
