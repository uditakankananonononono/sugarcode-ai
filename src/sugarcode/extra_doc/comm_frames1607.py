"""Communications Systems.

PARTIAL: caller payload/frame overhead arithmetic only, not communications
systems, transmission simulation, throughput prediction or protocol compliance.
Frame capacity/overhead supplied by caller; no headers or real network inferred.
"""
from fractions import Fraction
SCOPE='caller frame overhead arithmetic only; no communication performance claims'


def frames(payloads,capacity,overhead):
    """Payloads exactlist/tuple1..64 exactint0..1000000;capacity exactint1..
    1000000;overhead exactint0..1000000 per frame. Each payload framed separately
    without aggregation,empty payload uses0 frames. Return(payload,frames,wire
    units),totals payload/wire/frame count,exact useful fraction None if wire0.
    No padding counted;wire=payload+frames*overhead. No rates/timing/side effects.
    """
    if type(capacity) is not int or not 1<=capacity<=1000000:raise ValueError('capacity must be exactint1..1000000')
    if type(overhead) is not int or not 0<=overhead<=1000000:raise ValueError('overhead must be exactint0..1000000')
    if type(payloads) not in (list,tuple) or not 1<=len(payloads)<=64:raise ValueError('payloads must be exactlist/tuple length1..64')
    result=[]
    for payload in payloads:
        if type(payload) is not int or not 0<=payload<=1000000:raise ValueError('payload must be exactint0..1000000')
        count=(payload+capacity-1)//capacity;wire=payload+count*overhead;result.append((payload,count,wire))
    payload_total=sum(row[0] for row in result);wire_total=sum(row[2] for row in result)
    return {'frames':tuple(result),'payload_total':payload_total,'wire_total':wire_total,
            'frame_count':sum(row[1] for row in result),'useful_fraction':Fraction(payload_total,wire_total) if wire_total else None,'scope':SCOPE}
