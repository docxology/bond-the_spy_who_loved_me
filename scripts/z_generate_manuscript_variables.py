"""LIPARUS manuscript variable hydration (runs LAST: z_ prefix).

Thin wrapper. Computes the ``{{TOKEN}}`` map from ``manuscript/config.yaml``
plus the deterministic domain-metric runs, writes
``output/data/manuscript_variables.json``, renders the concept figures, and
writes the resolved manuscript tree to ``output/manuscript/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from the_spy_who_loved_me.figures import build_all_figures  # noqa: E402
from the_spy_who_loved_me.manuscript_variables import (  # noqa: E402
    generate_variables,
    resolve_manuscript_tree,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LIPARUS manuscript variable hydration")
    parser.add_argument("--allow-draft", action="store_true", help="skip strict output gate")
    parser.add_argument("--skip-figures", action="store_true", help="do not render figures")
    args = parser.parse_args(argv)

    variables = generate_variables(require_outputs=not args.allow_draft)
    data_dir = PROJECT_ROOT / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "manuscript_variables.json").write_text(
        json.dumps(variables, indent=2, sort_keys=True), encoding="utf-8"
    )

    if not args.skip_figures:
        built = build_all_figures()
        print("\n".join(f"{k}: {v}" for k, v in built.items()))

    output_dir, resolved = resolve_manuscript_tree(variables, strict=not args.allow_draft)
    print(f"resolved {len(resolved)} manuscript sections -> {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
