import itertools,re,pytest
from sugarcode.extra_doc.abstract_edge_neighbors import neighbors
class Number(int):pass
class Items(tuple):pass

def oracle(edges,vertex):
    adjacent=tuple(candidate for candidate in range(100) if candidate!=vertex and ((vertex,candidate) in edges or (candidate,vertex) in edges))
    return {'abstract_edge_neighbors_validated':False,'not_claimed':('real_person_identification','contact_tracing','medical_decisions'),'neighbors':adjacent,'degree':len(adjacent),'isolated':not adjacent}

def refuse(args,message):
    with pytest.raises(ValueError) as e:neighbors(*args)
    assert re.fullmatch(re.escape(message),str(e.value))

def test_oracle():
    choices=tuple(itertools.product((0,1,99),repeat=2))
    for n in (0,1,2,3):
        for edges in itertools.product(choices,repeat=n):
            for vertex in (0,1,2,99):assert neighbors(edges,vertex)==oracle(edges,vertex)

def test_caps():
    for edges in (((0,99),)*30,((99,99),)*30,tuple((i,99) for i in range(30)),tuple((99,i) for i in reversed(range(30)))):
        for vertex in (0,1,99):assert neighbors(edges,vertex)==oracle(edges,vertex)

def test_bad():
    for bad in ((None,)*31,[],Items(()),None,'é'):
        refuse((bad,None),'edges: tuple of 0 to 30 pairs required')
    for pos in (0,1,29):
        for bad in (None,(),(0,), (0,1,2),[0,1],Items((0,1)),'Ж'):
            rows=[(0,1)]*30;rows[pos]=bad
            refuse((tuple(rows),None),f'edges[{pos}]: vertex pair required')
        for col in (0,1):
            for bad in (-1,100,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                rows=[(0,1)]*30;edge=[0,1];edge[col]=bad;rows[pos]=tuple(edge)
                refuse((tuple(rows),None),f'edges[{pos}][{col}]: whole number 0 to 99 required')
    for bad in (-1,100,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((),bad),'vertex: whole number 0 to 99 required')
