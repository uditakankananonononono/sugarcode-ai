"""Row 736, Analogies: coverage of a supplied part-to-part mapping.

analogy_mapping takes source and target, each a list or tuple of 1 to
max_parts distinct names (strings of 1 to 12 characters), mapping, a list or
tuple of (source_name, target_name) pairs, and max_parts, a nonbool int from 1
to 8 (default 4). Every mapped source name must be in source and every
mapped target name in target. A source name may be mapped once and a target
name may be used once.
Returns pairs (the mapping as given), unmapped_source and unmapped_target
(names in their list order), percent (mapped pairs * 100 // len(source),
rounded down) and complete (every source name and every target name is used).
Checks, in this order: max_parts, source (type, size, names, distinct), target
(same four), mapping type, mapping size (at most max_parts pairs), each pair
(shape, source name listed, target name listed), repeated names.
NOT_CLAIMED: real similarity, truth of the analogy, persuasiveness, audience
fit, production readiness.
"""
SCOPE = 'PARTIAL: one-to-one coverage count of a supplied analogy mapping, no meaning is judged'
NOT_CLAIMED = ('real similarity', 'truth of the analogy', 'persuasiveness',
               'audience fit', 'production readiness')


def _names(label, seq, max_parts):
    if type(seq) not in (list, tuple):
        raise TypeError(label + ' must be a list or tuple')
    if not 1 <= len(seq) <= max_parts:
        raise ValueError(label + ' must contain 1 to max_parts names')
    for n in seq:
        if type(n) is not str or not 1 <= len(n) <= 12:
            raise ValueError('each name must be a string of 1 to 12 characters')
    if len(set(seq)) != len(seq):
        raise ValueError(label + ' names must be distinct')


def analogy_mapping(source, target, mapping, max_parts=4):
    if type(max_parts) is not int or not 1 <= max_parts <= 8:
        raise ValueError('max_parts must be a nonbool integer between 1 and 8')
    _names('source', source, max_parts)
    _names('target', target, max_parts)
    if type(mapping) not in (list, tuple):
        raise TypeError('mapping must be a list or tuple')
    if len(mapping) > max_parts:
        raise ValueError('mapping must contain at most max_parts pairs')
    pairs = []
    for p in mapping:
        if type(p) not in (list, tuple) or len(p) != 2:
            raise ValueError('each pair must be a (source_name, target_name) pair')
        s, t = p
        if type(s) is not str or s not in source:
            raise ValueError('mapped source name must be listed in source')
        if type(t) is not str or t not in target:
            raise ValueError('mapped target name must be listed in target')
        pairs.append((s, t))
    if len({s for s, _ in pairs}) != len(pairs) or len({t for _, t in pairs}) != len(pairs):
        raise ValueError('each name may be used once')
    used_s = {s for s, _ in pairs}
    used_t = {t for _, t in pairs}
    us = [n for n in source if n not in used_s]
    ut = [n for n in target if n not in used_t]
    return {'pairs': pairs, 'unmapped_source': us, 'unmapped_target': ut,
            'percent': len(pairs) * 100 // len(source), 'complete': not us and not ut}
