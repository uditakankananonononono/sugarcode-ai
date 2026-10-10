"""H28 characterization: a vendor ProviderUnavailable raised by provider.available() is not contained.

AUTHORED BY READING ONLY, NOT RUN. Pins CURRENT behavior. Not a defect claim, not a fix.
Source read at a29dddd5: instinct_models/router.py 71-78 (available() is called outside the try that
catches the vendor ProviderError), llm/shared.py 103-123 (router.run has no try), cli.py _cmd_shared
(catches only sugarcode.llm.providers.ProviderError).
Case (b) (chat raising vendor ProviderError) is already pinned by tests/test_h10_shared_boundary.py
test_real_router_error_attempt_is_withheld, so it is not repeated here.
"""
import pytest

from instinct_models import Router, Task
from instinct_models.providers import LOCAL
from instinct_models.providers import ProviderError as VendorProviderError
from instinct_models.providers import ProviderUnavailable as VendorProviderUnavailable
from sugarcode.cli import main
from sugarcode.llm import shared
from sugarcode.llm.providers import ProviderError as LocalProviderError

Q = "design a CRISPR guide for TP53"


class _RaisingAvailable:
    name = "stub-raises-in-available"
    locality = LOCAL

    def available(self):
        raise VendorProviderUnavailable("stub: not available")

    def chat(self, messages, *, tools=None, max_tokens=1024):
        raise AssertionError("chat must not be reached when available() raises")


def test_the_two_provider_error_classes_are_unrelated():
    assert not issubclass(VendorProviderError, LocalProviderError)
    assert not issubclass(VendorProviderUnavailable, LocalProviderError)
    assert issubclass(VendorProviderUnavailable, VendorProviderError)


def test_router_run_does_not_contain_available_raising_vendor_unavailable():
    r = Router([_RaisingAvailable()])
    with pytest.raises(VendorProviderUnavailable):
        r.run(Task(messages=[{"role": "user", "content": Q}], tools=[]))


def test_shared_ask_propagates_it_and_it_is_not_the_local_provider_error():
    with pytest.raises(VendorProviderUnavailable) as ei:
        shared.shared_ask(Q, router=Router([_RaisingAvailable()]))
    assert not isinstance(ei.value, LocalProviderError)


def test_cli_shared_ask_does_not_catch_it(monkeypatch, capsys):
    monkeypatch.setattr(shared.Router, "from_config", classmethod(lambda cls, cfg: Router([_RaisingAvailable()])))
    with pytest.raises(VendorProviderUnavailable):
        main(["shared", "ask", Q])
