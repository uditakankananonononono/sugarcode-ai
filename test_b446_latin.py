import itertools
import unittest
import b446_latin as m


def latin_by_counts(a):
    n=len(a)
    return all(sum(x==s for x in row)==1 for row in a for s in range(n)) and all(sum(a[r][c]==s for r in range(n))==1 for c in range(n) for s in range(n))


def transversal_brute(a):
    n=len(a);count=0
    for cells in itertools.combinations([(r,c) for r in range(n) for c in range(n)],n):
        if len({r for r,c in cells})==n and len({c for r,c in cells})==n and len({a[r][c] for r,c in cells})==n:count+=1
    return count


class LatinTests(unittest.TestCase):
    def test_tables_and_independent_oracles(self):
        examples=[((0,),)]
        examples += [tuple(tuple(flat[i*2:i*2+2]) for i in range(2)) for flat in itertools.product(range(2),repeat=4)]
        examples += [tuple(tuple((r+c)%n for c in range(n)) for r in range(n)) for n in (3,4)]
        examples += [((0,0,1),(1,2,2),(2,1,0))]
        for a in examples:
            n=len(a)
            self.assertEqual(m.is_latin(a),latin_by_counts(a))
            row_collisions=sum(sum(row.count(s)*(row.count(s)-1)//2 for s in range(n)) for row in a)
            col_collisions=sum(sum(col.count(s)*(col.count(s)-1)//2 for s in range(n)) for col in zip(*a))
            self.assertEqual(m.row_collision_count(a),row_collisions)
            self.assertEqual(m.column_collision_count(a),col_collisions)
            trans=tuple(tuple(a[c][r] for c in range(n)) for r in range(n))
            self.assertEqual(m.transpose_square(a),trans)
            self.assertEqual(m.transpose_square(trans),a)
            self.assertEqual(m.transversal_count(a),transversal_brute(a))
            self.assertEqual(m.diagonal_sum(a),sum(a[i][i] for i in range(n)))
            flat=[x for row in a for x in row]
            self.assertEqual(m.symbol_histogram(a),tuple(flat.count(s) for s in range(n)))
            if latin_by_counts(a):
                reduced=m.reduce_latin_square(a)
                self.assertTrue(latin_by_counts(reduced))
                self.assertEqual(reduced[0],tuple(range(n)))
                self.assertEqual(tuple(row[0] for row in reduced),tuple(range(n)))
                self.assertEqual(m.reduce_latin_square(reduced),reduced)
                # Independent enumeration of symbol renaming and row order.
                candidates=[]
                for symbols in itertools.permutations(range(n)):
                    renamed=tuple(tuple(symbols[x] for x in row) for row in a)
                    if renamed[0]!=tuple(range(n)):continue
                    for rows in itertools.permutations(renamed):
                        if tuple(row[0] for row in rows)==tuple(range(n)):candidates.append(rows)
                self.assertEqual(candidates,[reduced])
            else:
                with self.assertRaisesRegex(ValueError,'^table must be Latin$'):m.reduce_latin_square(a)
        for a in examples:
            for b in examples:
                if len(a)!=len(b):continue
                n=len(a)
                pairs=[(a[r][c],b[r][c]) for r in range(n) for c in range(n)]
                distinct=sum(any(p==(x,y) for p in pairs) for x in range(n) for y in range(n))
                self.assertEqual(m.orthogonal_pair_count(a,b),distinct)
                self.assertEqual(m.is_orthogonal(a,b),latin_by_counts(a) and latin_by_counts(b) and all(pairs.count((x,y))==1 for x in range(n) for y in range(n)))
        a=tuple(tuple((r+c)%3 for c in range(3)) for r in range(3))
        b=tuple(tuple((r+2*c)%3 for c in range(3)) for r in range(3))
        self.assertTrue(m.is_orthogonal(a,b))

    def test_refusals_and_caps(self):
        funcs=[m.row_collision_count,m.column_collision_count,m.is_latin,lambda a:m.orthogonal_pair_count(a,((0,),)),lambda a:m.is_orthogonal(a,((0,),)),m.transpose_square,m.reduce_latin_square,m.transversal_count,m.diagonal_sum,m.symbol_histogram]
        bads=[(None,TypeError,'table must be a list or tuple'),(iter([]),TypeError,'table must be a list or tuple'),([],ValueError,'order out of range'),([None]*5,ValueError,'order out of range'),([None],TypeError,'row must be a list or tuple'),([[True,False]],ValueError,'table must be square'),([[True]],TypeError,'symbol must be an integer'),([[0.0]],TypeError,'symbol must be an integer'),([[-1]],ValueError,'symbol out of range'),([[1]],ValueError,'symbol out of range')]
        for call in funcs:
            for a,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(a)
        cap=tuple(tuple((r+c)%4 for c in range(4)) for r in range(4))
        for call in funcs:
            if call not in (funcs[3],funcs[4]):call(cap)
        for call in (m.orthogonal_pair_count,m.is_orthogonal):
            call(cap,cap)
            with self.assertRaisesRegex(ValueError,'^orders must agree$'):call(cap,((0,),))
            for a,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(((0,),),a)
        with self.assertRaisesRegex(ValueError,'^table must be square$'):m.is_latin([[True,0],[0]])
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
