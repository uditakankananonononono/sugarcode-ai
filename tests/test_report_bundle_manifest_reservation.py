"""Exact reserved-manifest collision canaries. Authored NOT RUN."""
import hashlib
import json

import pytest

from sugarcode.report import make_bundle, write_bundle


def test_constructor_rejects_reserved_manifest():
    with pytest.raises(ValueError, match="reserved"):
        make_bundle("n", {"MANIFEST.json": "original artifact"})


def manual_bundle():
    return {"name": "n", "created_utc": "fixed", "generator": "test", "metadata": {},
            "artifacts": {"ordinary.txt": {"content": "new", "sha256": "unused", "bytes": 3},
                          "MANIFEST.json": {"content": "collision", "sha256": "unused", "bytes": 9}}}


@pytest.mark.parametrize("kind", ["manual", "mutated"])
def test_direct_or_mutated_bundle_rejected_without_touching_existing_bytes(tmp_path, kind):
    (tmp_path / "MANIFEST.json").write_bytes(b"old manifest\r\n\x00")
    (tmp_path / "ordinary.txt").write_bytes(b"old artifact\r\n")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    if kind == "manual":
        bundle = manual_bundle()
    else:
        bundle = make_bundle("n", {"ordinary.txt": "new"})
        bundle["artifacts"]["MANIFEST.json"] = {"content": "collision"}
    with pytest.raises(ValueError, match="reserved"):
        write_bundle(bundle, tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_reserved_direct_bundle_does_not_create_output_directory(tmp_path):
    destination = tmp_path / "not-created"
    with pytest.raises(ValueError, match="reserved"):
        write_bundle(manual_bundle(), destination)
    assert not destination.exists()


def test_ordinary_bundle_success_keeps_artifact_and_generated_manifest(tmp_path):
    bundle = make_bundle("n", {"ordinary.txt": "hello"}, created_utc="fixed")
    result = write_bundle(bundle, tmp_path)
    assert (tmp_path / "ordinary.txt").read_bytes() == b"hello"
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
    assert manifest["files"] == {"ordinary.txt": {"sha256": hashlib.sha256(b"hello").hexdigest(), "bytes": 5}}
    assert result["manifest"] == manifest
    assert set(p.name for p in tmp_path.iterdir()) == {"ordinary.txt", "MANIFEST.json"}
