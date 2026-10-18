import itertools
import math
import unittest
import b446_graphs as m


def components(n,edges):
    reach=[[i==j for j in range(n)] for i in range(n)]
    for u,v in edges:reach[u][v]=reach[v][u]=True
    for k in range(n):
        for i in range(n):
            for j in range(n):reach[i][j]=reach[i][j] or (reach[i][k] and reach[k][j])
    return {tuple(j for j in range(n) if reach[i][j]) for i in range(n)}


def recursive_matchings(vertices,edges):
    if not vertices:return [()]
    u=min(vertices);rest=vertices-{u}
    out=recursive_matchings(rest,edges)
    for v in rest:
        if (min(u,v),max(u,v)) in edges:
            out += [((u,v),)+tail for tail in recursive_matchings(rest-{v},edges)]
    return out


def coloring_backtrack(n,edges,k):
    def walk(prefix):
        if len(prefix)==n:return 1
        u=len(prefix)
        return sum(walk(prefix+[c]) for c in range(k) if all(prefix[v]!=c for v in range(u) if (v,u) in edges))
    return walk([])


class GraphTests(unittest.TestCase):
    def test_all_graphs_to_four(self):
        for n in range(5):
            possible=list(itertools.combinations(range(n),2))
            for mask in range(1<<len(possible)):
                edges=[e for i,e in enumerate(possible) if mask>>i&1]
                parts=components(n,edges)
                self.assertEqual(m.connected_component_count(n,edges),len(parts))
                self.assertEqual(m.cycle_rank(n,edges),len(edges)-sum(len(c)-1 for c in parts))
                trees=forests=0
                for choice in range(1<<len(edges)):
                    subset=[e for i,e in enumerate(edges) if choice>>i&1]
                    cc=components(n,subset)
                    if len(subset)==n-len(cc):
                        forests+=math.prod(map(len,cc))
                        trees+=int(n>0 and len(cc)==1)
                self.assertEqual(m.spanning_tree_count(n,edges),trees)
                self.assertEqual(m.rooted_forest_count(n,edges),forests)
                matches=recursive_matchings(set(range(n)),set(edges))
                self.assertEqual(m.matching_count(n,edges),len(matches))
                self.assertEqual(m.perfect_matching_count(n,edges),sum(len(x)*2==n for x in matches))
                def independent(vertices):
                    if not vertices:return 1
                    u=min(vertices);rest=vertices-{u}
                    neighbors={v for v in rest if (min(u,v),max(u,v)) in edges}
                    return independent(rest)+independent(rest-neighbors)
                count=independent(set(range(n)))
                self.assertEqual(m.independent_set_count(n,edges),count)
                self.assertEqual(m.vertex_cover_count(n,edges),count)
                counts=[coloring_backtrack(n,set(edges),k) for k in range(7)]
                for k in range(7):self.assertEqual(m.proper_coloring_count(n,edges,k),counts[k])
                self.assertEqual(m.chromatic_number(n,edges),next(k for k,c in enumerate(counts) if c))

    def test_caps_and_all_entry_refusals(self):
        funcs=[m.spanning_tree_count,m.rooted_forest_count,m.matching_count,m.perfect_matching_count,m.independent_set_count,m.vertex_cover_count,lambda n,e:m.proper_coloring_count(n,e,1),m.chromatic_number,m.connected_component_count,m.cycle_rank]
        bads=[(True,None,TypeError,'vertex count must be an integer'),(1.0,[],TypeError,'vertex count must be an integer'),(-1,[],ValueError,'vertex count out of range'),(7,None,ValueError,'vertex count out of range'),(2,None,TypeError,'edges must be a list or tuple'),(2,iter([]),TypeError,'edges must be a list or tuple'),(2,[None]*16,ValueError,'edge count out of range'),(2,[None],TypeError,'edge must be a list or tuple'),(2,[(True,)],ValueError,'edge must have two endpoints'),(2,[(True,False)],TypeError,'vertex must be an integer'),(2,[(0,1.0)],TypeError,'vertex must be an integer'),(2,[(-1,True)],ValueError,'vertex out of range'),(2,[(0,2)],ValueError,'vertex out of range'),(2,[(0,0)],ValueError,'loops not allowed'),(2,[(0,1),(1,0)],ValueError,'edges must be distinct')]
        complete=list(itertools.combinations(range(6),2))
        for call in funcs:
            for n,edges,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(n,edges)
            call(0,[]);call(6,complete)
        self.assertEqual(m.spanning_tree_count(6,complete),6**4)
        self.assertEqual(m.rooted_forest_count(6,complete),7**5)
        self.assertEqual(m.perfect_matching_count(6,complete),15)
        self.assertEqual(m.chromatic_number(6,complete),6)
        self.assertEqual(m.proper_coloring_count(6,complete,6),math.factorial(6))
        for bad in (True,1.0,float('inf'),float('nan')):
            with self.assertRaisesRegex(TypeError,'^colors must be an integer$'):m.proper_coloring_count(0,[],bad)
        for bad in (-1,7):
            with self.assertRaisesRegex(ValueError,'^colors out of range$'):m.proper_coloring_count(0,[],bad)
        with self.assertRaisesRegex(TypeError,'^vertex count must be an integer$'):m.proper_coloring_count(True,None,False)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
