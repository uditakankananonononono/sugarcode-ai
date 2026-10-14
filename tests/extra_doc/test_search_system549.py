import itertools
import pytest
from sugarcode.extra_doc.search_system549 import search_documents as run


def test_exact_token_set_matching_tie_order_case_and_no_substring():
    rows=[('z','red red blue'),('a','BLUE red'),('b','redder green'),('c','blue')]
    for order in itertools.permutations(rows):
        assert run(list(order),'RED blue red')=={'matches':[('a',2,['blue','red']),('z',2,['blue','red']),('c',1,['blue'])],
                                                  'query_tokens':['blue','red']}
    assert run(rows,'absent')['matches']==[]


@pytest.mark.parametrize('bad',[None,[],{},True,1,b'text'])
def test_query_type(bad):
    with pytest.raises(TypeError,match='^exact text string required$'):run([('doc','a')],bad)


@pytest.mark.parametrize('bad',['','a'*257])
def test_query_cap(bad):
    with pytest.raises(ValueError,match='^text length outside declared range$'):run([('doc','a')],bad)


@pytest.mark.parametrize('bad',['é','a\n','a_b','!'])
def test_query_charset(bad):
    with pytest.raises(ValueError,match='^ASCII words and spaces required$'):run([('doc','a')],bad)


def test_space_only_query_and_text():
    for rows,query in [([('doc','a')],' '),([('doc',' ')],'a')]:
        with pytest.raises(ValueError,match='^at least one token required$'):run(rows,query)


@pytest.mark.parametrize('bad',[None,(),{},True])
def test_outer_type(bad):
    with pytest.raises(TypeError,match='^exact list required$'):run(bad,'a')


@pytest.mark.parametrize('n',[0,33])
def test_rows_cap_before_scan(n):
    with pytest.raises(ValueError,match='^row count must be 1..32$'):run([None]*n,'a')


@pytest.mark.parametrize('row',[(),(None,),(None,)*3])
def test_arity_before_slots(row):
    with pytest.raises(ValueError,match='^wrong row arity$'):run([row],'a')


@pytest.mark.parametrize('slot',range(2))
@pytest.mark.parametrize('bad',[None,True,1,1.0,b'a',[],{}])
def test_per_slot_types(slot,bad):
    row=['doc','a'];row[slot]=bad
    message='exact string label required' if slot==0 else 'exact text string required'
    with pytest.raises(TypeError,match='^'+message+'$'):run([tuple(row)],'a')


@pytest.mark.parametrize('bad',['','A','a b','a'*25])
def test_label_caps(bad):
    with pytest.raises(ValueError,match='^label must be 1..24 lowercase identifier characters$'):run([(bad,'a')],'a')


@pytest.mark.parametrize('bad',['','a'*1025])
def test_document_caps(bad):
    with pytest.raises(ValueError,match='^text length outside declared range$'):run([('doc',bad)],'a')


def test_duplicate_identity_independent_text_and_endpoints():
    with pytest.raises(ValueError,match='^duplicate document$'):run([('a','red'),('a','blue')],'red')
    assert run([('a','a'*1024)],'a'*256)['matches']==[]
    assert run([('a'*24,'a')],'a')['matches']==[('a'*24,1,['a'])]
    assert len(run([('doc_'+str(i),'a') for i in range(32)],'a')['matches'])==32


def test_unmatched_document_tokens_do_not_inflate_score_or_match_list():
    assert run([('a','red extra more'),('b','red blue')],'red blue')=={
        'matches':[('b',2,['blue','red']),('a',1,['red'])], 'query_tokens':['blue','red']}
