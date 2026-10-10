"""SC-H01 pure, opt-in archive proposal. No gate imports, IO or decisions."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping


class InvalidRetentionPlan(ValueError):
    """The bounded proposal or supplied retrieval cannot preserve all records."""


@dataclass(frozen=True)
class RetentionLimits:
    # No implicit retention or capacity policy: every limit must be supplied.
    max_source_values: int
    max_source_bytes: int
    max_active_values: int
    max_active_bytes: int
    max_archive_values: int
    max_archive_bytes: int
    max_manifest_bytes: int
    max_depth: int

    def __post_init__(self) -> None:
        for value in vars(self).values():
            if type(value) is not int or value < 1:
                raise InvalidRetentionPlan("limits must be positive exact integers")
        if self.max_active_values > 10_000 or self.max_depth > 64:
            raise InvalidRetentionPlan("active limits exceed SC-J04 write boundary")


@dataclass(frozen=True)
class ArchiveArtifact:
    sha256: str
    content: bytes


@dataclass(frozen=True)
class RetentionPlan:
    active_json: bytes
    manifest_json: bytes
    archives: tuple[ArchiveArtifact, ...]


def _snapshot(value: Any, *, max_values: int, max_depth: int) -> tuple[Any, int]:
    remaining = max_values
    ancestors: set[int] = set()

    def visit(item: Any, depth: int) -> Any:
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > max_depth:
            raise InvalidRetentionPlan("value/depth budget exceeded")
        kind = type(item)
        if item is None or kind in (str, bool, int):
            return item
        if kind is float:
            if not math.isfinite(item):
                raise InvalidRetentionPlan("nonfinite number")
            return item
        # Stored JSON only. No tuple coercion or subclass conversion.
        if kind not in (dict, list):
            raise InvalidRetentionPlan("non-JSON builtin value")
        identity = id(item)
        if identity in ancestors:
            raise InvalidRetentionPlan("cyclic container")
        ancestors.add(identity)
        try:
            if kind is list:
                return [visit(child, depth + 1) for child in item]
            result = {}
            for key, child in item.items():
                if type(key) is not str:
                    raise InvalidRetentionPlan("non-string key")
                result[key] = visit(child, depth + 1)
            return result
        finally:
            ancestors.remove(identity)

    copied = visit(value, 0)
    return copied, max_values - remaining


def _encode(value: Any, max_bytes: int) -> bytes:
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("ascii")
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise InvalidRetentionPlan("cannot encode canonical JSON") from exc
    if len(encoded) > max_bytes:
        raise InvalidRetentionPlan("byte budget exceeded")
    return encoded


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _object(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise InvalidRetentionPlan("expected JSON object")
    return value


def _decode(content: bytes, max_bytes: int, max_values: int, depth: int) -> dict[str, Any]:
    if type(content) is not bytes or len(content) > max_bytes:
        raise InvalidRetentionPlan("invalid bytes or byte budget exceeded")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, child in items:
            if key in result:
                raise InvalidRetentionPlan("duplicate JSON key")
            result[key] = child
        return result

    def constant(_: str) -> Any:
        raise InvalidRetentionPlan("nonfinite JSON constant")

    try:
        value = json.loads(content, object_pairs_hook=pairs, parse_constant=constant)
        value, _ = _snapshot(value, max_values=max_values, max_depth=depth)
        value = _object(value)
        if _encode(value, max_bytes) != content:
            raise InvalidRetentionPlan("retrieval must use canonical artifact bytes")
        return value
    except (ValueError, TypeError, RecursionError, UnicodeError, OverflowError) as exc:
        raise InvalidRetentionPlan("invalid retrieved JSON") from exc


def _encode_state(value: dict[str, Any], values: int, byte_limit: int,
                  depth: int) -> tuple[bytes, int]:
    copied, count = _snapshot(value, max_values=values, max_depth=depth)
    return _encode(copied, byte_limit), count


def prepare_retention_plan(state: dict[str, Any], *, roles: dict[str, str],
                           archive_ids: tuple[str, ...], limits: RetentionLimits) -> RetentionPlan:
    """Partition an explicitly classified snapshot without dropping any record.

    roles is a caller-owned SC-J05 adapter result, not inferred authority.
    Allowed roles: pending, authority, cold_history, unknown.
    Only trusted non-authority cold_history may move.
    archive_ids is an explicit reviewed selection, never an age-based default.
    """
    _object(state)
    copied, source_values = _snapshot(state, max_values=limits.max_source_values,
                                      max_depth=limits.max_depth)
    source_json = _encode(copied, limits.max_source_bytes)
    if type(roles) is not dict:
        raise InvalidRetentionPlan("roles must be an exact dict")
    if any(type(key) is not str or type(role) is not str or
           role not in ("pending", "authority", "cold_history", "unknown")
           for key, role in roles.items()):
        raise InvalidRetentionPlan("invalid explicit role")
    if set(roles) != set(copied):
        raise InvalidRetentionPlan("roles must classify every source ID exactly")
    if type(archive_ids) is not tuple or any(type(key) is not str for key in archive_ids):
        raise InvalidRetentionPlan("archive_ids must be an exact tuple of strings")
    if len(set(archive_ids)) != len(archive_ids) or not set(archive_ids) <= set(copied):
        raise InvalidRetentionPlan("duplicate or unknown archive ID")
    selected = set(archive_ids)
    for key in selected:
        record = _object(copied[key])
        if roles[key] != "cold_history" or record.get("status") == "pending":
            raise InvalidRetentionPlan("pending, authority or unclassified record cannot move")
    active = {key: copied[key] for key in sorted(copied) if key not in selected}
    active_json, active_values = _encode_state(active, limits.max_active_values,
                                               limits.max_active_bytes, limits.max_depth)
    archives: list[ArchiveArtifact] = []
    descriptors: list[dict[str, Any]] = []

    def add_shard(shard: dict[str, Any]) -> None:
        content, count = _encode_state(shard, limits.max_archive_values,
                                       limits.max_archive_bytes, limits.max_depth)
        digest = _hash(content)
        archives.append(ArchiveArtifact(digest, content))
        descriptors.append({"sha256": digest, "bytes": len(content),
                            "values": count, "ids": sorted(shard)})

    shard: dict[str, Any] = {}
    for key in sorted(selected):
        candidate = {**shard, key: copied[key]}
        try:
            _encode_state(candidate, limits.max_archive_values,
                          limits.max_archive_bytes, limits.max_depth)
        except InvalidRetentionPlan:
            if not shard:
                raise
            add_shard(shard)
            shard = {key: copied[key]}
            # A single oversized record is refused, never split or truncated.
            _encode_state(shard, limits.max_archive_values,
                          limits.max_archive_bytes, limits.max_depth)
        else:
            shard = candidate
    if shard:
        add_shard(shard)
    manifest = {
        "format": "sc-h01-plan-v1", "source_sha256": _hash(source_json),
        "source_bytes": len(source_json), "source_values": source_values,
        "source_ids": sorted(copied), "roles": dict(sorted(roles.items())),
        "active": {"sha256": _hash(active_json), "bytes": len(active_json),
                   "values": active_values, "ids": sorted(active)},
        "archives": descriptors,
    }
    return RetentionPlan(active_json, _encode(manifest, limits.max_manifest_bytes),
                         tuple(archives))


def replay_retention_plan(*, manifest_json: bytes, active_json: bytes,
                          retrieved: Mapping[str, bytes], limits: RetentionLimits) -> dict[str, Any]:
    """Verify exact artifact bytes and reconstruct the complete source snapshot.

    Returns JSON data, not approval decisions. Hashes prove consistency with
    a trusted manifest, never authorship. No partial state on any failure.
    """
    # Manifest is bounded by bytes; each JSON value occupies at least one byte.
    manifest = _decode(manifest_json, limits.max_manifest_bytes,
                       limits.max_manifest_bytes, 64)
    try:
        if manifest["format"] != "sc-h01-plan-v1":
            raise InvalidRetentionPlan("unsupported manifest")
        active = _decode(active_json, limits.max_active_bytes,
                         limits.max_active_values, limits.max_depth)
        descriptors = manifest["archives"]
        if type(descriptors) is not list:
            raise InvalidRetentionPlan("archive descriptors must be a list")
        expected = [descriptor["sha256"] for descriptor in descriptors]
        if len(expected) != len(set(expected)) or set(retrieved) != set(expected):
            raise InvalidRetentionPlan("missing, extra or repeated archive")
        state = dict(active)
        _, aggregate_values = _snapshot(active, max_values=limits.max_source_values,
                                         max_depth=limits.max_depth)
        aggregate_bytes = len(active_json)
        for descriptor in descriptors:
            content = retrieved[descriptor["sha256"]]
            if _hash(content) != descriptor["sha256"]:
                raise InvalidRetentionPlan("archive digest mismatch")
            shard = _decode(content, limits.max_archive_bytes,
                            limits.max_archive_values, limits.max_depth)
            if set(state).intersection(shard):
                raise InvalidRetentionPlan("overlapping archive IDs")
            _, shard_values = _snapshot(shard, max_values=limits.max_archive_values,
                                         max_depth=limits.max_depth)
            aggregate_values += shard_values - 1
            aggregate_bytes += len(content) - 2 + (1 if state and shard else 0)
            if (aggregate_values > limits.max_source_values or
                    aggregate_bytes > limits.max_source_bytes):
                raise InvalidRetentionPlan("replayed source budget exceeded")
            state.update(shard)
        # Re-derive the entire manifest and partition, including role vetoes,
        # counts, IDs, canonical shard boundaries, and the source fingerprint.
        rebuilt = prepare_retention_plan(
            state, roles=manifest["roles"],
            archive_ids=tuple(key for key in state if key not in active), limits=limits)
        if rebuilt.active_json != active_json or rebuilt.manifest_json != manifest_json:
            raise InvalidRetentionPlan("manifest/source replay mismatch")
        return state
    except (KeyError, TypeError, ValueError, RecursionError, OverflowError) as exc:
        raise InvalidRetentionPlan("retrieval integrity check failed") from exc


def prepare_current_policy_plan(state: dict[str, Any], *, archive_ids: tuple[str, ...],
                                limits: RetentionLimits) -> RetentionPlan:
    """Fail-closed readiness wrapper: current eligible set is empty.

    No trusted cold-history classification grant exists. All records are unknown,
    including terminal records. This preserves every active record or fails capacity.
    Pure bytes only, no archive publication, active-state write, or relocation.
    """
    if type(archive_ids) is not tuple or archive_ids:
        raise InvalidRetentionPlan("current policy has no eligible archive IDs")
    _object(state)
    return prepare_retention_plan(state, roles={key: "unknown" for key in state},
                                  archive_ids=(), limits=limits)
