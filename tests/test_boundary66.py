import math
from decimal import Decimal, localcontext
import pytest
from sugarcode.modules.riboswitch.boundary_response import response_curve

@pytest.mark.parametrize('kd,c',[(1,[0,1,2]),(1e100,[0,1e100,1e101])])
def test_decimal_response(kd,c):
    r=response_curve(kd,hill=4,concentrations=c,basal=0)
    with localcontext() as ctx:
        ctx.prec=70
        for x,row in zip(c,r['curve']):
            a,b=Decimal(str(x))**4,Decimal(str(kd))**4
            assert row['occupancy']==pytest.approx(float(a/(a+b)))
    assert r['dynamic_range'] is None

@pytest.mark.parametrize('field',['kd_uM','hill','basal','maximum'])
@pytest.mark.parametrize('v',[True,'1',pytest.param(10**10000,id='huge'),float('nan'),float('inf')])
def test_bad_scalars(field,v):
    kw={'kd_uM':1};kw[field]=v
    with pytest.raises(ValueError):response_curve(**kw)

@pytest.mark.parametrize('c',[[0,float('nan')],[0,True],[0,10**10000],[1,0],[],[0]*10001])
def test_bad_grid(c):
    with pytest.raises(ValueError):response_curve(1,concentrations=c)
