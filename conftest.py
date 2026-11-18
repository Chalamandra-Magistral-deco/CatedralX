"""Make the repo's dual import convention work for pytest from the root.

Tests use both `from elite.X...` (prefixed) and `from X...` (via elite/ on path).
scripts/verify_isolated_safety.sh already does this via PYTHONPATH; this file
reproduces it for plain `pytest`, IDE runners, and CI without the wrapper.
"""
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent
for _p in (str(_ROOT), str(_ROOT / "elite")):
    if _p not in sys.path:
        sys.path.insert(0, _p)



@pytest.fixture(autouse=True)
def _test_hormonal_signing_key(monkeypatch):
    """Provide a deterministic test-only HMAC key unless a test removes it."""
    monkeypatch.setenv(
        "CATEDRALX_HORMONAS_HMAC_KEY",
        "catedralx-test-only-hormonal-state-key-32-bytes",
    )
    monkeypatch.delenv("CATEDRALX_HORMONAS_KEYRING", raising=False)
    monkeypatch.delenv("CATEDRALX_HORMONAS_ACTIVE_KEY_ID", raising=False)
