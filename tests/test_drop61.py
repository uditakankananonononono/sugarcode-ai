"""Drop 61: final commercial sweep - stable entrez cache keys.

The record cache used builtin hash() for filenames, which Python salts
per process: a record cached by one run was unreachable from any other,
making --offline useless across CLI invocations. Locked to sha256.
"""
import hashlib
import urllib.parse

from sugarcode.bio import entrez


def test_cache_filename_is_stable_sha256(monkeypatch, tmp_path):
    monkeypatch.setattr(entrez, "CACHE_DIR", tmp_path)
    params = {"db": "nuccore", "id": "NG_009009.1", "retmode": "text"}
    key = urllib.parse.urlencode(sorted(params.items()))
    expected = hashlib.sha256(f"efetch.fcgi?{key}".encode()).hexdigest()[:32]

    calls = []

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"PAYLOAD"

    def fake_urlopen(url, timeout):
        calls.append(url)
        return _Resp()

    monkeypatch.setattr(entrez.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(entrez, "_MIN_INTERVAL", 0.0)

    first = entrez._get("efetch.fcgi", dict(params))
    assert first == b"PAYLOAD"
    assert (tmp_path / f"{expected}.raw").exists()
    # second call served from cache - no network
    second = entrez._get("efetch.fcgi", dict(params))
    assert second == b"PAYLOAD"
    assert len(calls) == 1
    # offline mode hits the same cache entry
    third = entrez._get("efetch.fcgi", dict(params), offline=True)
    assert third == b"PAYLOAD"
    assert len(calls) == 1
