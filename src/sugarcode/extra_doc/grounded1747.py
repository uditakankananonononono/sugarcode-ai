"""Doc row1747 Grounded Theory: PARTIAL supplied successive code-set ledger.

Rounds exact list2..20 (id,codes) tuples, unique exact nonblank str IDs1..80,
codes exact list0..100 unique same labels. Report new codes relative to all
previous rounds and first round each code appeared. Empty new-code round is
reported only as supplied evidence, not theoretical saturation or grounded theory.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def track_codes(rounds):
    if type(rounds) is not list or not 2<=len(rounds)<=20:raise ValueError('rounds must be an exact list with 2..20 entries')
    ids=set()
    for row in rounds:
        if type(row) is not tuple or len(row)!=2:raise ValueError('round must be an id codes tuple')
        name,codes=row
        if not _label(name) or name in ids:raise ValueError('round IDs must be unique valid labels')
        ids.add(name)
        if type(codes) is not list or len(codes)>100 or any(not _label(x) for x in codes) or len(set(codes))!=len(codes):raise ValueError('codes must be an exact list of 0..100 unique valid labels')
    seen=set();new=[];first={}
    for n,codes in rounds:
        fresh=sorted(set(codes)-seen);new.append((n,fresh))
        for c in fresh:first[c]=n
        seen.update(codes)
    return {'new_codes':new,'first_seen':sorted(first.items()),'no_new_code_rounds':[n for n,cs in new if not cs],'claim':'PARTIAL','theory_validated':False,'saturation_claimed':False}
