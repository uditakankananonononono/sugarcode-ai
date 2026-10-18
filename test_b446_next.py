import itertools
import unittest
from functools import lru_cache
import b446_next as m


def words(n):
    return [''.join(p) for k in range(n+1) for p in itertools.product('ab',repeat=k)]


def subs(a):
    return [''.join(a[i] for i in range(len(a)) if mask>>i&1) for mask in range(1<<len(a))]


def paths(a,b,sub=1,transpose=False):
    # Enumerate every monotone alignment path, independently of DP tables.
    if not a:return [len(b)]
    if not b:return [len(a)]
    result=[1+x for x in paths(a[1:],b,sub,transpose)]
    result += [1+x for x in paths(a,b[1:],sub,transpose)]
    result += [(0 if a[0]==b[0] else sub)+x for x in paths(a[1:],b[1:],sub,transpose)]
    if transpose and len(a)>=2 and len(b)>=2 and a[0]==b[1] and a[1]==b[0]:
        result += [1+x for x in paths(a[2:],b[2:],sub,transpose)]
    return result


def is_sub(a,b):
    it=iter(b)
    return all(any(x==y for y in it) for x in a)


class WordTests(unittest.TestCase):
    def test_all_binary_words_to_three(self):
        all_words=words(3)
        for a,b in itertools.product(all_words,repeat=2):
            ps=paths(a,b)
            self.assertEqual(m.levenshtein_distance(a,b),min(ps))
            self.assertEqual(m.levenshtein_optimal_path_count(a,b),ps.count(min(ps)))
            self.assertEqual(m.indel_distance(a,b),min(paths(a,b,2)))
            self.assertEqual(m.optimal_string_alignment_distance(a,b),min(paths(a,b,1,True)))
            common=set(subs(a))&set(subs(b))
            self.assertEqual(m.longest_common_subsequence_length(a,b),max(map(len,common)))
            super_length=next(n for n in range(max(len(a),len(b)),len(a)+len(b)+1) if any(is_sub(a,''.join(w)) and is_sub(b,''.join(w)) for w in itertools.product('ab',repeat=n)))
            self.assertEqual(m.shortest_common_supersequence_length(a,b),super_length)
            self.assertEqual(m.subsequence_embedding_count(a,b),subs(a).count(b))
            strings={a[i:j] for i in range(len(a)+1) for j in range(i,len(a)+1)}
            self.assertEqual(m.longest_common_substring_length(a,b),max(len(s) for s in strings if s in b))
            if len(a)==len(b):
                self.assertEqual(m.hamming_distance(a,b),len(a)-sum(a[i]==b[i] for i in range(len(a))))
        for a in words(4):
            length=next(n for n in range(len(a),2*len(a)+1) if any(w==w[::-1] and is_sub(a,''.join(w)) for w in itertools.product('ab',repeat=n)))
            self.assertEqual(m.minimum_palindrome_insertions(a),length-len(a))

    def test_caps_and_refusal_order(self):
        binary=[m.levenshtein_distance,m.optimal_string_alignment_distance,m.indel_distance,m.longest_common_subsequence_length,m.shortest_common_supersequence_length,m.hamming_distance,m.levenshtein_optimal_path_count,m.subsequence_embedding_count,m.longest_common_substring_length]
        unary=[m.minimum_palindrome_insertions]
        for call in binary:
            self.assertIsInstance(call('a'*8,'b'*8),int)
            for invalid,error,msg in [(True,TypeError,'word must be a string'),(1,TypeError,'word must be a string'),([],TypeError,'word must be a string'),('a'*9,ValueError,'word too long'),('c'*9,ValueError,'word too long'),('c',ValueError,'word alphabet must be ab')]:
                for left,right in ((invalid,False),('',invalid)):
                    with self.assertRaisesRegex(error,'^'+msg+'$'):call(left,right)
        for call in unary:
            self.assertEqual(call('a'*8),0)
            for invalid,error,msg in [(True,TypeError,'word must be a string'),(1,TypeError,'word must be a string'),('a'*9,ValueError,'word too long'),('c'*9,ValueError,'word too long'),('c',ValueError,'word alphabet must be ab')]:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(invalid)
        with self.assertRaisesRegex(ValueError,'^words must have equal length$'):m.hamming_distance('a','')
        self.assertFalse(m.CLAIMS)
        self.assertEqual(m.optimal_string_alignment_distance('ab','ba'),1)
        self.assertEqual(m.levenshtein_distance('ab','ba'),2)
        self.assertEqual(m.minimum_palindrome_insertions('ab'),1)
        self.assertEqual(m.minimum_palindrome_insertions('abba'),0)

if __name__=='__main__':unittest.main()
