import hashlib
import os
import pytest
from sugarcode.self_improve.source_admission import (
 SourceLimits,InputLimitExceeded,admit_source_text,read_source_snapshot,
 admit_candidate_text,read_candidate_sources)


@pytest.mark.parametrize('bad',[True,-1,1.0,'1',None])
def test_limits_exact_domain(bad):
 with pytest.raises(ValueError):SourceLimits(bad,1)
 with pytest.raises(ValueError):SourceLimits(1,bad)


@pytest.mark.parametrize('raw',[b'',b'a',b'a\r\nb\n', 'a\u2028z'.encode(),b'\xef\xbb\xbf#bom'])
def test_exact_byte_snapshot_hash_and_no_newline_rewrite(tmp_path,raw):
 p=tmp_path/'code';p.write_bytes(raw)
 s=read_source_snapshot(p,max_bytes=len(raw),expected_sha256=hashlib.sha256(raw).hexdigest())
 assert s.content==raw and s.text==raw.decode() and s.sha256==hashlib.sha256(raw).hexdigest()
 assert p.read_bytes()==raw


@pytest.mark.parametrize('size',[0,1,65536,1048576])
def test_exact_and_one_over_cap(tmp_path,size):
 p=tmp_path/'code';p.write_bytes(b'x'*size)
 assert len(read_source_snapshot(p,max_bytes=size).content)==size
 p.write_bytes(b'x'*(size+1))
 with pytest.raises(InputLimitExceeded):read_source_snapshot(p,max_bytes=size)
 assert p.stat().st_size==size+1


def test_oversize_before_utf8_decode(tmp_path):
 p=tmp_path/'code';p.write_bytes(b'\xff'*20)
 with pytest.raises(InputLimitExceeded):read_source_snapshot(p,max_bytes=19)
 with pytest.raises(UnicodeDecodeError):read_source_snapshot(p,max_bytes=20)


@pytest.mark.parametrize('digest',['a'*64,'A'*64,'short',False])
def test_digest_refuses(tmp_path,digest):
 p=tmp_path/'code';p.write_bytes(b'ok')
 with pytest.raises(ValueError):read_source_snapshot(p,max_bytes=2,expected_sha256=digest)


def test_fifo_and_final_symlink_refuse_without_read(tmp_path,monkeypatch):
 fifo=tmp_path/'fifo';os.mkfifo(fifo)
 p=tmp_path/'regular';p.write_bytes(b'ok');link=tmp_path/'link';link.symlink_to(p)
 def fail(*a):pytest.fail('nonregular source read attempted')
 monkeypatch.setattr(os,'read',fail)
 with pytest.raises(ValueError):read_source_snapshot(fifo,max_bytes=2)
 with pytest.raises(OSError):read_source_snapshot(link,max_bytes=2)


def test_short_reads_not_eof_and_only_cap_plus_one(tmp_path,monkeypatch):
 p=tmp_path/'code';p.write_bytes(b'x'*20);original=os.read;calls=[];total=0
 def short(fd,n):
  nonlocal total
  calls.append(n);raw=original(fd,min(n,3));total+=len(raw);return raw
 monkeypatch.setattr(os,'read',short)
 with pytest.raises(InputLimitExceeded):read_source_snapshot(p,max_bytes=10)
 assert total==11 and max(calls)<=11


def test_descriptor_closed_on_failure(tmp_path,monkeypatch):
 p=tmp_path/'code';p.write_bytes(b'xx');original=os.close;closed=[]
 def close(fd):closed.append(fd);return original(fd)
 monkeypatch.setattr(os,'close',close)
 with pytest.raises(InputLimitExceeded):read_source_snapshot(p,max_bytes=1)
 assert len(closed)==1


def test_multibyte_text_budget_and_builtin_only():
 assert admit_source_text('é',max_bytes=2).content==b'\xc3\xa9'
 with pytest.raises(InputLimitExceeded):admit_source_text('é',max_bytes=1)
 class S(str):
  def encode(self,*a,**k):pytest.fail('coercion called')
 with pytest.raises(ValueError):admit_source_text(S('x'),max_bytes=1)
 with pytest.raises(UnicodeEncodeError):admit_source_text('\ud800',max_bytes=1)


def test_pair_caps_are_independent_and_all_or_nothing(tmp_path):
 assert admit_candidate_text('xx','t',limits=SourceLimits(2,1)).tests.text=='t'
 with pytest.raises(InputLimitExceeded):admit_candidate_text('x','tt',limits=SourceLimits(2,1))
 c=tmp_path/'code';t=tmp_path/'tests';c.write_bytes(b'xx');t.write_bytes(b'tt')
 before=(c.read_bytes(),t.read_bytes())
 with pytest.raises(InputLimitExceeded):read_candidate_sources(c,t,limits=SourceLimits(2,1))
 assert (c.read_bytes(),t.read_bytes())==before


def test_empty_source_is_bytes_admitted_not_syntax_validated():
 assert admit_candidate_text('','',limits=SourceLimits(0,0)).code.content==b''


def test_snapshot_not_reloaded_after_replacement(tmp_path):
 p=tmp_path/'code';p.write_bytes(b'old');s=read_source_snapshot(p,max_bytes=3)
 p.write_bytes(b'new')
 assert s.content==b'old' and s.text=='old'


@pytest.mark.parametrize('kind',['keyword_filter','scoring_rule','text_transform','aggregator','threshold_alert','field_extractor'])
def test_real_new_template_and_test_sources_fit_proposed_limits(kind,tmp_path):
 from sugarcode.self_improve.codegen import synthesize_code
 from sugarcode.self_improve.plans import FeaturePlan
 from sugarcode.self_improve.testsynth import synthesize_tests
 plan=FeaturePlan('m','source_case',kind,'description','gap',{})
 code=synthesize_code(plan);tests=synthesize_tests(plan,[])
 admitted=admit_candidate_text(code,tests,limits=SourceLimits(1048576,1048576))
 c=tmp_path/'feature.py';t=tmp_path/'test_feature.py'
 c.write_bytes(admitted.code.content);t.write_bytes(admitted.tests.content)
 read=read_candidate_sources(c,t,limits=SourceLimits(1048576,1048576),code_sha256=admitted.code.sha256,test_sha256=admitted.tests.sha256)
 assert read==admitted


def test_read_error_closes_descriptor_and_returns_no_snapshot(tmp_path,monkeypatch):
 p=tmp_path/'code';p.write_bytes(b'code');closed=[];original=os.close
 def error(*a):raise OSError('injected read error')
 def close(fd):closed.append(fd);original(fd)
 monkeypatch.setattr(os,'read',error);monkeypatch.setattr(os,'close',close)
 with pytest.raises(OSError):read_source_snapshot(p,max_bytes=4)
 assert len(closed)==1
