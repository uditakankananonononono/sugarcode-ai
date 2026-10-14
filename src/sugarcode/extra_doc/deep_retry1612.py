"""Deep Space Communications.

PARTIAL: caller independent retry probability arithmetic only, not deep-space
communications, mission reliability, measured channels or operational decisions.
Success probability/delay/attempt cap are caller inputs; independence is a toy
assumption, not a validated space-channel model.
"""
from fractions import Fraction
SCOPE='caller independent retry arithmetic only; no space-channel or mission reliability claims'


def retries(success_num,success_den,attempts,roundtrip_ticks):
    """All exactints;0<=success_num<=success_den<=1000000,success_den>=1;
    attempts1..64;roundtrip_ticks0..1000000. At most attempts independent trials,
    stop on success. Return first-success probabilities by1-based attempt,
    exhausted probability,expected attempts and expected ticks. An attempted
    trial costs roundtrip_ticks even on last failure;no partial-time outcomes.
    No channel estimates,errorcorrection,mission advice or real telemetry.
    """
    if type(success_num) is not int or type(success_den) is not int or not 0<=success_num<=success_den<=1000000 or success_den==0:
        raise ValueError('success components must be exactint0<=num<=den<=1000000 and den>0')
    if type(attempts) is not int or not 1<=attempts<=64:raise ValueError('attempts must be exactint1..64')
    if type(roundtrip_ticks) is not int or not 0<=roundtrip_ticks<=1000000:raise ValueError('roundtrip_ticks must be exactint0..1000000')
    p=Fraction(success_num,success_den);failure=1-p;survival=Fraction(1);first=[];expected=Fraction(0)
    for i in range(1,attempts+1):
        expected+=survival;first.append((i,survival*p));survival*=failure
    return {'first_success':tuple(first),'exhausted':survival,'expected_attempts':expected,
            'expected_ticks':expected*roundtrip_ticks,'scope':SCOPE}
