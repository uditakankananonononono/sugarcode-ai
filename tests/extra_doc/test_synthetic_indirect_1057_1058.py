import copy,random,string,math
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import gaussian_synthetic_likelihood as s
from sugarcode.extra_doc import auxiliary_indirect_inference as i
class L(list):pass
class D(dict):pass
class I(int):pass
class S(str):pass

def sd():return {'observed':1,'candidates':[['a',[-1,0,2]],['b',[0,1,3]]]}
def id():return {'observed':[-1,1,2],'candidates':[['a',[-1,0,2]],['b',[0,1,3]]],'weights':[2,3]}
def pair(v):return [v.numerator,v.denominator]
def moments(values):
    size=len(values);mean=F(sum(values),size);variance=F(size*sum(v*v for v in values)-sum(values)**2,size*(size-1));return mean,variance

def so(x):
    fitted={}
    for label,values in x['candidates']:
        mean,var=moments(values);d=(x['observed']-mean)**2/var;fitted[label]={'mean':pair(mean),'variance':pair(var),'discrepancy':pair(d),'score':math.log(float(var))/2+float(d)/2}
    return {'fitted':fitted,'best':min(fitted,key=lambda k:fitted[k]['score']),'claims':[False]*4}
def io(x):
    om,ov=moments(x['observed']);fitted={};distances={}
    for label,values in x['candidates']:
        mean,var=moments(values);d=x['weights'][0]*(mean-om)**2+x['weights'][1]*(var-ov)**2;distances[label]=d;fitted[label]={'mean':pair(mean),'variance':pair(var),'distance':pair(d)}
    return {'observed':{'mean':pair(om),'variance':pair(ov)},'fitted':fitted,'best':min(distances,key=distances.get),'claims':[False]*4}
def match_s(x):
    actual=s.compare(x);expected=so(x);assert actual['best']==expected['best'];assert actual['claims']==expected['claims']
    for label in expected['fitted']:
        for key,val in expected['fitted'][label].items():
            if key=='score':assert actual['fitted'][label][key]==pytest.approx(val,abs=1e-13)
            else:assert actual['fitted'][label][key]==val

def test_hand():
    x={'observed':0,'candidates':[['a',[-1,1]],['b',[-2,2]]]};match_s(x);assert s.compare(x)['best']=='a';assert s.compare(x)['fitted']['a']['variance']==[2,1];assert s.compare(x)['fitted']['a']['score']==pytest.approx(math.log(2)/2)
    y={'observed':[-1,1],'candidates':[['a',[-1,1]],['b',[-2,2]]],'weights':[2,3]};assert i.compare(y)==io(y);assert i.compare(y)['fitted']['b']['distance']==[108,1]

def test_random_oracles():
    rng=random.Random(1058)
    for n in range(2,7):
        for _ in range(50):
            candidates=[]
            for label in 'abcdef'[:n]:
                values=[rng.randint(-9,9) for _ in range(rng.randint(2,12))]
                if len(set(values))==1:values[-1]=9 if values[0]!=9 else -9
                candidates.append([label,values])
            match_s({'observed':rng.randint(-9,9),'candidates':candidates})
            x={'observed':[rng.randint(-9,9) for _ in range(rng.randint(2,12))],'candidates':candidates,'weights':[rng.randint(1,9),rng.randint(1,9)]};assert i.compare(x)==io(x)

def test_ties_caps_and_freshness():
    for size in [2,6]:
        for length in [2,12]:
            candidates=[[label,[-9]+[9]*(length-1)] for label in 'abcdef'[:size]]
            for observed in [-9,9]:match_s({'observed':observed,'candidates':candidates})
            assert s.compare({'observed':0,'candidates':candidates})['best']=='a'
            for weight in [1,9]:
                x={'observed':[0]*length,'candidates':candidates,'weights':[weight,weight]};assert i.compare(x)==io(x);assert i.compare(x)['best']=='a'
    x=id();x['candidates']=[['z',[1,1]],['a',[1,1]]];assert i.compare(x)==io(x);assert i.compare(x)['best']=='z'
    x=sd();x['candidates']=[['z',[1,2]],['a',[1,2]]];assert s.compare(x)['best']=='z'
    for fn,make in [(s.compare,sd),(i.compare,id)]:
        x=make();saved=copy.deepcopy(x);out=fn(x);out['claims'][0]=True;out['fitted'].clear();assert fn(x)['claims']==[False]*4;assert x==saved
        x=make();x['candidates'][-1][0]='abcdefgh';assert fn(x)['best'] in ['a','abcdefgh']

def expect(fn,x,message):
    with pytest.raises(ValueError) as err:fn(x)
    assert str(err.value)==message

@pytest.mark.parametrize('fn,make',[(s.compare,sd),(i.compare,id)])
def test_outer_and_containers(fn,make):
    message='exact dict with observed and candidates required' if fn==s.compare else 'exact dict with observed, candidates, weights required'
    for val in [None,[],D(make()),{},dict(make(),extra=1)]:expect(fn,val,message)
    for cls in [L,tuple]:
        x=make();x['candidates']=cls(x['candidates']);expect(fn,x,'candidates must be an exact list of 2..6 records')
    for j in range(2):
        for cls in [L,tuple]:
            x=make();x['candidates'][j]=cls(x['candidates'][j]);expect(fn,x,'candidate must be an exact pair list')
            x=make();x['candidates'][j][1]=cls(x['candidates'][j][1]);expect(fn,x,'samples must be an exact list of 2..12 values')
    if fn==i.compare:
        for field,msg in [('observed','samples must be an exact list of 2..12 values'),('weights','weights must be an exact pair list')]:
            for cls in [L,tuple]:
                x=make();x[field]=cls(x[field]);expect(fn,x,msg)

def test_numeric_every_slot():
    bad=[True,I(1),1.0,-10,10,None,'1']
    for val in bad:
        x=sd();x['observed']=val;expect(s.compare,x,'observed must be an exact integer -9..9')
    for fn,make in [(s.compare,sd),(i.compare,id)]:
        for j in range(2):
            for k in range(3):
                for val in bad:
                    x=make();x['candidates'][j][1][k]=val;expect(fn,x,'samples must contain exact integers -9..9')
    for j in range(3):
        for val in bad:
            x=id();x['observed'][j]=val;expect(i.compare,x,'samples must contain exact integers -9..9')
    for j in range(2):
        for val in [True,I(1),1.0,0,10,None,'1']:
            x=id();x['weights'][j]=val;expect(i.compare,x,'weights must contain exact integers 1..9')

def test_labels_all_slots():
    invalid=[S('a'),True,None,'','abcdefghi']+[c for c in string.printable if c not in string.ascii_lowercase]+['é','Ω','中','а','𝚊']
    for val in invalid:
        for fn,make in [(s.compare,sd),(i.compare,id)]:
            for j in range(2):
                x=make();x['candidates'][j][0]=val;expect(fn,x,'exact lowercase ASCII label required')
    for c in invalid[5:]:
        for val in [c+'a','a'+c+'b','a'+c]:
            for fn,make in [(s.compare,sd),(i.compare,id)]:
                x=make();x['candidates'][-1][0]=val;expect(fn,x,'exact lowercase ASCII label required')

def test_shapes_all_messages():
    for fn,make in [(s.compare,sd),(i.compare,id)]:
        for size in [0,1,7]:
            x=make();x['candidates']=[[k,[0,1]] for k in 'abcdefg'[:size]];expect(fn,x,'candidates must be an exact list of 2..6 records')
        for j in range(2):
            for size in [0,1,13]:
                x=make();x['candidates'][j][1]=[0,1]+[0]*max(0,size-2) if size>=2 else [0]*size;expect(fn,x,'samples must be an exact list of 2..12 values')
        x=make();x['candidates'][1][0]='a';expect(fn,x,'candidate labels must be unique')
        for value in [[],['a'],['a',[0,1],2]]:
            x=make();x['candidates'][1]=value;expect(fn,x,'candidate must be an exact pair list')
    for size in [0,1,13]:
        x=id();x['observed']=[0]*size;expect(i.compare,x,'samples must be an exact list of 2..12 values')
    for size in [0,1,3]:
        x=id();x['weights']=[1]*size;expect(i.compare,x,'weights must be an exact pair list')
    for j in range(2):
        x=sd();x['candidates'][j][1]=[1,1];expect(s.compare,x,'sample variance must be positive')

def test_contract():
    assert s.ALPHABET==i.ALPHABET=='abcdefghijklmnopqrstuvwxyz'
    assert s.SCOPE=='PARTIAL: scalar Gaussian synthetic likelihood from supplied simulations only'
    assert i.SCOPE=='PARTIAL: finite-candidate auxiliary mean/variance matching only'
    assert s.NOT_CLAIMED==('simulator execution','multivariate composite likelihood','statistical calibration','production readiness')
    assert i.NOT_CLAIMED==('simulator execution','parameter optimization','statistical consistency guarantees','production readiness')
