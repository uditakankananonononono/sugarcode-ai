"""Row1920 Museum Studies.
PARTIAL: count injective placements under a supplied binary compatibility matrix.
placements(compatibility): exact list1..5 of exact list1..6 binary exact integers,
all rows same width. Rows are artifacts; columns are displays. A full placement
uses one allowed display for every artifact, with no reused display. Return count
of full placements and count using each artifact/display pair, same matrix shape.
Zero placements allowed, including more artifacts than displays. Check outer,
first row width, then each row shape/cells. No real artifacts or curatorial advice.
"""
SCOPE='PARTIAL: supplied binary artifact-display injective placement counting'
NOT_CLAIMED=('curatorial quality','real artifact suitability','museum operations','production readiness')


def placements(compatibility):
    if type(compatibility) is not list or not 1<=len(compatibility)<=5:
        raise ValueError('compatibility exact list1..5')
    if type(compatibility[0]) is not list or not 1<=len(compatibility[0])<=6:
        raise ValueError('first compatibility row exact list1..6')
    width=len(compatibility[0])
    for row in compatibility:
        if type(row) is not list or len(row)!=width:
            raise ValueError('compatibility row exact list matching width')
        for x in row:
            if type(x) is not int or x not in (0,1):
                raise ValueError('compatibility cell exact binary int')
    height=len(compatibility)
    def count(fixed_row=None,fixed_col=None):
        states={0:1}
        for i,row in enumerate(compatibility):
            next_states={}
            for mask,ways in states.items():
                for j,allowed in enumerate(row):
                    if not allowed or mask&(1<<j):continue
                    if i==fixed_row and j!=fixed_col:continue
                    newmask=mask|(1<<j)
                    next_states[newmask]=next_states.get(newmask,0)+ways
            states=next_states
        return sum(states.values())
    return {'placement_count':count(),'usage_counts':[[count(i,j) for j in range(width)] for i in range(height)],'curatorial_quality_validated':False}
