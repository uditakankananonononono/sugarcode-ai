"""Exact distances and counts over bounded caller-supplied binary words.

SCOPE: strings over 'ab', length at most 8, pure deterministic arithmetic.
NOT_CLAIMED: language understanding, retrieval, network, product integration.
"""
CLAIMS = False
SCOPE = "exact binary-word distances and counts only"
NOT_CLAIMED = "language understanding, retrieval, network, product integration"
MAX_LENGTH = 8


def _word(value):
    if isinstance(value, bool):
        raise TypeError("word must be a string")
    if type(value) is not str:
        raise TypeError("word must be a string")
    if len(value) > MAX_LENGTH:
        raise ValueError("word too long")
    if any(c not in 'ab' for c in value):
        raise ValueError("word alphabet must be ab")
    return value


def _pair(a, b):
    return _word(a), _word(b)


def _edit(a, b, substitution, transpose=False):
    n, k = len(a), len(b)
    table = [[0]*(k+1) for _ in range(n+1)]
    for i in range(n+1): table[i][0] = i
    for j in range(k+1): table[0][j] = j
    for i in range(1,n+1):
        for j in range(1,k+1):
            table[i][j] = min(table[i-1][j]+1, table[i][j-1]+1, table[i-1][j-1]+(0 if a[i-1]==b[j-1] else substitution))
            if transpose and i>=2 and j>=2 and a[i-1]==b[j-2] and a[i-2]==b[j-1]:
                table[i][j] = min(table[i][j], table[i-2][j-2]+1)
    return table[n][k]


def levenshtein_distance(a,b):
    a,b = _pair(a,b)
    return _edit(a,b,1)


def optimal_string_alignment_distance(a,b):
    a,b = _pair(a,b)
    return _edit(a,b,1,True)


def indel_distance(a,b):
    a,b = _pair(a,b)
    return _edit(a,b,2)


def longest_common_subsequence_length(a,b):
    a,b = _pair(a,b)
    row = [0]*(len(b)+1)
    for x in a:
        previous = row[:]
        for j,y in enumerate(b,1):
            row[j] = previous[j-1]+1 if x==y else max(previous[j],row[j-1])
    return row[-1]


def shortest_common_supersequence_length(a,b):
    a,b = _pair(a,b)
    return len(a)+len(b)-longest_common_subsequence_length(a,b)


def hamming_distance(a,b):
    a,b = _pair(a,b)
    if len(a)!=len(b):
        raise ValueError("words must have equal length")
    return sum(x!=y for x,y in zip(a,b))


def levenshtein_optimal_path_count(a,b):
    """Count minimum-cost alignment paths, not distinct edited strings."""
    a,b = _pair(a,b)
    n,k = len(a),len(b)
    costs = [[0]*(k+1) for _ in range(n+1)]
    counts = [[1]*(k+1) for _ in range(n+1)]
    for i in range(n+1): costs[i][0] = i
    for j in range(k+1): costs[0][j] = j
    for i in range(1,n+1):
        for j in range(1,k+1):
            options = [(costs[i-1][j]+1,counts[i-1][j]),(costs[i][j-1]+1,counts[i][j-1]),(costs[i-1][j-1]+(a[i-1]!=b[j-1]),counts[i-1][j-1])]
            best = min(cost for cost,_ in options)
            costs[i][j] = best
            counts[i][j] = sum(count for cost,count in options if cost==best)
    return counts[n][k]


def subsequence_embedding_count(a,b):
    """Count index selections in a that spell b."""
    a,b = _pair(a,b)
    counts = [1]+[0]*len(b)
    for x in a:
        for j in range(len(b),0,-1):
            if x==b[j-1]: counts[j] += counts[j-1]
    return counts[-1]


def longest_common_substring_length(a,b):
    a,b = _pair(a,b)
    row = [0]*(len(b)+1)
    best = 0
    for x in a:
        previous = row
        row = [0]*(len(b)+1)
        for j,y in enumerate(b,1):
            if x==y:
                row[j] = previous[j-1]+1
                best = max(best,row[j])
    return best


def minimum_palindrome_insertions(a):
    a = _word(a)
    n = len(a)
    if n==0: return 0
    table = [[0]*n for _ in range(n)]
    for width in range(2,n+1):
        for i in range(n-width+1):
            j = i+width-1
            table[i][j] = (table[i+1][j-1] if width>2 else 0) if a[i]==a[j] else min(table[i+1][j],table[i][j-1])+1
    return table[0][n-1]
