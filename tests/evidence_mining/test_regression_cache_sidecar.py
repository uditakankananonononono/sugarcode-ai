"""Regression test for behavior at base revision 99cb2d32."""
import json
from hashlib import sha256

from sugarcode.modules.evidence_mining import CachedHTTPClient


def test_non_object_sidecar_is_rejected_not_a_crash(tmp_path):
    calls = []

    def transport(url, headers, timeout):
        calls.append(url)
        return b'{"a": 1}'

    c = CachedHTTPClient(tmp_path, min_interval=0, transport=transport)
    assert c.get("http://x/y") == b'{"a": 1}'
    meta = next(tmp_path.glob("*.json"))
    for bad in ("[]", "null", "3", '"text"'):
        meta.write_text(bad)
        # old code: AttributeError out of get(). New: entry rejected, refetched online.
        assert c.get("http://x/y", refresh=False) == b'{"a": 1}'
        assert json.loads(meta.read_text())["body_sha256"] == sha256(b'{"a": 1}').hexdigest()
    n = len(calls)
    meta.write_text("[]")
    try:
        c.get("http://x/y", offline=True)
    except Exception as exc:  # offline: rejected entry is a verified-cache miss
        assert type(exc).__name__ == "OfflineCacheMiss"
    else:
        raise AssertionError("offline read accepted a non-object sidecar")
    assert len(calls) == n
