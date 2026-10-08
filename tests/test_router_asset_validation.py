import numpy as np,pytest
from sugarcode.llm.router import Router

def save(path,**changes):
 data=dict(vocab=np.array(['one','two']),idf=np.array([1.,1.]),W=np.zeros((2,2)),b=np.zeros(2),labels=np.array(['one','two']))
 data.update(changes);np.savez_compressed(path,**data)

@pytest.mark.parametrize('changes',[{'W':np.zeros((3,2))},{'idf':np.array([np.nan,1.])},{'W':np.array([[np.inf,0],[0,0]])},{'labels':np.array(['one','one'])},{'vocab':np.array(['one','one'])},{'b':np.zeros(3)}])
def test_corrupt_assets_refused_at_load(tmp_path,changes):
 p=tmp_path/'r.npz';save(p,**changes)
 with pytest.raises(ValueError):Router.load(p)

def test_real_shipped_router_routes():
 from sugarcode.llm.router import default_router
 rows=default_router().route('splice mutation')
 assert len(rows)==3 and all(np.isfinite(x['probability']) for x in rows)
