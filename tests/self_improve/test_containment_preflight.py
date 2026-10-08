import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest


def module():
    spec=importlib.util.spec_from_file_location('containment_checks',Path(__file__).with_name('conftest.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_preflight_permission_refusal_is_explicit(tmp_path,monkeypatch):
    m=module();monkeypatch.setattr(m.IsolatedRunner,'_command',lambda *a:['bwrap'])
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1,stdout=b'',stderr=b'bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted'))
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


@pytest.mark.parametrize('stderr', [b'python: cannot open file', b'bwrap: invalid option', b'unknown startup failure'])
def test_non_environment_nonzero_fails(tmp_path,monkeypatch,stderr):
    m=module();monkeypatch.setattr(m.IsolatedRunner,'_command',lambda *a:['invalid'])
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1,stdout=b'',stderr=stderr))
    with pytest.raises(RuntimeError,match='unexplained containment startup failure'):
        m.containment_unavailable_reason(tmp_path)


@pytest.mark.parametrize('error',[FileNotFoundError('bad interpreter'),PermissionError('bad executable permissions'),OSError('unknown OS failure')])
def test_os_errors_fail_not_skip(tmp_path,monkeypatch,error):
    m=module();monkeypatch.setattr(m.IsolatedRunner,'_command',lambda *a:['invalid'])
    def fail(*a,**k):raise error
    monkeypatch.setattr(m.subprocess,'run',fail)
    with pytest.raises(type(error)):m.containment_unavailable_reason(tmp_path)


def test_probe_timeout_fails_not_skip(tmp_path,monkeypatch):
    m=module();monkeypatch.setattr(m.IsolatedRunner,'_command',lambda *a:['bwrap'])
    def fail(*a,**k):raise m.subprocess.TimeoutExpired('bwrap',5)
    monkeypatch.setattr(m.subprocess,'run',fail)
    with pytest.raises(m.subprocess.TimeoutExpired):m.containment_unavailable_reason(tmp_path)


def test_unsafe_runtime_refusal_fails_not_skip(tmp_path,monkeypatch):
    m=module()
    def fail(*a):raise m.IsolationUnavailable('unsafe Python runtime mount root')
    monkeypatch.setattr(m.IsolatedRunner,'_command',fail)
    with pytest.raises(m.IsolationUnavailable):m.containment_unavailable_reason(tmp_path)


def test_allowlist_requires_exact_status_and_output(tmp_path,monkeypatch):
    m=module();monkeypatch.setattr(m.IsolatedRunner,'_command',lambda *a:['bwrap'])
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=2,stdout=b'',stderr=m._ALLOWED_STDERR.encode()))
    with pytest.raises(RuntimeError):m.containment_unavailable_reason(tmp_path)
