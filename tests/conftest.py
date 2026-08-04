"""LIPARUS test configuration.

Pins matplotlib to a headless backend (so figures render without a display)
and ensures the package ``src/`` is importable. No mock framework is used
anywhere in the suite — tests run the real, deterministic algorithms.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

_PKG_ROOT = Path(__file__).resolve().parents[1]
_SRC = _PKG_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
