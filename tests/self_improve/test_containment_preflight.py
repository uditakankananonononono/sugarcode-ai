import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest


def module():
    spec=importlib.util.spec_from_file_location('containment_checks',Path(__file__).with_name('conftest.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_preflight_permission_refusal_is_explicit(tmp_path,monkeypatch):
    m=module();monkeypatch.setattr(m.IsolatedRunner,'_command',lambda *a:['bwrap'])
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1,stderr=b'Failed RTM_NEWADDR: Operation not permitted'))
    assert 'Operation not permitted' in m.containment_unavailable_reason(tmp_path)


def test_preflight_success_does_not_skip(tmp_path,monkeypatch):
    m=module();monkeypatch.setattr(m.IsolatedRunner,'_command',lambda *a:['bwrap'])
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stderr=b''))
    assert m.containment_unavailable_reason(tmp_path) is None


def test_preflight_does_not_swallow_programming_failure(tmp_path,monkeypatch):
    m=module()
    def broken(*args):raise ValueError('real implementation failure')
    monkeypatch.setattr(m.IsolatedRunner,'_command',broken)
    with pytest.raises(ValueError,match='real implementation failure'):
        m.containment_unavailable_reason(tmp_path)


def test_fixture_skip_is_loud_and_environment_only(tmp_path,monkeypatch):
    m=module();monkeypatch.setattr(m,'containment_unavailable_reason',lambda _: 'Operation not permitted')
    with pytest.raises(pytest.skip.Exception,match='REAL CONTAINMENT NOT VERIFIED.*Operation not permitted'):
        m.real_containment.__wrapped__(tmp_path)


def test_missing_binary_refusal(tmp_path,monkeypatch):
    m=module()
    def unavailable(*args):raise m.IsolationUnavailable('bubblewrap executable unavailable')
    monkeypatch.setattr(m.IsolatedRunner,'_command',unavailable)
    assert m.containment_unavailable_reason(tmp_path)=='bubblewrap executable unavailable'
