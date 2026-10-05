"""Shared pytest setup for the Berbel test suite.

Hack search path to have plain import statements work for both the
custom_components, as well as the berbel_ble bits.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

for path in (REPO_ROOT, REPO_ROOT / "custom_components" / "berbel"):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
