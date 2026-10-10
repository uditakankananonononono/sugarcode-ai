# Isolated child stdout strict result protocol

Base35998c7. Superseding peer PREP f10607fe retained; earlier v1 not used.
Parent dispatch now calls decode_child_result on stdout after its existing
1,048,576-byte cap (reads one extra byte) and successful child exit. Child
launcher remains unchanged. Strict UTF-8 only, no BOM/alternate encoding; one
object with exact sole key result, no duplicate decoded keys at any depth,
nonfinite constants/float overflow, lone surrogate or malformed/deep JSON.
ResultProtocolError is ValueError subclass with reason code. Exact bytes or
bytearray input, positive exact-int config limits. Default depth64 with wrapper
root depth0, same counting convention as snapshot_json. This is a stricter
protocol compatibility change, not validation of arbitrary scientific result.

Peer proposed max_int_digits64 WITHOUT traffic evidence. Integrator did NOT
adopt arbitrary64-digit default: default None preserves interpreter integer
conversion limit, converting its ValueError to int_overflow. Explicit optional
positive max_int_digits remains. Tested100-digit legitimate integer accepted;
no corpus-wide large-integer compatibility assertion. Budget is byte cap plus
postdecode depth, not universal CPU/memory/resource isolation or value-count cap.

No finite-result quality/schema/authenticity or effect permission claim. Child
can output arbitrary well-formed finite data. Legacy in-process dispatch, input
encoding and gate/registry race policies unchanged. Parser resource failures
MemoryError/IO failures are not universally typed. Real containment remains
an independent capability; fixture refuses unavailable containment rather than
calling decoder-only tests sandbox proof.

Builder: peer codec authored file40 pytest cases actually PASS, existing dispatch7
cases PASS, plus11 new limit/large-integer/hostile-child cases PASS. Full selected
codec+self_improve+shared-layer+router-assets249 PASS/no skips on35998c7 base
(198 prior +40codec +11integration). Six integration probes execute actual isolated
child code writing adversarial stdout directly and exiting0, bypassing launcher:
NaN/duplicate result/nested duplicate/1e999/BOM/lone-surrogate all refused. This
reproduces the dispatch boundary here, not a universal production containment
claim. Independent verdict required. No in-flight F01/ledger changes included.

Independent verdict relayed2026-10-10: VERIFIED parent-stdout boundary; SCOPED
residue. Verifier reproduced249 PASS/no skips, including actual six hostile-child
cases and extra decode probes. Default integer bound remains interpreter-dependent:
older interpreters without conversion limit can parse roughly1MiB of digits with
quadratic cost, bounded only by read cap, NOT refused early by this decoder.
Full1MiB is read then decoded; timeouts/IO/MemoryError remain outside typed codec
errors. str input refused intentionally. Depth-root0 correspondence is documented,
not an independently derived cross-module schema equivalence claim.
