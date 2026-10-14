"""Exact finite-master Benders decomposition for scalar shortage recourse.
NOT_CLAIMED: arbitrary recourse LPs; authentic demands; scalable master solver;
runtime integration or external execution.
"""
from fractions import Fraction as F
import math


def solve(options,demands,penalties,iterations):
    if type(options) is not list or not 1<=len(options)<=80:raise ValueError('1..80 Benders options before scan')
    if type(demands) is not list or not 1<=len(demands)<=20:raise ValueError('1..20 Benders recourse demands before scan')
    def num(v,lo):
        if type(v) not in (int,float) or not lo<=v<=1000 or not math.isfinite(v):raise ValueError('strict finite bounded Benders number')
        return F(str(v))
    menu=[]
    for row in options:
        if type(row) is not list or len(row)!=2:raise ValueError('Benders capacity and fixed cost pair')
        menu.append((num(row[0],0),num(row[1],-1000)))
    d=[num(v,0) for v in demands]
    if type(penalties) is not list or len(penalties)!=len(d):raise ValueError('one penalty per Benders demand')
    p=[num(v,0) for v in penalties]
    if type(iterations) is not int or not 1<=iterations<=80:raise ValueError('strict Benders iterations 1..80')
    cuts=[(F(0),F(0))];trace=[];incumbent=None;best=None;converged=False
    for _ in range(iterations):
        master=[c+max(a+b*x for a,b in cuts) for x,c in menu];i=min(range(len(menu)),key=lambda i:(master[i],i));x,c=menu[i];lower=master[i]
        shortages=[max(v-x,F(0)) for v in d];dual=[q if v>x else F(0) for v,q in zip(d,p)];recourse=sum(q*v for q,v in zip(p,shortages));value=c+recourse
        if best is None or (value,i)<(best,incumbent):best=value;incumbent=i
        gap=best-lower;intercept=sum(q*v for q,v in zip(dual,d));slope=-sum(dual)
        trace.append({'option_index':i,'lower_bound_fraction':str(lower),'incumbent_objective_fraction':str(best),'incumbent_index':incumbent,
                      'recourse_fraction':str(recourse),'shortages_fraction':[str(v) for v in shortages],'dual_fraction':[str(v) for v in dual],
                      'cut_intercept_fraction':str(intercept),'cut_slope_fraction':str(slope),'gap_fraction':str(gap),'cuts_used':len(cuts)})
        if gap==0:converged=True;break
        cuts.append((intercept,slope))
    return {'selected_index':incumbent,'objective_fraction':str(best),'lower_bound_fraction':str(lower),'gap_fraction':str(gap),
            'converged_exact_in_supplied_menu':converged,'trace':trace,'iterations_used':len(trace),'external_effects':[]}
