"""LIPARUS mission-phase CLI: brief / recon / plan / execute / debrief / full.

Thin orchestrator. Delegates each phase to the mission provider's
corresponding method and renders the resulting protocol object to stdout as
JSON via :mod:`bond_api.serialization`. ``execute`` also writes the raw
outcome results to ``output/data/mission_outcome.json`` for provenance.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from bond_api.protocol import ReconRequest  # noqa: E402
from bond_api.serialization import to_json  # noqa: E402

from the_spy_who_loved_me.mission import PACKAGE_VERSION, MissionProvider  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_HELP = "mission phase: brief | recon | plan | execute | debrief | full"


def _print_json(obj: object) -> None:
    print(to_json(obj))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="liparus", description="LIPARUS mission CLI")
    parser.add_argument("phase", nargs="?", default="brief", help=_HELP)
    parser.add_argument("--goal", default="locate and assess the quarry", help="recon goal")
    parser.add_argument(
        "--out", default=str(PROJECT_ROOT / "output" / "data" / "mission_outcome.json")
    )
    args = parser.parse_args(argv)

    provider = MissionProvider()
    request = ReconRequest(goal=args.goal)

    if args.phase == "brief":
        _print_json(provider.brief())
    elif args.phase == "recon":
        _print_json(provider.recon(request))
    elif args.phase == "plan":
        _print_json(provider.plan(provider.brief()))
    elif args.phase == "execute":
        outcome = provider.execute(provider.plan(provider.brief()))
        _print_json(outcome)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(outcome.results, indent=2, sort_keys=True), encoding="utf-8")
    elif args.phase == "debrief":
        from bond_api.protocol import run_mission

        _print_json(run_mission(provider, request))
    elif args.phase == "full":
        _print_json(provider.brief())
        _print_json(provider.recon(request))
        _print_json(provider.plan(provider.brief()))
        outcome = provider.execute(provider.plan(provider.brief()))
        _print_json(outcome)
        _print_json(provider.debrief(outcome))
    else:
        parser.error(f"unknown phase {args.phase!r}")

    print(f"# liparus v{PACKAGE_VERSION}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
