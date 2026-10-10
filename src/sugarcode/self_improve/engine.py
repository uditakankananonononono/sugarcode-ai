"""The per-module self-improvement engine.

Autonomous loop: record gaps -> detect recurring ones -> plan a feature ->
synthesize real code and tests -> sandbox-test it -> request human approval
-> (on approval) activate into the module's own feature registry. Every
stage is recorded to an append-only ledger.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .approval_schema import (ActivationExpectation, RollbackExpectation,
                              ApprovalSchemaError, require_approved)
from .approval_binding import validate_rollback_binding, ApprovalBindingError
from .source_admission import admit_candidate_text, PRODUCTION_SOURCE_LIMITS
from .codegen import synthesize_code
from .detector import CapabilityGap, GapDetector
from .events import GapEvent, GapEventStore
from .evidence import GapObservation, preview_evidence
from .capped_readers import InputLimitExceeded, JSONL_FILE_BYTES, JSONL_LINE_BYTES
from .jsonl_store import append_jsonl, read_jsonl
from .json_values import snapshot_json
from .gate import APPROVED, ApprovalGate, ManualApprovalGate
from .plans import Candidate, FeaturePlan
from .planner import FeaturePlanner
from .registry import FeatureRegistry
from .sandbox import SandboxResult, SandboxRunner
from .testsynth import synthesize_tests

_KIND_SAMPLES: dict[str, list] = {
    "keyword_filter": ["grant for phd students in biology", "unrelated notice",
                       {"title": "grant deadline"}, None, 42],
    "scoring_rule": ["grant for phd students in biology", "totally unrelated",
                     {"title": "grant"}, "grant grant grant"],
    "text_transform": ["hello   world", "many\t\n spaces   here", "", "untouched"],
    "aggregator": [{"category": "a", "value": 1}, {"category": "a", "value": 2},
                   {"category": "b", "value": 5}, "not a dict"],
    "threshold_alert": [{"value": 10}, {"value": -3}, {"value": "not-a-number"}, "junk"],
    "field_extractor": ["contact me at prof@uni.edu on 2026-09-25, score 91.5",
                        "no fields here", None, 7],
}


class CommittedEffectAuditError(RuntimeError):
    """Effect completed but its ledger append failed. Never blindly retry.

    outcome contains bounded operation metadata. result_reference, for dispatch,
    is the exact in-memory return object, not a serializable or durable receipt.
    No source/result repr, conversion or serialization is attempted here.
    """
    committed = True
    retry_safe = False

    def __init__(self, *, operation, subject, approval_id, version, outcome,
                 result_reference=None):
        super().__init__("effect completed but audit append failed; do not retry")
        self.operation = operation
        self.subject = subject
        self.approval_id = approval_id
        self.version = version
        self.outcome = outcome
        self.result_reference = result_reference


class InvalidLedgerValue(ValueError):
    """Ledger JSON is unsupported, ambiguous or bound to another module."""


def _ledger_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidLedgerValue("duplicate ledger object key")
        result[key] = value
    return result


class SelfImprovementEngine:
    def __init__(self, *, module_id: int, module_slug: str, state_dir: Path | str,
                 gate: ApprovalGate | None = None, sandbox: SandboxRunner | None = None,
                 planner: FeaturePlanner | None = None, min_occurrences: int = 2) -> None:
        self.module_id = module_id
        self.module_slug = module_slug
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.store = GapEventStore(self.state_dir / "gap-events")
        self.detector = GapDetector(self.store, min_occurrences=min_occurrences)
        self.planner = planner or FeaturePlanner()
        self.sandbox = sandbox or SandboxRunner()
        self.registry = FeatureRegistry(module_slug, self.state_dir)
        self.gate: ApprovalGate = gate or ManualApprovalGate(self.state_dir / "approvals.json")
        self._ledger_path = self.state_dir / "ledger.jsonl"
        self._candidates: dict[str, Candidate] = {}

    # -- ledger --------------------------------------------------------------
    def _log(self, event: str, **fields: Any) -> None:
        record = {"at": time.time(), "module": self.module_slug, "event": event, **fields}
        try:
            if type(record["module"]) is not str or record["module"] != self.module_slug:
                raise InvalidLedgerValue("ledger write module mismatch")
            encoded = json.dumps(snapshot_json(record), sort_keys=True, allow_nan=False)
        except (ValueError, TypeError, RecursionError) as exc:
            raise InvalidLedgerValue("invalid ledger write; no append") from exc
        output = (encoded + "\n").encode("utf-8")
        if len(output) > JSONL_LINE_BYTES:
            raise InputLimitExceeded("line", JSONL_LINE_BYTES)
        append_jsonl(self._ledger_path, output, max_file_bytes=JSONL_FILE_BYTES,
                     max_line_bytes=JSONL_LINE_BYTES, decode=self._decode_ledger)

    def ledger(self) -> list[dict[str, Any]]:
        """Validated history; may create advisory lock sidecar, not pure file read."""
        return read_jsonl(self._ledger_path, max_file_bytes=JSONL_FILE_BYTES,
                          max_line_bytes=JSONL_LINE_BYTES, decode=self._decode_ledger)

    def _decode_ledger(self, lines) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                record = snapshot_json(json.loads(line, object_pairs_hook=_ledger_object))
                if type(record) is not dict or record.get("module") != self.module_slug:
                    raise InvalidLedgerValue("invalid ledger module or record")
            except (ValueError, TypeError, KeyError, RecursionError) as exc:
                raise InvalidLedgerValue(f"invalid ledger row {number}; repair required") from exc
            records.append(record)
        return records

    def preview_gap_evidence(self, observations: list[GapObservation]) -> list[dict]:
        """Read-only experimental priority preview. Does not plan or activate."""
        return preview_evidence(self.module_slug, observations)

    # -- pipeline stages -------------------------------------------------------
    def record_gap(self, signature: str, *, kind: str = "capability_miss",
                   detail: str = "", exemplar: Any = None) -> GapEvent:
        event = GapEvent(module_slug=self.module_slug, signature=signature,
                         kind=kind, detail=detail, exemplar=exemplar)
        self.store.append(event)
        self._log("gap_event_recorded", signature=signature, kind=kind)
        return event

    def _open_gaps(self) -> list[CapabilityGap]:
        return [g for g in self.detector.detect(self.module_slug)
                if not self.registry.covers_gap(g.signature)]

    def detect_gaps(self) -> list[CapabilityGap]:
        gaps = self._open_gaps()
        for gap in gaps:
            self._log("gap_detected", signature=gap.signature,
                      occurrences=gap.occurrences, severity=gap.severity)
        return gaps

    def plan_gap(self, gap: CapabilityGap) -> FeaturePlan:
        plan = self.planner.plan(gap)
        self._log("feature_planned", name=plan.name, kind=plan.kind,
                  gap_signature=gap.signature)
        return plan

    def synthesize(self, plan: FeaturePlan) -> Candidate:
        code = synthesize_code(plan)
        sample = _KIND_SAMPLES[plan.kind]
        # Fold gap exemplars into the sample so tests exercise the real miss.
        for exemplar in self._exemplars_for(plan.gap_signature):
            sample = sample + [exemplar]
        test_code = synthesize_tests(plan, sample)
        admit_candidate_text(code, test_code, limits=PRODUCTION_SOURCE_LIMITS)
        candidate = Candidate(plan=plan, code=code, test_code=test_code)
        self._candidates[candidate.key] = candidate
        self._log("feature_synthesized", key=candidate.key, name=plan.name,
                  code_sha256=candidate.code_sha256)
        return candidate

    def _exemplars_for(self, signature: str) -> list:
        return [e.exemplar for e in self.store.all(self.module_slug)
                if e.signature == signature and e.exemplar is not None][:5]

    def evaluate(self, candidate_key: str) -> SandboxResult:
        candidate = self._candidates[candidate_key]
        admit_candidate_text(candidate.code, candidate.test_code, limits=PRODUCTION_SOURCE_LIMITS)
        result = self.sandbox.run(candidate)
        self._log("feature_evaluated", key=candidate_key, passed=result.passed,
                  exit_code=result.exit_code, timed_out=result.timed_out,
                  output_limit_exceeded=result.output_limit_exceeded,
                  output_limit_stream=result.output_limit_stream,
                  duration=result.duration_seconds)
        if not result.passed:
            self._log("feature_rejected_by_tests", key=candidate_key,
                      tail=result.stdout[-500:])
        return result

    def propose(self, candidate_key: str) -> str:
        candidate = self._candidates[candidate_key]
        self.registry.save_proposal(
            candidate_key, name=candidate.plan.name, kind=candidate.plan.kind,
            code=candidate.code, test_code=candidate.test_code,
            gap_signature=candidate.plan.gap_signature)
        approval_id = self.gate.request(
            module_id=self.module_id, module_slug=self.module_slug,
            action_type="self_improvement_activation",
            summary=f"Activate self-built feature {candidate.plan.name} "
                    f"({candidate.plan.kind}) on module {self.module_slug}",
            payload={"candidate_key": candidate_key, "name": candidate.plan.name,
                     "kind": candidate.plan.kind, "code_sha256": candidate.code_sha256,
                     "gap_signature": candidate.plan.gap_signature})
        self.registry.set_proposal_approval(candidate_key, approval_id)
        self._log("activation_proposed", key=candidate_key, approval_id=approval_id)
        return approval_id

    def activate(self, candidate_key: str, *, approval_id: str) -> dict[str, Any]:
        # Preserve mismatch refusal before looking up a forged/unknown gate ID.
        if self.registry.get_proposal(candidate_key).get("approval_id") != approval_id:
            raise PermissionError("approval id does not match this candidate's proposal")
        coordinated = getattr(self.gate, "coordinated_record", None)
        if not callable(coordinated):
            raise PermissionError("engine commit requires a full approval record and coordinated gate")
        with coordinated(approval_id) as (gate_identity, record), self.registry._lock:
            if type(gate_identity) is not str or not gate_identity:
                raise PermissionError("coordinated gate requires a stable nonempty identity")
            proposal = self.registry.get_proposal(candidate_key)
            if proposal.get("approval_id") != approval_id:
                raise PermissionError("approval id does not match this candidate's proposal")
            try:
                require_approved(record, ActivationExpectation(
                    self.module_id, self.module_slug, candidate_key, proposal["name"],
                    proposal["kind"], proposal["code_sha256"], proposal["gap_signature"]),
                    allow_unrecorded_decision=(type(self.gate) is ManualApprovalGate and self.gate._auto is True))
            except ApprovalSchemaError as exc:
                raise PermissionError("activation approval binding mismatch") from exc
            entry = self.registry.activate(candidate_key, approval_id=approval_id,
                                                   engine_gate_identity=gate_identity)
            try:
                self._log("feature_activated", key=candidate_key, name=entry["file"],
                          version=entry["version"], approval_id=approval_id)
            except Exception as exc:
                raise CommittedEffectAuditError(operation="activate", subject=candidate_key,
                    approval_id=approval_id, version=entry["version"],
                    outcome=dict(entry)) from exc
            return entry

    def rollback(self, feature_name: str, *, approval_id: str) -> dict[str, Any]:
        coordinated = getattr(self.gate, "coordinated_record", None)
        if not callable(coordinated):
            raise PermissionError("engine commit requires a full approval record and coordinated gate")
        with coordinated(approval_id) as (gate_identity, record), self.registry._lock:
            if type(gate_identity) is not str or not gate_identity:
                raise PermissionError("coordinated gate requires a stable nonempty identity")
            try:
                require_approved(record, RollbackExpectation(
                    self.module_id, self.module_slug, feature_name),
                    allow_unrecorded_decision=(type(self.gate) is ManualApprovalGate and self.gate._auto is True))
            except ApprovalSchemaError as exc:
                raise PermissionError("rollback approval binding mismatch") from exc
            pin = record.get("payload", {}).get("active_version_at_request")
            if type(pin) is not int or pin <= 0:
                raise PermissionError("rollback requires a positive active version pin")
            try:
                validate_rollback_binding(record, module_id=self.module_id,
                                          module_slug=self.module_slug, feature_name=feature_name,
                                          current_active_version=pin)
            except ApprovalBindingError as exc:
                raise PermissionError("rollback approval version binding mismatch") from exc
            outcome = self.registry.rollback(feature_name, approval_id=approval_id,
                                             expected_active_version=pin, engine_gate_identity=gate_identity)
            try:
                self._log("feature_rolled_back", **outcome)
            except Exception as exc:
                raise CommittedEffectAuditError(operation="rollback", subject=feature_name,
                    approval_id=approval_id, version=outcome["rolled_back_from"],
                    outcome=dict(outcome)) from exc
            return outcome

    def request_rollback(self, feature_name: str) -> str:
        active = self.registry._active_entry(feature_name)["version"]
        approval_id = self.gate.request(
            module_id=self.module_id, module_slug=self.module_slug,
            action_type="self_improvement_rollback",
            summary=f"Roll back self-built feature {feature_name} on {self.module_slug}",
            payload={"feature": feature_name, "active_version_at_request": active})
        self._log("rollback_proposed", feature=feature_name, approval_id=approval_id)
        return approval_id

    def dispatch(self, feature_name: str, items: list, params: dict | None = None) -> dict:
        result, version = self.registry._dispatch_with_receipt(feature_name, items, params)
        try:
            self._log("feature_dispatched", feature=feature_name, item_count=len(items))
        except Exception as exc:
            raise CommittedEffectAuditError(operation="dispatch", subject=feature_name,
                approval_id=None, version=version,
                outcome={"feature": feature_name, "version": version,
                         "result_available": True, "result_storage": "in_memory_only"},
                result_reference=result) from exc
        return result

    # -- the autonomous loop ---------------------------------------------------
    def run_cycle(self, *, max_new: int = 1) -> dict[str, Any]:
        """One autonomous improvement cycle, up to the human approval gate."""
        report: dict[str, Any] = {"module": self.module_slug, "gaps": [],
                                  "candidates": [], "proposals": [], "failed": []}
        gaps = self.detect_gaps()
        report["gaps"] = [{"signature": g.signature, "occurrences": g.occurrences,
                           "severity": g.severity} for g in gaps]
        for gap in gaps[:max_new]:
            plan = self.plan_gap(gap)
            candidate = self.synthesize(plan)
            result = self.evaluate(candidate.key)
            entry = {"key": candidate.key, "name": plan.name, "kind": plan.kind,
                     "tests_passed": result.passed}
            report["candidates"].append(entry)
            if result.passed:
                approval_id = self.propose(candidate.key)
                report["proposals"].append({"key": candidate.key, "name": plan.name,
                                            "approval_id": approval_id})
            else:
                report["failed"].append(entry)
        self._log("cycle_completed", gaps=len(gaps),
                  proposed=len(report["proposals"]), failed=len(report["failed"]))
        return report

    def status(self) -> dict[str, Any]:
        """Inspection without logging. Independent reads, not an atomic snapshot.

        Cooperating log reads may create advisory sidecars; state bytes are not
        rewritten. Invalid history still refuses rather than reporting healthy.
        """
        events = self.store.all(self.module_slug)
        registry = self.registry._load()
        ledger = self.ledger()
        covered = {
            v["gap_signature"] for feature in registry["features"].values()
            for v in feature["versions"]
        }
        covered.update(p["gap_signature"] for p in registry["proposals"].values()
                       if p["status"] in ("proposed", "activated"))
        gaps = self.detector._detect_events(self.module_slug, events)
        return {
            "module": self.module_slug,
            "gap_events": len(events),
            "open_gaps": [g.signature for g in gaps if g.signature not in covered],
            "features": registry["features"],
            "proposals": registry["proposals"],
            "ledger_events": len(ledger),
        }
