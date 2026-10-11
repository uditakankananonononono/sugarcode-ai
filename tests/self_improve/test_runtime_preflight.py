import sys
from pathlib import Path
import pytest
from sugarcode.self_improve.runtime_preflight import SandboxEnvironmentUnavailable
from sugarcode.self_improve.sandbox import SandboxRunner
from sugarcode.self_improve.isolation import IsolatedRunner
from sugarcode.self_improve.plans import Candidate, FeaturePlan


def candidate():
    return Candidate(FeaturePlan('m', 'demo', 'keyword_filter', 'd', 'g'),
                     'raise AssertionError("candidate must not run")',
                     'raise AssertionError("tests must not run")')


@pytest.mark.parametrize('isolated', [False, True])
def test_user_site_only_pytest_is_not_a_child_runtime_dependency(tmp_path, monkeypatch, isolated):
    # A real venv without pytest, with a parent-only user-site package available.
    import subprocess
    venv = tmp_path / 'runtime'
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(venv)], check=True)
    child = str(venv / 'bin/python')
    home = tmp_path / 'parent-home'
    site = home / '.local/lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    site.mkdir(parents=True)
    (site / 'pytest.py').write_text('PARENT_ONLY = True\n')
    env = dict(__import__('os').environ, HOME=str(home))
    # venv user site is disabled; use the base interpreter to prove parent-only import.
    base = str(Path(sys.base_prefix) / 'bin/python3')
    subprocess.run([base, '-c', 'import pytest; assert pytest.PARENT_ONLY'], env=env, check=True)
    monkeypatch.setattr(sys, 'executable', child)
    if isolated:
        class LocalIsolated(IsolatedRunner):
            # Exercise real -I dependency semantics; namespace setup is tested separately.
            def _command(self, work):
                return []
        runner = LocalIsolated()
    else:
        runner = SandboxRunner()
    with pytest.raises(SandboxEnvironmentUnavailable, match='child interpreter cannot import pytest'):
        runner.run(candidate())


def test_preflight_no_candidate_files_and_no_candidate_launch(tmp_path, monkeypatch):
    from sugarcode.self_improve import sandbox
    seen = []
    def refused(prefix, **kwargs):
        work = Path(kwargs['cwd'])
        seen.append(work)
        assert list(work.iterdir()) == []
        assert kwargs['env']['HOME'] != str(tmp_path)
        raise SandboxEnvironmentUnavailable('explicit environment diagnostic')
    monkeypatch.setattr(sandbox, 'require_pytest', refused)
    monkeypatch.setattr(sandbox, 'run_bounded_process', lambda *a, **kw: pytest.fail('candidate launched'))
    with pytest.raises(SandboxEnvironmentUnavailable):
        SandboxRunner().run(candidate())
    assert seen and not seen[0].exists()


def test_isolated_preflight_uses_contained_command_before_candidate_write(monkeypatch):
    from types import SimpleNamespace
    from sugarcode.self_improve import isolation
    works = []
    def command(self, work):
        works.append(work)
        return ['contained-wrapper', '--clearenv']
    monkeypatch.setattr(IsolatedRunner, '_command', command)
    monkeypatch.setattr(isolation.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=0))
    def refused(prefix, **kwargs):
        assert prefix == ['contained-wrapper', '--clearenv', sys.executable, '-I']
        assert list(works[0].iterdir()) == []
        raise SandboxEnvironmentUnavailable('explicit environment diagnostic')
    monkeypatch.setattr(isolation, 'require_pytest', refused)
    monkeypatch.setattr(isolation, 'run_bounded_process', lambda *a, **kw: pytest.fail('candidate launched'))
    with pytest.raises(SandboxEnvironmentUnavailable):
        IsolatedRunner().run(candidate())
    assert not works[0].exists()


def test_engine_raises_environment_error_not_empty_proposal_report(tmp_path):
    from sugarcode.self_improve.engine import SelfImprovementEngine
    class Unavailable:
        def run(self, candidate):
            raise SandboxEnvironmentUnavailable('child interpreter cannot import pytest')
    engine = SelfImprovementEngine(module_id=1, module_slug='m', state_dir=tmp_path, sandbox=Unavailable())
    for _ in range(3):
        engine.record_gap('filter only biology grants', exemplar='biology grant')
    with pytest.raises(SandboxEnvironmentUnavailable, match='cannot import pytest'):
        engine.run_cycle()
    events = [row['event'] for row in engine.ledger()]
    assert 'sandbox_environment_unavailable' in events
    assert 'feature_rejected_by_tests' not in events
    assert 'feature_evaluated' not in events
    assert not engine.registry.proposals()


@pytest.mark.parametrize('exit_code,timed_out,overflow', [(1, False, None), (0, True, None), (0, False, 'stderr')])
def test_preflight_bounded_failure_is_explicit(monkeypatch, exit_code, timed_out, overflow):
    from sugarcode.self_improve import runtime_preflight
    from sugarcode.self_improve.bounded_process import CapturedProcess
    def capture(command, **kwargs):
        assert command == ['trusted-python', '-I', '-c', 'import pytest']
        assert kwargs['timeout_seconds'] == 5
        assert kwargs['output_bytes'] == 4096 and kwargs['tail_bytes'] == 1000
        return CapturedProcess(exit_code, b'', b'', timed_out, overflow, 0, 0, 0)
    monkeypatch.setattr(runtime_preflight, 'run_bounded_process', capture)
    with pytest.raises(SandboxEnvironmentUnavailable):
        runtime_preflight.require_pytest(['trusted-python', '-I'])


def test_preflight_start_failure_is_explicit(monkeypatch):
    from sugarcode.self_improve import runtime_preflight
    def failed(*args, **kwargs):
        raise FileNotFoundError('runtime absent')
    monkeypatch.setattr(runtime_preflight, 'run_bounded_process', failed)
    with pytest.raises(SandboxEnvironmentUnavailable, match='could not start'):
        runtime_preflight.require_pytest(['missing-python'])


def test_keep_workdirs_does_not_leak_empty_preflight_workspace(monkeypatch):
    from sugarcode.self_improve import sandbox
    seen = []
    def refused(prefix, **kwargs):
        seen.append(Path(kwargs['cwd']))
        raise SandboxEnvironmentUnavailable('missing pytest')
    monkeypatch.setattr(sandbox, 'require_pytest', refused)
    with pytest.raises(SandboxEnvironmentUnavailable):
        SandboxRunner(keep_workdirs=True).run(candidate())
    assert seen and not seen[0].exists()


def test_actual_containment_missing_pytest_refuses_before_candidate(real_containment, tmp_path, monkeypatch):
    import subprocess
    venv = tmp_path / 'trusted-runtime'
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(venv)], check=True)
    monkeypatch.setattr(sys, 'executable', str(venv / 'bin/python'))
    monkeypatch.setattr(sys, 'prefix', str(venv))
    with pytest.raises(SandboxEnvironmentUnavailable, match='cannot import pytest'):
        IsolatedRunner().run(candidate())
