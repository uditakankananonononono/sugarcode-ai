import itertools
import re
import pytest
from sugarcode.extra_doc.dna_symbol_xor import xor
class Text(str): pass
TABLE = {'AA':'A','AC':'C','AG':'G','AT':'T',
         'CA':'C','CC':'A','CG':'T','CT':'G',
         'GA':'G','GC':'T','GG':'A','GT':'C',
         'TA':'T','TC':'G','TG':'C','TT':'A'}
CODES = {'A':0,'C':1,'G':2,'T':3}

def oracle(left,right):
    result='';zeros=[];encoded=[]
    for i,(a,b) in enumerate(zip(left,right)):
        symbol=TABLE[a+b];result+=symbol;encoded.append(CODES[symbol])
        if a==b:zeros.append(i)
    return {'dna_symbol_xor_validated':False,
            'not_claimed':('molecular_execution','biological_computation','laboratory_validation'),
            'symbols':result,'encoded':tuple(encoded),'zero_positions':tuple(zeros)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: xor(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_truth_table_oracle():
    for n in (1,2,3):
        words=[''.join(p) for p in itertools.product('ACGT',repeat=n)]
        for a,b in itertools.product(words,repeat=2): assert xor(a,b)==oracle(a,b)

def test_caps_first_last():
    for a,b in (('A'*30,'T'*30),('T'+'A'*29,'A'*30),('A'*29+'T','A'*30),('G'*30,'G'*30)):
        assert xor(a,b)==oracle(a,b)

def test_types_lengths_and_order():
    for j,name in enumerate(('left','right')):
        for bad in ('','A'*31,Text('A'),None,1,True,b'A',('A',)):
            args=['A','A'];args[j]=bad
            refuse(args,f'{name}: text of 1 to 30 symbols required')
        for pos in (0,1,29):
            for bad in ('é','ａ','Ж','a','N',' ','\n'):
                text=list('A'*30);text[pos]=bad;args=['A'*30,'A'*30];args[j]=''.join(text)
                refuse(args,f'{name}[{pos}]: uppercase A,C,G,T required')
    refuse(('A','AA'),'left and right must have equal length')
    refuse(('AA','A'),'left and right must have equal length')
    refuse(('N',None),'left[0]: uppercase A,C,G,T required')

def test_reject_extra_ascii_symbol_first_and_later():
    for pos in (0,1,29):
        for symbol in 'x1234567890_-':
            text=list('A'*30);text[pos]=symbol
            refuse((''.join(text),'A'*30),f'left[{pos}]: uppercase A,C,G,T required')
            refuse(('A'*30,''.join(text)),f'right[{pos}]: uppercase A,C,G,T required')
