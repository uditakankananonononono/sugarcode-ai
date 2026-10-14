import pytest
from sugarcode.extra_doc.search_system549 import search_documents as raw_run
def run(rows): return raw_run(rows, 'red')
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
ROWS = [('a', 'red blue'), ('b', 'green'), ('c', 'RED')]

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses_nonfirst(container):
    with pytest.raises(TypeError,match='^exact list required$'):run(container(ROWS))
    with pytest.raises(TypeError,match='^exact tuple row required$'):run([ROWS[0],container(ROWS[1])]+ROWS[2:])

@pytest.mark.parametrize('slot',[0])
def test_label_subclasses_nonfirst(slot):
    rows=list(ROWS);record=list(rows[1]);record[slot]=S(record[slot]);rows[1]=tuple(record)
    with pytest.raises(TypeError,match='^exact string label required$'):run(rows)



def test_nonadjacent_duplicate_full_message():
    with pytest.raises(ValueError,match='^duplicate document$'):run(ROWS+[ROWS[0]])


def test_nonfirst_wrong_arity_exact():
    with pytest.raises(ValueError,match='^wrong row arity$'):run([ROWS[0],ROWS[1][:-1]]+ROWS[2:])


def test_query_and_document_text_subclasses():
    with pytest.raises(TypeError,match='^exact text string required$'):
        raw_run([('a','red')],S('red'))
    with pytest.raises(TypeError,match='^exact text string required$'):
        raw_run([('a','red'),('b',S('red'))],'red')

@pytest.mark.parametrize('bad',['red!','red\n','  ','é'])
def test_nonfirst_mixed_document_charset_and_space(bad):
    message='at least one token required' if bad=='  ' else 'ASCII words and spaces required'
    with pytest.raises(ValueError,match='^'+message+'$'):
        raw_run([('a','red'),('b',bad)],'red')


def test_full_empty_matches_and_case_distinct_tokens():
    assert raw_run([('a','RED red 1'),('b','redder')],'ReD 1 1')=={
        'matches':[('a',2,['1','red'])],'query_tokens':['1','red']}
    assert raw_run([('a','blue')],'RED red')=={'matches':[],'query_tokens':['red']}
