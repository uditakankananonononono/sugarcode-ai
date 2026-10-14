"""Row 580 Networking Stack: exact encapsulation and fragmentation arithmetic for a caller-described stack.

The caller supplies a payload size in bytes (int 0 to 10**7), 1 to 8 layer header sizes in bytes (ints
0 to 1000) and a per-fragment limit in bytes (int 1 to 65535). The headers of all layers together are
added to every fragment, so each fragment carries at most limit minus the header total bytes of payload.
Reported: header total,
payload bytes per fragment (limit minus header total), fragment count (ceil of payload over that, at
least 1), total bytes on the wire (payload plus one header set per fragment) and efficiency (payload
over wire bytes, Fraction, None when the wire total is 0). A header total at or above the limit is
refused. Caps and the every-fragment-repeats-all-headers model are implementation choices, not spec
values; no real protocol's fragmentation rules are used.
NOT_CLAIMED: that any header size matches a real protocol, that real stacks fragment this way,
throughput, latency, loss, checksums, that the numbers describe a deployed network, approval-gate
clearance, deployment.
"""
from fractions import Fraction

NOT_CLAIMED = ('any header size matches a real protocol', 'real stacks fragment this way',
               'throughput, latency, loss or checksums', 'the numbers describe a deployed network',
               'approval-gate clearance', 'deployment')


def encapsulate(payload, headers, limit):
    for label, v, lo, hi in (('payload', payload, 0, 10 ** 7), ('limit', limit, 1, 65535)):
        if type(v) is not int:
            raise TypeError(label + ' must be nonbool int')
        if not lo <= v <= hi:
            raise ValueError('%s must be between %d and %d' % (label, lo, hi))
    if type(headers) not in (list, tuple):
        raise TypeError('headers must be a list or tuple')
    if not 1 <= len(headers) <= 8:
        raise ValueError('layer count must be between 1 and 8')
    for h in headers:
        if type(h) is not int:
            raise TypeError('header sizes must be nonbool int')
        if not 0 <= h <= 1000:
            raise ValueError('header sizes must be between 0 and 1000')
    total = sum(headers)
    if total >= limit:
        raise ValueError('header total must be below the limit')
    per = limit - total
    frags = max(1, -(-payload // per))
    wire = payload + frags * total
    return {'header_total': total, 'payload_per_fragment': per, 'fragments': frags, 'wire_bytes': wire,
            'efficiency': Fraction(payload, wire) if wire else None,
            'stack_validated': False, 'not_claimed': NOT_CLAIMED}
