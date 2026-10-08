"""Combined product commands, explicit execution and metadata-only status."""
import json
import os
from pathlib import Path
import subprocess
import sys


def test_both_commands_visible_and_status_never_runs_script(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
    def invoke(*args):
        return subprocess.run([sys.executable, '-m', 'sugarcode.cli', *args],
                              capture_output=True, text=True, env=env)
    help_result = invoke('--help')
    assert help_result.returncode == 0
    assert 'queue-status' in help_result.stdout and 'trusted local script queue' in help_result.stdout
    marker = tmp_path / 'executed'
    script = tmp_path / 'script.py'
    script.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("yes")\nprint(42)\n')
    db = tmp_path / 'q.sqlite'
    submitted = invoke('queue', '--db', str(db), 'submit', 'combined', '--script', str(script))
    assert submitted.returncode == 0, submitted.stdout + submitted.stderr
    assert not marker.exists()
    before = db.read_bytes()
    status = invoke('queue-status', '--db', str(db), '--state', 'pending', '--limit', '1')
    assert status.returncode == 0, status.stdout + status.stderr
    row = json.loads(status.stdout)['jobs'][0]
    assert row['id'] == 'combined' and row['state'] == 'pending'
    assert set(row) == {'id', 'sha256', 'state', 'timeout', 'heartbeat', 'exit_code'}
    assert db.read_bytes() == before and not marker.exists()
    ran = invoke('queue', '--db', str(db), 'run')
    assert ran.returncode == 0 and marker.read_text() == 'yes'
    status = invoke('queue-status', '--db', str(db), '--state', 'succeeded')
    assert status.returncode == 0 and json.loads(status.stdout)['jobs'][0]['state'] == 'succeeded'
    receipt = tmp_path / 'receipt.json'
    assert invoke('queue', '--db', str(db), 'receipt', 'combined', '--out', str(receipt)).returncode == 0
    verified = invoke('queue', '--db', str(db), 'verify', '--receipt', str(receipt))
    assert verified.returncode == 0 and json.loads(verified.stdout)['authenticity_verified'] is False
