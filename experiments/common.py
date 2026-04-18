"""Shared helpers for experiment entry points."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
VENDOR = ROOT / ".vendor"


def bootstrap_pythonpath() -> None:
    """Ensure the project source tree is importable."""

    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
    vendor_str = str(VENDOR)
    if VENDOR.exists() and vendor_str not in sys.path:
        # Append vendor packages after the standard library so stdlib modules
        # (for example dataclasses on Python 3.13) are not shadowed by backports.
        sys.path.append(vendor_str)
