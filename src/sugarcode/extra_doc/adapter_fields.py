"""Row 661, Adapter Pattern: renaming fields of a supplied record.

adapter_fields takes mapping, a list or tuple of 0 to 8 (source, target) pairs
of strings of 1 to 12 characters, with unique sources and unique targets, and
record, a list or tuple of 0 to 10 (field, value) pairs with unique fields of
1 to 12 characters and values that are nonbool ints from -1000 to 1000.
Reported: converted ((target, value) pairs in mapping order, for each mapped
source present in the record), missing (mapped sources absent from the
record, mapping order) and unmapped (record fields not in the mapping, record
order).
Checks, in this order: mapping type, size, record type, size, then each
mapping pair (shape, source, duplicate source, target, duplicate target),
then each record pair (shape, field, duplicate field, value).
NOT_CLAIMED: nested data, type conversion, real interfaces, schemas,
production readiness.
"""
SCOPE = 'PARTIAL: field renaming over one supplied flat record, no real interfaces'
NOT_CLAIMED = ('nested data', 'type conversion', 'real interfaces', 'schemas',
               'production readiness')


def _name(v, msg):
    if type(v) is not str or not 1 <= len(v) <= 12:
        raise ValueError(msg)


def adapter_fields(mapping, record):
    if type(mapping) not in (list, tuple):
        raise TypeError('mapping must be a list or tuple')
    if len(mapping) > 8:
        raise ValueError('mapping must contain at most 8 entries')
    if type(record) not in (list, tuple):
        raise TypeError('record must be a list or tuple')
    if len(record) > 10:
        raise ValueError('record must contain at most 10 entries')
    sources, targets = [], set()
    for p in mapping:
        if type(p) not in (list, tuple) or len(p) != 2:
            raise ValueError('each mapping entry must be a (source, target) pair')
        src, dst = p
        _name(src, 'sources must be strings of 1 to 12 characters')
        if src in sources:
            raise ValueError('duplicate source')
        _name(dst, 'targets must be strings of 1 to 12 characters')
        if dst in targets:
            raise ValueError('duplicate target')
        sources.append(src)
        targets.add(dst)
    values = {}
    for p in record:
        if type(p) not in (list, tuple) or len(p) != 2:
            raise ValueError('each record entry must be a (field, value) pair')
        field, value = p
        _name(field, 'fields must be strings of 1 to 12 characters')
        if field in values:
            raise ValueError('duplicate field')
        if type(value) is not int or not -1000 <= value <= 1000:
            raise ValueError('value must be a nonbool integer between -1000 and 1000')
        values[field] = value
    converted, missing = [], []
    for src, dst in mapping:
        if src in values:
            converted.append((dst, values[src]))
        else:
            missing.append(src)
    unmapped = [f for f in values if f not in sources]
    return {'converted': converted, 'missing': missing, 'unmapped': unmapped}
