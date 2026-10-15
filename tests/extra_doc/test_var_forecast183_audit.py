from copy import deepcopy
from sugarcode.extra_doc import var_forecast183 as m


def test_fresh_output_and_shape():
 d=dict(matrix=[[1,1],[0,1]],state=[1,2],variances=[1,3],horizon=5)
 old=deepcopy(d);r=m.forecast(d);expected=deepcopy(r)
 assert type(r) is dict and len(r['means'])==6 and len(r['covariances'])==6
 assert type(r['claims']) is list and all(type(v) is bool and v is False for v in r['claims'])
 for row in r['means']:assert type(row) is list and len(row)==2
 for matrix in r['covariances']:
  assert type(matrix) is list and len(matrix)==2
  for row in matrix:assert type(row) is list and len(row)==2 and all(type(v) is int for v in row)
 r['means'][0][0]=999;r['covariances'][0][0][0]=999;r['claims'][0]=True
 assert m.forecast(d)==expected and d==old
