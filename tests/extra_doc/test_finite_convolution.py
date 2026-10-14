import itertools
import re
import pytest
from sugarcode.extra_doc.finite_convolution import convolve
class Number(int): pass
class Items(tuple): pass

def oracle(signal,kernel):
    out=[0]*(len(signal)+len(kernel)-1)
    for i,sample in enumerate(signal):
        for j,coefficient in enumerate(kernel): out[i+j]+=sample*coefficient
    return {'finite_convolution_validated':False,
            'not_claimed':('sampling_assumptions','spectral_interpretation','filter_design'),
            'samples':tuple(out),'output_length':len(out)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: convolve(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    options=[t for n in (1,2,3) for t in itertools.product((-1,0,1),repeat=n)]
    for signal,kernel in itertools.product(options,repeat=2): assert convolve(signal,kernel)==oracle(signal,kernel)

def test_caps_and_impulses():
    for signal in ((-1000,)*30,(1000,)*30,(1,)+(0,)*29,(0,)*29+(1,)):
        for kernel in ((-1000,)*8,(1000,)*8,(1,)+(0,)*7,(0,)*7+(1,)):
            assert convolve(signal,kernel)==oracle(signal,kernel)
    assert convolve((1,2,3),(4,5))['samples']==(4,13,22,15)

def test_shapes_values_and_order():
    for j,(name,cap) in enumerate((('signal',30),('kernel',8))):
        for bad in ((),(None,)*(cap+1),[0],Items((0,)),None,'é'):
            args=[(0,),(0,)];args[j]=bad
            refuse(args,f'{name}: tuple of 1 to {cap} entries required')
        for pos in (0,1,cap-1):
            for bad in (-1001,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                seq=[0]*cap;seq[pos]=bad;args=[(0,),(0,)];args[j]=tuple(seq)
                refuse(args,f'{name}[{pos}]: whole number -1000 to 1000 required')
    refuse((None,None),'signal: tuple of 1 to 30 entries required')
    refuse(((None,),None),'signal[0]: whole number -1000 to 1000 required')
