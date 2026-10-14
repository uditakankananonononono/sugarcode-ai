import pytest
from sugarcode.extra_doc.domain_event677 import replay
from sugarcode.extra_doc.anti_corruption678 import translate
from sugarcode.extra_doc.hexagonal679 import audit as hexagonal
from sugarcode.extra_doc.clean_architecture680 import audit as clean
from sugarcode.extra_doc.onion681 import audit as onion

@pytest.mark.parametrize('call,message',[
 (lambda:replay([('e%d'%i,'a',1,0) for i in range(101)]),'events must be an exact list with 0..100 entries'),
 (lambda:translate({'r%d'%i:'i%d'%i for i in range(21)},{}),'rules must be an exact dict with 1..20 entries'),
 (lambda:translate({'a':'x'},{'k%d'%i:'v' for i in range(51)}),'payload must be an exact dict with 0..50 entries'),
 (lambda:hexagonal(['p%d'%i for i in range(51)],[]),'ports must be an exact list with 0..50 entries'),
 (lambda:hexagonal(['p'],[('p','a')]*101),'bindings must be an exact list with 0..100 entries'),
 (lambda:clean({'l%d'%i:1 for i in range(101)},[]),'layers must be an exact dict with 1..100 entries'),
 (lambda:clean({'a':1},[('a','a')]*501),'edges must be an exact list with 0..500 entries'),
 (lambda:onion({'l%d'%i:1 for i in range(51)},[]),'layers must be an exact dict with 1..50 entries'),
 (lambda:onion({'a':1},[('a','a')]*201),'edges must be an exact list with 0..200 entries'),
])
def test_caps_plus_one(call,message):
    with pytest.raises(ValueError) as exc:call()
    assert str(exc.value)==message
