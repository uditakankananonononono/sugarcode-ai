# Row229 Stochastic Gradient Descent

Exact description: "Scales to large data".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Actual one-pass mini-batch SGD linear-regression trainer accepts a lazy batch
iterator, validates and processes one batch at a time, never prefetches beyond
declared batch budget or materializes whole data. Update uses mean residual
feature gradient, rate divided by max(1,mean squared feature norm). This trace
normalization bounds the quadratic batch Lipschitz constant and stabilizes
batch-local descent; changing batch order can change training. No automatic
intercept, feature one may supply it. New native Sugarcode standalone files; namespace imports, no __init__.py.

Caps1..8weights,1..100batches,1..128samples per batch,features/targets/initial
within+-1000,rate(0,1]. Per-batch schema/numeric validation before calculation.
Training is local and input mutation-free. Output stores bounded per-batch
summaries, not raw data. At budget boundary no extra read: exhaustion is unknown,
not falsely called complete. Memory independent of total source stream length;
work/traces are bounded for this call. Caller should resume weights for later
calls; no persistence or multi-call scheduling implemented here.

12 pytest cases include300 independent Decimal minibatch sequences, asymmetric hand
mean gradient/loss values, stream sentinel preventing overread, all cap/type/
schema/refusal stages, signed numeric bounds, zero features and max batch menu.
BroadAST49/49 own arithmetic/comparison/integer-constant/boolean/any-all mutants
killed. Numerical-fault injection pins a defensive finite-weight guard only.

SCOPED bounded streaming data trainer, literalPARTIAL. NOT_CLAIMED: authentic,
IID/shuffled data, full-stream convergence or generalization, throughput scale
benchmark, real decision, external effects, runtime/persistence integration.
Features/target must have compatible units; scaling affects updates. No purchase
or communication. Independent audit still required.

Pre-delivery numeric correction: huge +/-10**400 values refused at learning rate,
initial weights, features and target before isfinite/float conversion. 12
final pytest cases. Re-ran all49AST mutants after correction,49killed.

Native port fresh49AST49kills. Source reviewed, no Atlas runtime-placement
claim carried over. No throughput benchmark established by bounded streaming.
