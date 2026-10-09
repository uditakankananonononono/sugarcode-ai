import pytest
from sugarcode.dataset_length_histogram import length_histogram

def test_lengths_are_codepoints_sorted_detached():
    items=['','a','é','🙂','ab'];got=length_histogram(items);items.append('abc')
    assert got.total==5 and got.counts==((0,1),(1,3),(2,1))
    with pytest.raises((AttributeError,TypeError)):got.total=9

def test_empty_and_caps():
    assert length_histogram([]).counts==()
    assert length_histogram(['ab'],max_entries=1,max_codepoints=2).total==1
    with pytest.raises(ValueError):length_histogram(['ab'],max_codepoints=1)
    with pytest.raises(ValueError):length_histogram(['a','b'],max_entries=1)

@pytest.mark.parametrize('value',[None,(),[1],[None]])
def test_strict_input(value):
    with pytest.raises((TypeError,ValueError)):length_histogram(value)

@pytest.mark.parametrize('limit',[True,0,-1,1.0])
def test_strict_limits(limit):
    with pytest.raises((TypeError,ValueError)):length_histogram([],max_entries=limit)
    with pytest.raises((TypeError,ValueError)):length_histogram([],max_codepoints=limit)

def test_subclasses_refused():
    class L(list):pass
    class S(str):pass
    with pytest.raises(TypeError):length_histogram(L())
    with pytest.raises(TypeError):length_histogram([S('x')])
