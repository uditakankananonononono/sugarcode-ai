import importlib
import importlib.util
import itertools
import math
import os
import sys
import unittest


def load(name):
    full = 'sugarcode.extra_doc.' + name
    if os.environ.get('MUTANT_MODULE') == full:
        spec = importlib.util.spec_from_file_location(full, os.environ['MUTANT_PATH'])
        module = importlib.util.module_from_spec(spec)
        sys.modules[full] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(full)


from fractions import Fraction as F
import random
import string
import ast
a=load('heart_failure1161');b=load('cancer_coord1162')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_mix_scope_and_tuples(self):
        for rows in ([ [2,72.1,1000,900],(1,70,900,1000) ],[ (2,72.1,1000,900),[1,70,900,1000] ]):
            out=a.summarize(rows,70,.1,100);self.assertEqual(out['net_total'],0);self.assertEqual(out['mean_weight'],F(1421,20));self.assertEqual(out['daily'][0]['day'],1);self.assertFalse(out['daily'][0]['weight_flag']);self.assertTrue(out['daily'][1]['net_flag']);self.assertEqual(out['daily'][1]['weight_delta'],F(21,10));self.assertEqual(out['scope'],'caller-threshold weight/fluid ledger only; no diagnosis treatment or triage')
        for rows in ([['A','É9!',()],('B','Ω?',['A'])],[('B','Ω?',('A',)),['A','É9!',[]]]):
            out=b.readiness(rows,('A',));self.assertEqual(out,{'ready':('B',),'blocked':(),'owners':(('Ω?',('B',)),),'completed':('A',),'scope':'caller-declared care-task dependency readiness; no clinical care or therapy selection'})
    def test_inclusive_flags_and_caps(self):
        out=a.summarize(((0,1,1,0),),1,0,1);self.assertTrue(out['daily'][0]['weight_flag']);self.assertTrue(out['daily'][0]['net_flag'])
        a.summarize([(i,1000,100000,0) for i in range(90)],1000,1000,100000)
        a.summarize([(100000,0,0,0)],0,0,0)
        b.readiness([('a'*40,'o'*40,[])],[])
        rows=[(str(i),'o',[]) for i in range(32)];b.readiness(rows,[str(i) for i in range(32)])
    def test_validation_precedence(self):
        with self.assertRaises(ValueError) as caught:a.summarize([],True,0,0)
        self.assertEqual(str(caught.exception),'finite built-in nonnegative ledger real outside range')
        with self.assertRaises(ValueError) as caught:b.readiness([('a','o',['missing'])],S('bad'))
        self.assertEqual(str(caught.exception),'dependencies must refer to known tasks')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);days=rng.sample(range(100),rng.randrange(1,30));rows=[(day,rng.randrange(10000)/10,rng.randrange(10000)/10,rng.randrange(10000)/10) for day in days];ref=rng.randrange(1000)/10;wt=rng.randrange(100)/10;nt=rng.randrange(1000)/10;out=a.summarize(rows,ref,wt,nt);cumulative=F(0);expected=[]
        for day,w,i,o in sorted(rows,key=lambda x:x[0]):
            w,i,o,rr,ww,nn=map(lambda x:F(str(x)),(w,i,o,ref,wt,nt));net=i-o;cumulative+=net
            expected.append({'day':day,'weight':w,'weight_delta':w-rr,'net_fluid':net,'cumulative_net':cumulative,'weight_flag':w-rr>=ww,'net_flag':net>=nn})
        self.assertEqual(out['daily'],tuple(expected));self.assertEqual(out['net_total'],cumulative);self.assertEqual(out['mean_weight'],sum(F(str(row[1])) for row in rows)/len(rows))
        alphabet=['É','Ω','中','９','A','?','!','_'];names=[rng.choice(alphabet)+str(i) for i in range(rng.randrange(1,15))];tasks=[];lookup={}
        for i,name in enumerate(names):
            deps=rng.sample(names[:i],rng.randrange(i+1));owner=rng.choice(alphabet)+'owner';tasks.append((name,owner,deps));lookup[name]=(owner,deps)
        done=set(rng.sample(names,rng.randrange(len(names)+1)));out=b.readiness(tasks,list(done));ready=tuple(sorted(name for name in names if name not in done and set(lookup[name][1])<=done));blocked=tuple((name,tuple(sorted(set(lookup[name][1])-done))) for name in sorted(names) if name not in done and name not in ready);owners={}
        for name in ready:owners.setdefault(lookup[name][0],[]).append(name)
        self.assertEqual(out['ready'],ready);self.assertEqual(out['blocked'],blocked);self.assertEqual(out['completed'],tuple(sorted(done)));self.assertEqual(out['owners'],tuple((owner,tuple(owners[owner])) for owner in sorted(owners)))
        self.assertEqual(out,b.readiness([list(row) if i%2 else row for i,row in enumerate(tasks[::-1])],tuple(done)))
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def charset(char):
    def test(self):
        for rows,done in ([[(char,'o',[])],[]],[ [('a',char,[])],[]],[ [('a','o',[]),('child_long','o',[char])],[] ],[ [(char,'o',[])],[char] ]):
            if char.isprintable():
                if rows[0][0]=='a' and len(rows)==2:rows=[(char,'o',[]),('child_long','o',[char])]
                b.readiness(rows,done)
            else:
                with self.assertRaises(ValueError) as caught:b.readiness(rows,done)
                self.assertEqual(str(caught.exception),'text must be exactstr printable Unicode length1..40')
    return test
for i,char in enumerate(string.printable+'ÉΩ中９?!'):setattr(Tests,'test_charset_%03d'%i,charset(char))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:fn(*args)
        self.assertEqual(str(caught.exception),message)
    return test
cases=[]
for rows in ([],[(0,0,0,0)]*91,L([(0,0,0,0)]),T([(0,0,0,0)])):cases.append((a.summarize,(rows,0,0,0),'rows must contain1..90 ledger records'))
for row in ((0,0,0),L((0,0,0,0)),T((0,0,0,0))):cases.append((a.summarize,([row],0,0,0),'ledger row must be exactlist/tuple four values'))
for day in (True,I(0),-1,100001,1.):cases.append((a.summarize,([(day,0,0,0)],0,0,0),'day must be built-in int0..100000'))
cases.append((a.summarize,([(0,0,0,0)]*2,0,0,0),'days must be unique'))
for slot in range(1,4):
 for value in (True,I(0),S('1'),float('nan'),10**10000,-.1):
  row=[0,0,0,0];row[slot]=value;cases.append((a.summarize,([row],0,0,0),'finite built-in nonnegative ledger real outside range'))
for rows in ([],[('a','o',[])]*33,L([('a','o',[])]),T([('a','o',[])])):cases.append((b.readiness,(rows,[]),'rows must contain1..32 task triples'))
for row in (('a','o'),L(('a','o',[])),T(('a','o',[]))):cases.append((b.readiness,([row],[]),'task row must be exactlist/tuple triple'))
for slot in range(2):
 for value in ('','a'*41,S('a'),'\n'):
  row=['a','o',[]];row[slot]=value;cases.append((b.readiness,([row],[]),'text must be exactstr printable Unicode length1..40'))
for deps in (L([]),T([]),['x']*32):cases.append((b.readiness,([('a','o',deps)],[]),'dependencies must be exactlist/tuple atmost31 tasks'))
for deps in (['a'],['b','b']):cases.append((b.readiness,([('a','o',deps),('b','o',[])],[]),'dependencies must be unique and nonself'))
cases.extend([(b.readiness,([('a','o',[])]*2,[]),'task labels must be unique'),(b.readiness,([('a','o',['b'])],[]),'dependencies must refer to known tasks'),(b.readiness,([('a','o',['b']),('b','o',['a'])],[]),'task dependencies must be acyclic')])
for done in (L([]),T([]),['a']*33):cases.append((b.readiness,([('a','o',[])],done),'completed must be exactlist/tuple atmost32 tasks'))
for done in (['b'],['a','a']):cases.append((b.readiness,([('a','o',[])],done),'completed tasks must be unique and known'))
for i,(fn,args,msg) in enumerate(cases):setattr(Tests,'test_refusal_%03d'%i,refusal(fn,args,msg))

def scalar_caps_and_max_dependencies(self):
    for row,ref,wt,nt in [((0,1000.5,0,0),0,0,0),((0,0,100000.5,0),0,0,0),((0,0,0,100000.5),0,0,0),((0,0,0,0),1000.5,0,0),((0,0,0,0),0,1000.5,0),((0,0,0,0),0,0,100000.5)]:
        with self.assertRaises(ValueError) as caught:a.summarize([row],ref,wt,nt)
        self.assertEqual(str(caught.exception),'finite built-in nonnegative ledger real outside range')
    a.summarize([(0,1000,100000,100000)],1000,1000,100000)
    names=[str(i) for i in range(32)];rows=[(name,'o',[]) for name in names[:-1]]+[(names[-1],'o',names[:-1])]
    out=b.readiness(rows,names[:-1]);self.assertEqual(out['ready'],(names[-1],))
    for rows,done in ([('a','o',[S('b')]),('b','o',[])],[]),([('a','o',[])],[S('a')]):
        with self.assertRaises(ValueError) as caught:b.readiness(rows,done)
        self.assertEqual(str(caught.exception),'text must be exactstr printable Unicode length1..40')
Tests.test_scalar_caps_and_max_dependencies=scalar_caps_and_max_dependencies

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Heart Failure Management.\n\nPARTIAL: caller-threshold weight and fluid ledger arithmetic, not heart-failure\nmanagement, diagnosis, risk assessment, treatment or emergency triage. No medical\nthresholds inferred; thresholds/observations must be supplied by the caller.\n')
    self.assertEqual(b.__doc__,'Cancer Care Coordination.\n\nPARTIAL: caller-declared task dependency/owner readiness ledger, not cancer care,\nclinical sequencing, diagnosis, therapy selection or patient-safety assurance.\n')
Tests.test_exact_disclaimers=exact_disclaimers
