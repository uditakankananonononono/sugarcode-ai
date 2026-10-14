"""Exact simultaneous fictitious play in a supplied finite zero-sum game.
NOT_CLAIMED: convergence at a finite budget; authentic payoff model; human
learning prediction; equilibrium unless gap zero; real-world execution.
"""
from fractions import Fraction
import math


def learn(payoffs,row_prior,column_prior,rounds):
    if type(rounds) is not int or not 1<=rounds<=100:raise ValueError('strict game rounds 1..100')
    if type(payoffs) is not list or not 2<=len(payoffs)<=8:raise ValueError('2..8 row actions before scan')
    if type(payoffs[0]) is not list or not 2<=len(payoffs[0])<=8:raise ValueError('2..8 column actions before scan')
    nr=len(payoffs);nc=len(payoffs[0]);matrix=[]
    for row in payoffs:
        if type(row) is not list or len(row)!=nc:raise ValueError('rectangular payoff matrix')
        vals=[]
        for v in row:
            if type(v) not in (int,float) or not -1000<=v<=1000 or not math.isfinite(v):raise ValueError('strict finite game payoff within -1000..1000')
            vals.append(Fraction(str(v)))
        matrix.append(vals)
    def counts(raw,n):
        if type(raw) is not list or len(raw)!=n:raise ValueError('one prior count per action')
        if any(type(v) is not int or not 0<=v<=1000 for v in raw):raise ValueError('strict integer prior counts 0..1000')
        if sum(raw)==0:raise ValueError('positive prior total for each player')
        return raw[:]
    rc=counts(row_prior,nr);cc=counts(column_prior,nc);history=[]
    def state():
        row=[Fraction(v,sum(rc)) for v in rc];col=[Fraction(v,sum(cc)) for v in cc]
        rv=[sum(v*p for v,p in zip(line,col)) for line in matrix]
        cv=[sum(row[i]*matrix[i][j] for i in range(nr)) for j in range(nc)]
        return row,col,rv,cv
    for t in range(1,rounds+1):
        row,col,rv,cv=state();i=max(range(nr),key=lambda j:(rv[j],-j));j=min(range(nc),key=lambda k:(cv[k],k))
        rc[i]+=1;cc[j]+=1
        history.append({'round':t,'row_action':i,'column_action':j,'row_expected_fraction':[str(v) for v in rv],'column_expected_fraction':[str(v) for v in cv]})
    row,col,rv,cv=state();gap=max(rv)-min(cv);value=sum(row[i]*matrix[i][j]*col[j] for i in range(nr) for j in range(nc))
    return {'row_counts':rc,'column_counts':cc,'row_policy_fraction':[str(v) for v in row],'column_policy_fraction':[str(v) for v in col],
            'value_fraction':str(value),'row_best_value_fraction':str(max(rv)),'column_best_value_fraction':str(min(cv)),
            'zero_sum_gap_fraction':str(gap),'equilibrium_in_supplied_game':gap==0,'history':history,
            'tie_break':'lowest action index','update':'simultaneous best responses to pre-round empirical beliefs including supplied priors','external_effects':[]}
