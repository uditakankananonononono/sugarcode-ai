"""Doc row678 Anti-Corruption Layer: PARTIAL exact field-mapping fixture.

rules exact dict1..20 external IDs to distinct internal IDs, labels nonblank
exact str<=80. payload exact dict0..50 labels to exact str<=120 including empty.
Output mapped known fields, unknown fields, and missing external fields, sorted
by key. No automatic semantics, runtime adapters, trust or security validation.
"""


def translate(rules,payload):
    if type(rules) is not dict or not 1<=len(rules)<=20:
        raise ValueError('rules must be an exact dict with 1..20 entries')
    if any(type(x) is not str or not 1<=len(x)<=80 or not x.strip() for pair in rules.items() for x in pair):
        raise ValueError('rule IDs must be nonblank exact strings of 1..80 characters')
    if len(set(rules.values()))!=len(rules):
        raise ValueError('internal IDs must be distinct')
    if type(payload) is not dict or len(payload)>50:
        raise ValueError('payload must be an exact dict with 0..50 entries')
    for key,value in payload.items():
        if type(key) is not str or not 1<=len(key)<=80 or not key.strip():
            raise ValueError('payload IDs must be nonblank exact strings of 1..80 characters')
        if type(value) is not str or len(value)>120:
            raise ValueError('payload values must be exact strings with 0..120 characters')
    return {'mapped':{rules[k]:payload[k] for k in sorted(payload) if k in rules},
            'unknown':{k:payload[k] for k in sorted(payload) if k not in rules},
            'missing':[k for k in sorted(rules) if k not in payload],
            'claim':'PARTIAL','semantics_validated':False}
