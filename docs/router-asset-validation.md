# Router asset validation

Existing Router.load checks NPZ field set, nonempty unique Unicode text axes,
matching vocab/IDF/weights/bias/label shapes, finite numeric values and positive
IDF before building a router. allow_pickle=False remains. Real shipped weights
still route questions through the existing product model; no algorithm changed.

This validates shape/content only, not authenticity, model quality, source
licensing, accuracy or a safe NPZ resource boundary. NPZ decompression/read size
is not capped. Structurally valid malicious weights can still pass. This is
not a model evaluation result or provider acceptance claim.
