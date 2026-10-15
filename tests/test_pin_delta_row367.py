import itertools
import pytest
from sugarcode.extra_doc import canonical367 as m


def fail(n,p,msg):
    with pytest.raises(ValueError) as e:m.map_journeys(n,p)
    assert str(e.value)==msg


def test_prefix_transient_every_position():
    # an absorbing ID at ANY non-final position is refused, not only the first
    for n in (1,2,3):
        for length in range(3,7):
            for pos in range(1,length-1):
                for ab in range(n,n+2):
                    path=[0]*length;path[-1]=n+1;path[pos]=ab
                    fail(n,[tuple(path)],'journey prefix must be transient')
                    fail(n,[(0,n),tuple(path)],'journey prefix must be transient')


def test_prefix_before_end_and_coverage():
    # prefix error in a later path beats the coverage error; prefix beats absorbing-end error
    fail(3,[(0,3),(1,3,2,4)],'journey prefix must be transient')
    fail(2,[(0,2,1,0)],'journey prefix must be transient')
    # valid when absorbing only at the end
    assert m.map_journeys(2,[(0,1,2),(1,0,3)])['journey_validated'] is False
