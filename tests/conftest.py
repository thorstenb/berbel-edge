"""Shared pytest setup for the Berbel test suite.

Hack search path to have plain import statements work for both the
custom_components, as well as the berbel_ble bits.
"""

import asyncio
import sys
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

for path in (REPO_ROOT, REPO_ROOT / "custom_components" / "berbel"):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

_sync_test_loop: asyncio.AbstractEventLoop | None = None


def pytest_runtest_setup(item):
    """Give every test an actual event loop.

    The Home Assistant test plugin has autouse fixtures that call the
    function asyncio.get_event_loop. For a plain synchronous test,
    that call bails once an asynchronous test has run earlier, leading
    to a missing event loop. Thus, set one explicitely.

    """
    global _sync_test_loop
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            asyncio.get_event_loop()
            return
        except RuntimeError:
            pass
    if _sync_test_loop is None or _sync_test_loop.is_closed():
        _sync_test_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_sync_test_loop)


def pytest_sessionfinish(session, exitstatus):
    """Close the event loop that pytest_runtest_setup created, if any."""
    if _sync_test_loop is not None and not _sync_test_loop.is_closed():
        _sync_test_loop.close()
