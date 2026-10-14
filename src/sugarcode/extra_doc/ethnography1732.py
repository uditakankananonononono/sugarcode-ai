"""Doc row1732 Ethnography: PARTIAL supplied field-note code tally.

Notes exact list0..100 tuples(id,setting,codes), unique IDs. Labels nonblank
exact str<=80; codes exact list0..20 unique labels. Report code note counts,
setting note counts, and codes occurring in only one setting, all sorted.
No ethnographic interpretation, private people inference or field observation.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def tally(notes):
    if type(notes) is not list or len(notes)>100:
        raise ValueError('notes must be an exact list with 0..100 entries')
    ids=set()
    for row in notes:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('note must be an id setting codes tuple')
        name,setting,codes=row
        if not _label(name) or name in ids:raise ValueError('note IDs must be unique valid labels')
        ids.add(name)
        if not _label(setting):raise ValueError('setting must be a valid label')
        if type(codes) is not list or len(codes)>20 or any(not _label(x) for x in codes) or len(set(codes))!=len(codes):
            raise ValueError('codes must be an exact list of 0..20 unique valid labels')
    counts={};settings={};code_settings={}
    for name,setting,codes in notes:
        settings[setting]=settings.get(setting,0)+1
        for c in codes:counts[c]=counts.get(c,0)+1;code_settings.setdefault(c,set()).add(setting)
    return {'code_counts':sorted(counts.items()),'setting_counts':sorted(settings.items()),
            'single_setting_codes':[(c,next(iter(s))) for c,s in sorted(code_settings.items()) if len(s)==1],
            'claim':'PARTIAL','interpretation_validated':False}
