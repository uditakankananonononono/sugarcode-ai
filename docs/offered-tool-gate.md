# Offered tool dispatch gate

Copilot _run executes only names from its request's offered tool set. A model
response naming another globally cataloged tool gets an error, no dispatch.
Each response executes at most24calls; further calls get explicit errors.
Existing max_steps remains separate, not a wall-clock or resource budget.
Offered valid calls run the existing real module function.

Test uses a local model-protocol harness and actual catalog dispatch, not a
live model/provider acceptance test. This gate is not owner authorization or
isolation: tools offered may still have side effects and require appropriate
product policy. Response list/trace byte size is not capped by this change.
