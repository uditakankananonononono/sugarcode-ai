import pytest
from sugarcode.self_improve.isolated_result_codec import decode_child_result, ResultProtocolError
from sugarcode.self_improve.registry import FeatureRegistry


@pytest.mark.parametrize('limits',[{'max_bytes':True},{'max_depth':0},{'max_int_digits':-1},{'max_depth':'bad'}])
def test_invalid_limits_typed(limits):
    with pytest.raises(ResultProtocolError,match='bad_limit'):decode_child_result(b'{"result":1}',**limits)


def test_large_legal_integer_not_arbitrarily_capped():
    assert decode_child_result(b'{"result":'+b'9'*100+b'}')==int('9'*100)


@pytest.mark.parametrize('raw',[b'{"result":NaN}',b'{"result":1,"result":2}',b'{"result":{"a":1,"a":2}}',b'{"result":1e999}',b'\xef\xbb\xbf{"result":1}',b'{"result":"\\ud800"}'])
def test_actual_dispatch_rejects_hostile_child_stdout(tmp_path,real_containment,raw):
    from sugarcode.self_improve.isolated_dispatch import dispatch
    registry=FeatureRegistry('m',tmp_path)
    # Hostile feature bypasses launcher output by writing directly then exiting.
    code='def run(items,params=None):\n import os\n os.write(1,'+repr(raw)+')\n os._exit(0)\n'
    registry.save_proposal('x',name='x',kind='text_transform',code=code,test_code='',gap_signature='x')
    registry.activate('x',approval_id='test')
    with pytest.raises(ResultProtocolError):dispatch(registry,'x',[])
