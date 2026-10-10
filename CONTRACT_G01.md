# G01 prep: header text encoder (authored, NOT RUN, NOT WIRED)

Base: exactly 275936a916d641669bbe4ddb3afbb98b278571de. Additive new files only.
- src/sugarcode/self_improve/header_text.py
- tests/self_improve/test_prep_g01_header_text.py
- this file

Gap (read at 275936a9, nothing run): src/sugarcode/self_improve/codegen.py _HEADER lines 22-27 put
{module_slug} and {gap_signature} raw into a triple-quoted docstring; .format at line 49.
Decision as relayed by Main (peer G01 choice (a) at 1:28:16 PM, author approval relayed 1:30:09 PM IST; this file is not itself authority): encode both with json.dumps(ensure_ascii=True), one line, NO validation, no regex.

Design: encode_header_text(str)->str; render_header_fields(slug, sig)->(str,str). Any str accepted,
including Unicode and "". No refusal of any kind and no type policy: a non-str is coerced with str() before json.dumps (matches old .format: None -> "None").
Does not touch or unify events GapEventStore._path (allows ---/__) or proposal_preflight_r01._identity.

Wiring NOT done (separate integrator unit). Shape for the integrator, unapplied: in codegen._assemble pass
the two rendered values to _HEADER.format; _HEADER lines become `Module: {module_slug}` unchanged (the
value already carries its quotes). Note the written docstring then holds JSON escape text, e.g. \u00e9;
astral characters become a surrogate-pair escape pair, which Python source accepts. FEATURE meta uses
repr() and is unaffected.

Unverified: import/compile/test pass; pyproject test layout; that a JSON escape sequence in a non-raw
docstring never fails to compile for every input (reasoned: JSON emits only \" \\ \n \r \t \b \f \uXXXX).
Existing GapEvent requires a non-blank signature, so "" reaches this helper only via a directly built FeaturePlan.
