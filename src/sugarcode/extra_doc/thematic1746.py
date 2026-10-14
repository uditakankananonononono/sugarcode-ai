"""Doc row1746 Thematic Analysis: PARTIAL supplied code-to-theme coverage.

Themes exact list1..20 (id,codes) tuples, codes exact list1..20 unique labels,
unique theme IDs. Excerpts exact list1..100 (id,codes), codes exact list0..20
unique labels; unique excerpt IDs. Labels exact nonblank str1..80. Codes may
map to several themes. Return excerpt theme matches, uncovered codes and theme
excerpt counts. No inferred themes, meanings or actual qualitative validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def _rows(rows,kind,lo,hi,mincodes):
    if type(rows) is not list or not lo<=len(rows)<=hi:raise ValueError(kind+' must be an exact list with '+str(lo)+'..'+str(hi)+' entries')
    ids=set()
    for row in rows:
        if type(row) is not tuple or len(row)!=2:raise ValueError(kind+' row must be an id codes tuple')
        name,codes=row
        if not _label(name) or name in ids:raise ValueError(kind+' IDs must be unique valid labels')
        ids.add(name)
        if type(codes) is not list or not mincodes<=len(codes)<=20 or any(not _label(x) for x in codes) or len(set(codes))!=len(codes):raise ValueError(kind+' codes must be an exact list of '+str(mincodes)+'..20 unique valid labels')


def map_themes(themes,excerpts):
    _rows(themes,'themes',1,20,1);_rows(excerpts,'excerpts',1,100,0)
    mapped={c for n,cs in themes for c in cs}
    coverage=[(n,[t for t,tc in themes if any(c in tc for c in cs)],sorted(c for c in cs if c not in mapped)) for n,cs in excerpts]
    counts=[(t,sum(any(c in tc for c in cs) for n,cs in excerpts)) for t,tc in themes]
    return {'coverage':coverage,'theme_counts':counts,'claim':'PARTIAL','themes_validated':False}
