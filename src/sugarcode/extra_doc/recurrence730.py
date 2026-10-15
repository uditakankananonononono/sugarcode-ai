"""Row730 Rapport Building: PARTIAL supplied-sequence cross-recurrence diagnostics.
first and second exact lists1..8 exact ints-5..5;tolerance exact int0..10;
minimum diagonal length exact int1..8. Recurrence cell(i,j)=1if absolute
value difference<=tolerance. Enumerate maximal down-right contiguous1runs,
including length1. Return binary matrix,exact recurrence fraction,and fraction
of recurrent cells in diagonal runs at least minimum length (Noneif no cells).
No actual interpersonal rapport,causal coordination or sequence validity claim;
this computes a conventional cross-recurrence statistic,not a relationship.
NOT_CLAIMED: rapport inference, causal coordination, valid observations, production readiness.
"""
from fractions import Fraction as F
SCOPE='PARTIAL: exact supplied cross-recurrence matrix and diagonal determinism'
NOT_CLAIMED=('rapport inference','causal coordination','valid observations','production readiness')

def diagnose(first,second,tolerance,minimum):
    for seq in (first,second):
        if type(seq) is not list or not 1<=len(seq)<=8:raise ValueError('sequence must be exact list1..8')
        if any(type(v) is not int or not -5<=v<=5 for v in seq):raise ValueError('values must be exact ints-5..5')
    if type(tolerance) is not int or not 0<=tolerance<=10:raise ValueError('tolerance must be exact int0..10')
    if type(minimum) is not int or not 1<=minimum<=8:raise ValueError('minimum must be exact int1..8')
    matrix=[[int(abs(a-b)<=tolerance) for b in second] for a in first];runs=[]
    for i,row in enumerate(matrix):
        for j,v in enumerate(row):
            if v and (i==0 or j==0 or not matrix[i-1][j-1]):
                length=0
                while i+length<len(first) and j+length<len(second) and matrix[i+length][j+length]:length+=1
                runs.append((i,j,length))
    total=sum(map(sum,matrix));covered=sum(length for i,j,length in runs if length>=minimum)
    return {'matrix':matrix,'diagonals':runs,'recurrence':F(total,len(first)*len(second)),'determinism':F(covered,total) if total else None,'rapport_validated':False}
