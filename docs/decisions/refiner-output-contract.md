# Validate optional refiner output after calling the hook

Current main checks the unrefined plan, then returns arbitrary refiner output.
A normally constructed invalid FeaturePlan rejects in its constructor, masking
this missing post-hook check in the existing test. A mutated frozen plan or
wrong return type bypasses that test's guard.

Contract follows ProposalRefiner's existing description: the hook may change
description and parameters, not module identity, gap identity, name or kind.
Return must be an exact FeaturePlan. Re-run its name/kind validation after the
hook and compare identity to an immutable pre-hook tuple. Hook exceptions still
propagate. Invalid output does not reach synthesis or proposal in run_cycle.

Limits: the hook executes as trusted Python before this validation. This is not
an untrusted-code sandbox, network policy or parameter semantic validation.
Frozen dataclasses are not a security mechanism. Description/parameters remain
caller-provided values and this candidate does not validate all their domains.
No automatic model-backed planning or scientific acceptance is claimed.
