"""LIPARUS figure generation CLI.

Thin wrapper around :func:`the_spy_who_loved_me.figures.build_all_figures`;
renders the five concept figures to ``output/figures/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from the_spy_who_loved_me.figures import build_all_figures  # noqa: E402


def main() -> int:
    built = build_all_figures()
    for name, path in built.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
