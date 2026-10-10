"""SC-R01 standalone fixtures. Authored-not-run; no integrated repair verdict.

The validator fixtures below are not SC-J02 implementations. They deliberately
return known prevalidated fixture state, or raise a sentinel boundary exception.
"""
import hashlib
from pathlib import Path

import pytest

from sugarcode.self_improve.proposal_preflight_r01 import (
    ProposalPreflightError,
    preflight_proposal,
)

RAW = b'{"module":"m1","features":{},"proposals":{}}'
CODE = 'def run(items, params=None):\n    return {"items": items}\n'
TEST_CODE = 'def test_run():\n    assert run([]) == {"items": []}\n'


@pytest.fixture
def directory(tmp_path):
    path = tmp_path / "m1"
    path.mkdir()
    (path / "registry.json").write_bytes(RAW)
    return path


def fixture_validator(raw, *, expected_module):
    assert raw == RAW
    assert expected_module == "m1"
    return {"module": "m1", "features": {}, "proposals": {}}


def prepare(directory, **overrides):
    args = dict(module_slug="m1", key="k123", name="demo", kind="keyword_filter",
                code=CODE, test_code=TEST_CODE, gap_signature="sig",
                validate_registry=fixture_validator)
    args.update(overrides)
    return preflight_proposal(directory, **args)


def snapshot(directory):
    # Capture relative entries, raw bytes and symlink targets, without following
    # fixture links. Includes directories to detect forbidden mkdir side effects.
    result = {}
    for path in directory.rglob("*"):
        relative = str(path.relative_to(directory))
        if path.is_symlink():
            result[relative] = ("symlink", str(path.readlink()))
        elif path.is_file():
            result[relative] = ("file", path.read_bytes())
        elif path.is_dir():
            result[relative] = ("directory", None)
    return result


def test_new_plan_preserves_bytes_and_does_not_create_candidates(directory):
    before = snapshot(directory)
    plan = prepare(directory)
    assert snapshot(directory) == before
    assert not (directory / "candidates").exists()
    assert plan.code_path == directory / "candidates" / "k123.py"
    assert plan.test_path == directory / "candidates" / "k123.test.py"
    assert plan.code_bytes == CODE.encode("utf-8")
    assert plan.test_bytes == TEST_CODE.encode("utf-8")
    assert plan.code_sha256 == hashlib.sha256(plan.code_bytes).hexdigest()
    assert plan.test_sha256 == hashlib.sha256(plan.test_bytes).hexdigest()
    assert plan.registry_sha256 == hashlib.sha256(RAW).hexdigest()


def test_existing_plain_candidates_directory_is_not_changed(directory):
    (directory / "candidates").mkdir()
    before = snapshot(directory)
    prepare(directory)
    assert snapshot(directory) == before


@pytest.mark.parametrize("raw", [b'{', b'{"module":"m1","module":"other"}',
                                 b'{"score":NaN}', b'[]', b'\xff'])
def test_registry_boundary_exception_propagates_before_mutation(directory, raw):
    class BoundaryRefusal(ValueError):
        pass

    (directory / "registry.json").write_bytes(raw)
    before = snapshot(directory)
    sentinel = BoundaryRefusal("fixture SC-J02 refusal")

    def reject(actual, *, expected_module):
        assert actual == raw
        assert expected_module == "m1"
        raise sentinel

    with pytest.raises(BoundaryRefusal) as caught:
        prepare(directory, validate_registry=reject)
    assert caught.value is sentinel
    assert snapshot(directory) == before


@pytest.mark.parametrize("key", ["", ".", "..", "../escape", "/tmp/escape",
                                "a/b", "a\\b", "a.test", "x\x00"])
def test_unsafe_key_refuses_before_mutation(directory, key):
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="unsafe key"):
        prepare(directory, key=key)
    assert snapshot(directory) == before


@pytest.mark.parametrize("name", ["../escape", "x.y"])
def test_unsafe_name_refuses_before_mutation(directory, name):
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="unsafe name"):
        prepare(directory, name=name)
    assert snapshot(directory) == before


@pytest.mark.parametrize("slug", ["../m1", "m/1", ""])
def test_unsafe_module_identity_refuses(directory, slug):
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="unsafe module_slug"):
        prepare(directory, module_slug=slug)
    assert snapshot(directory) == before


@pytest.mark.parametrize("kind", [""])
def test_unsupported_kind_refuses(directory, kind):
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="unsupported kind"):
        prepare(directory, kind=kind)
    assert snapshot(directory) == before


@pytest.mark.parametrize("field", ["key", "name", "kind", "module_slug", "code",
                                   "test_code", "gap_signature"])
def test_string_subclass_refused_without_conversion_hooks(directory, field):
    class Hostile(str):
        def encode(self, *args, **kwargs):
            raise AssertionError("must not encode subclass")

        def __str__(self):
            raise AssertionError("must not convert subclass")

    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="exact string"):
        prepare(directory, **{field: Hostile("demo")})
    assert snapshot(directory) == before


@pytest.mark.parametrize("field", ["code", "test_code"])
def test_surrogate_source_refuses_before_mutation(directory, field):
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="UTF-8") as caught:
        prepare(directory, **{field: "\ud800"})
    assert isinstance(caught.value.__cause__, UnicodeEncodeError)
    assert snapshot(directory) == before


def test_empty_gap_signature_preserved_for_j02_compatibility(directory):
    before = snapshot(directory)
    plan = prepare(directory, gap_signature="")
    assert plan.gap_signature == ""
    assert snapshot(directory) == before


@pytest.mark.parametrize("status", ["proposed", "activated"])
def test_existing_key_always_refuses_and_preserves_candidate_bytes(directory, status):
    candidates = directory / "candidates"
    candidates.mkdir()
    (candidates / "k123.py").write_bytes(CODE.encode())
    (candidates / "k123.test.py").write_bytes(TEST_CODE.encode())
    before = snapshot(directory)

    def existing(raw, *, expected_module):
        assert raw == RAW
        return {"module": expected_module, "features": {}, "proposals": {"k123": {
            "status": status, "code_sha256": hashlib.sha256(CODE.encode()).hexdigest(),
            "test_sha256": hashlib.sha256(TEST_CODE.encode()).hexdigest()}}}

    with pytest.raises(ProposalPreflightError, match="already registered"):
        prepare(directory, validate_registry=existing)
    assert snapshot(directory) == before


@pytest.mark.parametrize("filename", ["k123.py", "k123.test.py"])
@pytest.mark.parametrize("entry_kind", ["file", "directory", "broken_symlink", "symlink"])
def test_unregistered_destination_refuses_even_identical_or_broken_link(
    directory, tmp_path, filename, entry_kind
):
    candidates = directory / "candidates"
    candidates.mkdir()
    path = candidates / filename
    target = tmp_path / "outside.txt"
    target.write_bytes(b"outside unchanged")
    if entry_kind == "file":
        path.write_bytes(CODE.encode() if filename == "k123.py" else TEST_CODE.encode())
    elif entry_kind == "directory":
        path.mkdir()
    else:
        path.symlink_to(target if entry_kind == "symlink" else tmp_path / "missing")
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="already exists"):
        prepare(directory)
    assert snapshot(directory) == before
    assert target.read_bytes() == b"outside unchanged"


@pytest.mark.parametrize("entry_kind", ["file", "symlink", "broken_symlink"])
def test_candidates_nonplain_directory_refuses(directory, tmp_path, entry_kind):
    path = directory / "candidates"
    outside = tmp_path / "outside"
    outside.mkdir()
    if entry_kind == "file":
        path.write_bytes(b"not a directory")
    else:
        path.symlink_to(outside if entry_kind == "symlink" else tmp_path / "missing")
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="plain directory"):
        prepare(directory)
    assert snapshot(directory) == before
    assert list(outside.iterdir()) == []


def test_registry_symlink_refuses_without_following(directory, tmp_path):
    (directory / "registry.json").unlink()
    outside = tmp_path / "outside.json"
    outside.write_bytes(RAW)
    (directory / "registry.json").symlink_to(outside)
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="plain regular"):
        prepare(directory)
    assert snapshot(directory) == before
    assert outside.read_bytes() == RAW


def test_registry_directory_refuses(directory):
    (directory / "registry.json").unlink()
    (directory / "registry.json").mkdir()
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="plain regular"):
        prepare(directory)
    assert snapshot(directory) == before


def test_missing_registry_refuses_without_initializing(directory):
    (directory / "registry.json").unlink()
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="cannot inspect"):
        prepare(directory)
    assert snapshot(directory) == before


def test_module_directory_symlink_refuses(directory, tmp_path):
    link = tmp_path / "linked-module"
    link.symlink_to(directory, target_is_directory=True)
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="plain directories"):
        prepare(link)
    assert snapshot(directory) == before


def test_ancestor_directory_symlink_refuses(directory, tmp_path):
    link = tmp_path / "linked-parent"
    link.symlink_to(directory.parent, target_is_directory=True)
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="plain directories"):
        prepare(link / directory.name)
    assert snapshot(directory) == before


@pytest.mark.parametrize("value", [[], {"module": "other", "proposals": {}},
                                  {"module": "m1", "proposals": []}])
def test_validator_postcondition_refuses_invalid_return(directory, value):
    before = snapshot(directory)
    with pytest.raises(ProposalPreflightError, match="validator returned"):
        prepare(directory, validate_registry=lambda raw, *, expected_module: value)
    assert snapshot(directory) == before


def test_validator_called_before_destination_inspection(directory, monkeypatch):
    visited = []
    original = Path.lstat
    candidates = directory / "candidates"

    def observed(path, *args, **kwargs):
        if path == candidates:
            visited.append("candidates")
        return original(path, *args, **kwargs)

    def validated(raw, *, expected_module):
        visited.append("registry-validated")
        return fixture_validator(raw, expected_module=expected_module)

    monkeypatch.setattr(Path, "lstat", observed)
    prepare(directory, validate_registry=validated)
    assert visited == ["registry-validated", "candidates"]
