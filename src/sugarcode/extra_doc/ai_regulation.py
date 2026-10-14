"""Row 1955, Title: AI Regulation

count_custodies(rows): rows are (act, section, level)
triples; act and section strings of 1 to 16
characters; level a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each act its
custodies (sections where it alone holds the peak
level), the total custodies, the contested sections
(whose peak is held by more than one act, sorted
alphabetically), and the leader (the most
custodies, first supplied on ties, or None when
every section is contested).

SCOPE: PARTIAL: custody counting over supplied levels
NOT_CLAIMED: statutory interpretation, enforcement
prediction, penalty modeling, jurisdictional reach,
production readiness.
"""

SCOPE = 'PARTIAL: custody counting over supplied levels'
NOT_CLAIMED = ('statutory interpretation', 'enforcement prediction',
               'penalty modeling', 'jurisdictional reach',
               'production readiness')


def count_custodies(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (act, section, level) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        act, section, level = row
        if type(act) is not str or not 1 <= len(act) <= 16:
            raise ValueError(f'row {i}: act must be a string of 1 to 16 characters')
        if type(section) is not str or not 1 <= len(section) <= 16:
            raise ValueError(f'row {i}: section must be a string of 1 to 16 characters')
        if type(level) is not int or not 1 <= level <= 9:
            raise ValueError(f'row {i}: level must be a nonbool integer between 1 and 9')
    per_section = {}
    order = {}
    for act, section, level in rows:
        if section not in per_section:
            per_section[section] = {}
        if act not in order:
            order[act] = True
        if act not in per_section[section] or level > per_section[section][act]:
            per_section[section][act] = level
    custodies = {}
    contested = []
    count = 0
    for section in per_section:
        slot = per_section[section]
        top = max(slot.values())
        holders = []
        for act in slot:
            if slot[act] == top:
                holders.append(act)
        if len(holders) == 1:
            only = holders[0]
            if only not in custodies:
                custodies[only] = 0
            custodies[only] += 1
            count += 1
        else:
            contested.append(section)
    leader = None
    for act in order:
        if act not in custodies:
            continue
        if leader is None or custodies[act] > custodies[leader]:
            leader = act
    return {'total': len(rows),
            'custodies': custodies,
            'count': count,
            'contested': sorted(contested),
            'leader': leader}
