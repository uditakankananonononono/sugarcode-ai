"""Row 581 Protocol Design: exact byte layout of a caller-described fixed-width message format.

The caller supplies 1 to 20 unique fields (name, bits) with bits an int 1 to 64, in wire order, and
an alignment (int 1 to 16 bytes). Each field is placed at the next free bit; the message is padded at
the end to a whole multiple of the alignment in bytes. Reported per field: its start bit, end bit
(exclusive), and the byte index of its first and last bit; plus the used bits, the total bytes after
padding and the padding bits. Caps and the packing and end-padding rules are implementation choices,
not spec values; no real protocol layout, endianness or encoding is modelled.
NOT_CLAIMED: that the layout matches any real protocol, endianness, field semantics, versioning or
compatibility, parseability of real data, security of the format, approval-gate clearance, deployment.
"""
NOT_CLAIMED = ('layout matches any real protocol', 'endianness', 'field semantics',
               'versioning or compatibility', 'parseability of real data', 'security of the format',
               'approval-gate clearance', 'deployment')


def layout(fields, alignment):
    if type(alignment) is not int:
        raise TypeError('alignment must be nonbool int')
    if not 1 <= alignment <= 16:
        raise ValueError('alignment must be between 1 and 16')
    if type(fields) not in (list, tuple):
        raise TypeError('fields must be a list or tuple')
    if not 1 <= len(fields) <= 20:
        raise ValueError('field count must be between 1 and 20')
    rows = []
    for f in fields:
        if type(f) not in (list, tuple) or len(f) != 2:
            raise ValueError('each field must be (name, bits)')
        name, bits = f
        if type(name) is not str:
            raise TypeError('names must be str')
        if not 1 <= len(name) <= 40:
            raise ValueError('names must be 1 to 40 characters')
        if type(bits) is not int:
            raise TypeError('bits must be nonbool int')
        if not 1 <= bits <= 64:
            raise ValueError('bits must be between 1 and 64')
        rows.append((name, bits))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('field names must be unique')
    pos = 0
    out = []
    for name, bits in rows:
        out.append({'name': name, 'start_bit': pos, 'end_bit': pos + bits,
                    'first_byte': pos // 8, 'last_byte': (pos + bits - 1) // 8})
        pos += bits
    unit = 8 * alignment
    total = -(-pos // unit) * alignment
    return {'fields': out, 'used_bits': pos, 'total_bytes': total, 'padding_bits': total * 8 - pos,
            'protocol_validated': False, 'not_claimed': NOT_CLAIMED}
