"""Digital History (canonical1830): PARTIAL caller transcription alignment audit.

left/right exactstr length1..8 printableASCII32..126 including spaces. Unit
insertion/deletion/substitution;identicalmatchcost0. ReturnLevenshteindistance
andnumberoptimalalignmentpaths distinguishing operationorders/indexalignments
(notsameasuniquefinaltexts). Dynamicprogramming eachcellminimumcost/count.
No actualOCR/digitization/authenticity/history verified.
Validateleft type/length/allcharacters thenright. Textinputs only.
"""
SCOPE='PARTIAL: caller printable transcription edit distance and optimal alignment path count'
NOT_CLAIMED=('actual digitization','OCR accuracy','historical authenticity')


def alignment(left,right):
    for name,text in (('left',left),('right',right)):
        if type(text) is not str or not 1<=len(text)<=8:raise ValueError(name+' exact str1..8')
        for c in text:
            if not 32<=ord(c)<=126:raise ValueError(name+' printable ASCII32..126')
    n,m=len(left),len(right);cost=[[0]*(m+1) for _ in range(n+1)];count=[[0]*(m+1) for _ in range(n+1)];count[0][0]=1
    for i in range(n+1):
        for j in range(m+1):
            if not i and not j:continue
            options=[]
            if i:options.append((cost[i-1][j]+1,count[i-1][j]))
            if j:options.append((cost[i][j-1]+1,count[i][j-1]))
            if i and j:options.append((cost[i-1][j-1]+int(left[i-1]!=right[j-1]),count[i-1][j-1]))
            best=min(c for c,k in options);cost[i][j]=best;count[i][j]=sum(k for c,k in options if c==best)
    return {'edit_distance':cost[n][m],'optimal_alignment_paths':count[n][m],'digitization_validated':False}
