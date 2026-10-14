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


import inspect
import random
a=load('wolf934')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_scope_hand_mixed(self):
        coeff=[[[[0],[1]],([0],[1]),[[0],[1]]] for _ in range(3)]
        out=a.encircle([[3],(1,),[-1]],coeff)
        self.assertEqual(out['leaders'],(1,2,0));self.assertEqual(out['points'],((1.,),(1.,),(1.,)));self.assertEqual(out['scores'],(1.,1.,1.));self.assertEqual(out['scope'],'three-leader synchronous encircling sphere generation; no optimum guarantee')
        self.assertEqual(out,a.encircle(((3,),(1,),(-1,)),tuple(tuple((tuple(pair[0]),tuple(pair[1])) for pair in row) for row in coeff)))
    def test_caps_and_types(self):
        self.assertEqual(inspect.signature(a.encircle).parameters['bound'].default,10.)
        coeff=[(([2]*4,[2]*4),([-2]*4,[0]*4),([0]*4,[1]*4))]*16
        out=a.encircle([[100]*4]*16,coeff,bound=100)
        for row in out['points']:
            for x in row:self.assertIs(type(x),float)
        self.assertEqual(out['leaders'],(0,1,2))

def seeded(seed):
    def test(self):
        rng=random.Random(seed);n=rng.randrange(3,9);dim=rng.randrange(1,5);points=[[rng.uniform(-5,5) for _ in range(dim)] for _ in range(n)];coeff=[[( [rng.uniform(-2,2) for _ in range(dim)],[rng.uniform(0,2) for _ in range(dim)] ) for _ in range(3)] for _ in range(n)]
        out=a.encircle(points,coeff,bound=5);scores=[sum(x*x for x in row) for row in points];leaders=tuple(sorted(range(n),key=lambda i:(scores[i],i))[:3]);expected=[]
        for i,row in enumerate(points):
            new=[]
            for axis in range(dim):
                values=[]
                for k,index in enumerate(leaders):
                    A,C=coeff[i][k];D=abs(C[axis]*points[index][axis]-row[axis]);values.append(points[index][axis]-A[axis]*D)
                new.append(max(-5,min(5,sum(values)/3)))
            expected.append(tuple(new))
        self.assertEqual(out['leaders'],leaders)
        for actual,want in zip(out['points'],expected):
            for x,y in zip(actual,want):self.assertAlmostEqual(x,y,places=12)
        for x,row in zip(out['scores'],expected):self.assertAlmostEqual(x,sum(z*z for z in row),places=10)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(args,kwargs,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:a.encircle(*args,**kwargs)
        self.assertEqual(str(caught.exception),message)
    return test
p=[[0]]*3;c=[([([0],[1])]*3)]*3;cases=[]
for points in ([],[[0]]*2,[[0]]*17,L(p),T(p)):cases.append(((points,c),{},'points must contain3..16 vectors'))
for points in ([[]]*3,[[0]*5]*3,[L([0])]*3,[T([0])]*3,[[0,0],[0],[0,0]]):cases.append(((points,c),{},'vectors must have1..4 equal dimensions'))
for coef in ([],c+[c[0]],L(c),T(c)):cases.append(((p,coef),{},'one three-leader coefficient matrix per agent required'))
for row in ([],[([0],[1])]*2,L(c[0]),T(c[0])):cases.append(((p,[row]*3),{},'three leader coefficient pairs per agent required'))
for pair in (([0],),L(([0],[1])),T(([0],[1]))):cases.append(((p,[[pair]*3]*3),{},'each coefficient pair must contain A and C vectors'))
for value in (True,I(0),S('1'),float('nan'),10**10000,10.5,-10.5):cases.append((([[value]]*3,c),{},'finite built-in wolf real outside range'))
for value in (-.1,100.5,True,10**10000):cases.append(((p,c),{'bound':value},'finite built-in wolf real outside range'))
cases.append(((p,c),{'bound':0},'bound must be positive'))
for A,C in (([2.5],[1]),([-2.5],[1]),([0],[-.1]),([0],[2.5])):cases.append(((p,[[(A,C)]*3]*3),{},'finite built-in wolf real outside range'))
for i,(args,kw,msg) in enumerate(cases):setattr(Tests,'test_refusal_%02d'%i,refusal(args,kw,msg))

def explicit_first_dimension_and_bound_precedence(self):
    for points in ([[]]*3,[[0]*5]*3):
        coef=[[(points[0],points[0])]*3]*3
        with self.assertRaises(ValueError) as caught:a.encircle(points,coef)
        self.assertEqual(str(caught.exception),'vectors must have1..4 equal dimensions')
    with self.assertRaises(ValueError) as caught:a.encircle([],[],bound=-.5)
    self.assertEqual(str(caught.exception),'finite built-in wolf real outside range')
    a.encircle([[0]]*3,[[([0],[0])]*3]*3,bound=.5)
Tests.test_explicit_first_dimension_and_bound_precedence=explicit_first_dimension_and_bound_precedence


def audit_wolf_vector_type_at_every_position(self):
    message='vectors must have1..4 equal dimensions'
    coefficients=[[([0,0],[1,1])]*3 for _ in range(3)]
    for position in (0,1,2):
        for bad in (5,'ab',(),[],[0],L([0,0]),T([0,0])):
            points=[[1,2],[3,4],[5,6]];points[position]=bad
            with self.assertRaises(ValueError) as caught:a.encircle(points,coefficients)
            self.assertEqual(str(caught.exception),message)
    for agent in (0,1,2):
        for leader in (0,1,2):
            for side in (0,1):
                for bad in (5,'ab',(),[],[0],L([0,0]),T([0,0])):
                    coefficients=[[[[0,0],[1,1]] for _ in range(3)] for _ in range(3)]
                    coefficients[agent][leader][side]=bad
                    with self.assertRaises(ValueError) as caught:a.encircle([[1,2],[3,4],[5,6]],coefficients)
                    self.assertEqual(str(caught.exception),message)
Tests.test_audit_wolf_vector_type_at_every_position=audit_wolf_vector_type_at_every_position
