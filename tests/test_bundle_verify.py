"""Real filesystem staged bundle publication, no simulated exports."""
import hashlib,json
from pathlib import Path
import pytest

def test_actual_bundle_publish_and_tamper(tmp_path):
 from sugarcode.report.bundle_verify import publish,verify
 from sugarcode.report.exporters import make_bundle
 out=tmp_path/'bundle';b=make_bundle('result',{'result.txt':'actual output\n'})
 r=publish(b,out);assert r['status']=='verified' and (out/'result.txt').read_text()=='actual output\n'
 assert verify(out)['files_verified']==1
 (out/'result.txt').write_text('tampered')
 with pytest.raises(ValueError):verify(out)
def test_forged_metadata_cannot_publish(tmp_path):
 from sugarcode.report.bundle_verify import publish
 from sugarcode.report.exporters import make_bundle
 b=make_bundle('result',{'x.txt':'data'});b['artifacts']['x.txt']['sha256']='0'*64
 with pytest.raises(ValueError):publish(b,tmp_path/'out')
 assert not (tmp_path/'out').exists()
def test_path_traversal_and_overwrite_refused(tmp_path):
 from sugarcode.report.bundle_verify import publish
 from sugarcode.report.exporters import make_bundle
 b=make_bundle('result',{'x.txt':'data'});b['artifacts']['../escape']=b['artifacts'].pop('x.txt')
 with pytest.raises(ValueError):publish(b,tmp_path/'out')
 assert not (tmp_path/'escape').exists()
 out=tmp_path/'out';out.mkdir();(out/'keep').write_text('keep')
 with pytest.raises(FileExistsError):publish(make_bundle('x',{'x.txt':'new'}),out)
 assert (out/'keep').read_text()=='keep'
def test_symlink_artifact_refused(tmp_path):
 from sugarcode.report.bundle_verify import publish,verify
 from sugarcode.report.exporters import make_bundle
 out=tmp_path/'out';publish(make_bundle('x',{'x.txt':'data'}),out)
 (out/'x.txt').unlink();(out/'x.txt').symlink_to(tmp_path/'absent')
 with pytest.raises(ValueError):verify(out)
