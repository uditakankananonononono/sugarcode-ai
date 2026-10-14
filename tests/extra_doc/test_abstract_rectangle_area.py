import itertools,re,pytest
from sugarcode.extra_doc.abstract_rectangle_area import areas as call
class Number(int):pass
class Items(tuple):pass
NC=('wound_measurement', 'care_planning', 'clinical_interpretation')
def oracle(rows,scalar):
    values=[];above=[];total=0
    for i,(width,height) in enumerate(rows):
        area=sum(width for _ in range(height));values.append(area);total+=area
        if not area<=scalar:above.append(i)
    return {'abstract_rectangle_area_validated':False,'not_claimed':NC,
            'areas':tuple(values),'total_area':total,'above_positions':tuple(above),'above_count':len(above)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:call(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))
def test_oracle():
    choices=tuple(itertools.product((1,1,100),repeat=2))
    for n in (1,2,3):
        for rows in itertools.product(choices,repeat=n):
            for scalar in (0,1,10000):assert call(rows,scalar)==oracle(rows,scalar)
def test_caps_and_positions():
    for rows in (((100,100),)*20,((1,1),)*20,((100,1),)+((1,1),)*19,((1,1),)*19+((100,1),)):
        for scalar in (0,1,10000):assert call(rows,scalar)==oracle(rows,scalar)
def test_types_bounds_order():
    for bad in ((),(None,)*21,[(1,1)],Items(((1,1),)),None,'é'):
        refuse((bad,None),'rectangles: tuple of 1 to 20 pairs required')
    for pos in (0,1,19):
        for bad in (None,(),(1,), (1,1,1),[1,1],Items((1,1)),'Ж'):
            rows=[(1,1)]*20;rows[pos]=bad
            refuse((tuple(rows),None),f'rectangles[{pos}]: pair (width, height) required')
        for j,name in enumerate(('width', 'height')):
            for bad in (0,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                row=[1,1];row[j]=bad;rows=[(1,1)]*20;rows[pos]=tuple(row)
                refuse((tuple(rows),None),f'rectangles[{pos}].{name}: whole number 1 to 100 required')
    for bad in (-1,10001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse((((1,1),),bad),'threshold: whole number 0 to 10000 required')
