"""Row539 Stream Processing: supplied arrival-order event-time windows.
For every (timestamp,value), update max-seen timestamp then accept iff timestamp
>=max_seen-lateness. Aggregate accepted events into floor(timestamp/width)
tumbling windows; inclusive watermark, half-open windows. Caps128events,
width1..65536,lateness0..65536,nonnegative32bit timestamp/signed32bit magnitude
value. NOT_CLAIMED: real-time consumption, durable stream, exactly-once delivery,
window completion triggers, external processing or live system changes.
"""


def window_stream(events,width,lateness):
    if type(events) not in (list,tuple):raise TypeError('events must be a list or tuple')
    if len(events)>128:raise ValueError('event cap is 128')
    if type(width) is not int or not 1<=width<=65536:raise ValueError('width must be nonbool integer 1 through 65536')
    if type(lateness) is not int or not 0<=lateness<=65536:raise ValueError('lateness must be nonbool integer 0 through 65536')
    if any(type(e) not in (list,tuple) or len(e)!=2 for e in events):raise ValueError('events must contain timestamp and value')
    if any(type(t) is not int or not 0<=t<=4294967295 or type(v) is not int or v.bit_length()>32 for t,v in events):raise ValueError('timestamps must be nonnegative 32-bit and values signed 32-bit magnitude nonbool integers')
    maximum=0;accepted=[];late=[];counts={};totals={}
    for i,(t,v) in enumerate(events):
        maximum=max(maximum,t)
        if t<maximum-lateness:late.append(i);continue
        accepted.append(i);window=t//width;counts[window]=counts.get(window,0)+1;totals[window]=totals.get(window,0)+v
    return {'accepted_indices':accepted,'late_indices':late,
            'windows':[[w*width,(w+1)*width,counts[w],totals[w]] for w in sorted(counts)],'live_processing_performed':False}
