"""Gates that bind the package's documentation to the package.

Every assertion in this file exists because a prose claim in this tree was
found to be false while every test was green. Each one names the claim it
guards and is written so that restoring the false state turns it red:

* ``TestVersionIsDeclaredOnce`` — the version was restated in six places with
  nothing checking them against each other.
* ``TestLayerContract`` — ``manuscript/layer_contract.yaml`` was billed as a
  "machine-readable statement of which module may import what" and no script,
  test or gate read it. Now one does.
* ``TestFigureRegistries`` — ``experiment_plan.yaml`` and
  ``domain_profile.yaml`` listed three figures while the manuscript embedded
  and the code produced five.
* ``TestNoFabricatedPublicationIdentity`` — ``STANDALONE.md`` asserted a
  GitHub repo, two Zenodo DOIs, a PyPI release and five more locations, none
  of which exist.
* ``TestNoExemplarBoilerplate`` — the same file was un-rewritten scaffold text
  for an optimizer project, which the documented ``rg template_code_project``
  lineage check could not see because the boilerplate never used that string.
* ``TestDocsAgreeWithTheRun`` — ``AGENTS.md`` hardcoded scenario numbers that
  the manuscript deliberately tokenises, so a ``scenario.py`` edit would
  silently falsify it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import tomllib
import yaml

from the_spy_who_loved_me.figures import build_all_figures
from the_spy_who_loved_me.mission import PACKAGE_VERSION
from the_spy_who_loved_me.scenario import run_canonical
from the_spy_who_loved_me.tanker_capture import _PHASE_DURATIONS

PACKAGE_ROOT = Path(__file__).resolve().parents[1]

#: Directories that hold generated, vendored or VCS content — never scanned.
_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "output",
}
#: Generated blobs that are not authored documentation.
_EXCLUDED_FILES = {"uv.lock", ".template-export.json"}
_DOC_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".cff", ".toml"}


def _documentation_files() -> list[Path]:
    """Every authored documentation/metadata file in the package."""
    found: list[Path] = []
    for path in PACKAGE_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in _DOC_SUFFIXES:
            continue
        if path.name in _EXCLUDED_FILES:
            continue
        if any(part in _EXCLUDED_DIRS for part in path.relative_to(PACKAGE_ROOT).parts):
            continue
        found.append(path)
    return sorted(found)


def _grep(patterns: dict[str, str]) -> dict[str, list[str]]:
    """Map each pattern label to the ``path:line`` hits across the docs."""
    files = _documentation_files()
    assert len(files) >= 20, f"documentation scan set is too small: {len(files)}"
    hits: dict[str, list[str]] = {}
    for label, pattern in patterns.items():
        rx = re.compile(pattern, re.IGNORECASE)
        for path in files:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if rx.search(line):
                    hits.setdefault(label, []).append(f"{path.relative_to(PACKAGE_ROOT)}:{number}")
    return hits


class TestDocumentationScanSetIsReal:
    """The scan set must be non-empty and must contain the known offenders' files.

    A file-set gate whose glob silently matches nothing passes forever. This
    pins that the scan actually reaches the documents the other gates are
    about.
    """

    def test_scan_reaches_the_key_documents(self) -> None:
        names = {p.relative_to(PACKAGE_ROOT).as_posix() for p in _documentation_files()}
        for required in (
            "STANDALONE.md",
            "AGENTS.md",
            "README.md",
            "TODO.md",
            "docs/README.md",
            "experiment_plan.yaml",
            "domain_profile.yaml",
            "manuscript/layer_contract.yaml",
            ".agents/skills/the-spy-who-loved-me/SKILL.md",
        ):
            assert required in names, f"{required} is not in the documentation scan set"

    def test_the_scanner_can_find_something(self) -> None:
        """A positive control: a string that is definitely present is found."""
        assert _grep({"codename": r"\bLIPARUS\b"})["codename"]


class TestVersionIsDeclaredOnce:
    """One version, ten declaration sites, now cross-checked.

    ``pyproject.toml`` is the authority. Everything else mirrors it, and
    ``manuscript/06_reproducibility.md`` presents ``mission.PACKAGE_VERSION``
    and the ``{{LIPARUS_VERSION}}`` token (which comes from
    ``manuscript/config.yaml``) as the same figure — so they must be.
    """

    def _authoritative(self) -> str:
        with open(PACKAGE_ROOT / "pyproject.toml", "rb") as handle:
            version = tomllib.load(handle)["project"]["version"]
        assert isinstance(version, str) and version
        return version

    def test_every_declaration_site_agrees(self) -> None:
        expected = self._authoritative()
        config = yaml.safe_load((PACKAGE_ROOT / "manuscript" / "config.yaml").read_text())
        codemeta = json.loads((PACKAGE_ROOT / "codemeta.json").read_text())
        zenodo = json.loads((PACKAGE_ROOT / ".zenodo.json").read_text())
        citation = yaml.safe_load((PACKAGE_ROOT / "CITATION.cff").read_text())
        example = yaml.safe_load((PACKAGE_ROOT / "manuscript" / "config.yaml.example").read_text())
        skill = (PACKAGE_ROOT / ".agents/skills/the-spy-who-loved-me/SKILL.md").read_text()
        m_agents = (PACKAGE_ROOT / "manuscript" / "AGENTS.md").read_text()

        def _frontmatter_version(text: str) -> str:
            # A frontmatter ``version`` line, quoted or bare. Split on the
            # first colon and strip whitespace, quotes and commas rather than
            # regex-quoting a quote character.
            for line in text.splitlines():
                line = line.strip()
                if not line.startswith("version:"):
                    continue
                value = line.split(":", 1)[1].strip().strip("\"' ,")
                parts = value.split(".")
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    return value
            raise AssertionError("no frontmatter version found")

        declared = {
            "pyproject.toml [project] version": expected,
            "mission.PACKAGE_VERSION": PACKAGE_VERSION,
            "manuscript/config.yaml paper.version": str(config["paper"]["version"]),
            "manuscript/config.yaml mission.package_version": str(
                config["mission"]["package_version"]
            ),
            "codemeta.json version": str(codemeta["version"]),
            ".zenodo.json version": str(zenodo["version"]),
            "CITATION.cff version": str(citation["version"]),
            "manuscript/config.yaml.example paper.version": str(example["paper"]["version"]),
            ".agents/.../SKILL.md version": _frontmatter_version(skill),
            "manuscript/AGENTS.md version": _frontmatter_version(m_agents),
        }
        assert len(declared) >= 9
        disagreeing = {k: v for k, v in declared.items() if v != expected}
        assert not disagreeing, f"version drift against {expected}: {disagreeing}"


class TestLayerContract:
    """``manuscript/layer_contract.yaml`` is now read by something.

    It declares which modules are pure domain core (no ``bond_api``, no
    template ``infrastructure``), which single module may adapt the protocol,
    and which files are thin scripts. Before this class, that was prose with
    a ``.yaml`` extension.
    """

    def _contract(self) -> dict[str, list[str]]:
        data = yaml.safe_load((PACKAGE_ROOT / "manuscript" / "layer_contract.yaml").read_text())
        assert isinstance(data, dict) and data
        return data

    def test_every_listed_path_exists(self) -> None:
        contract = self._contract()
        missing = [
            rel
            for paths in contract.values()
            for rel in paths
            if not (PACKAGE_ROOT / rel).is_file()
        ]
        assert not missing, f"layer contract names files that do not exist: {missing}"

    def test_every_source_file_is_covered(self) -> None:
        """No module may sit outside the contract."""
        contract = self._contract()
        listed = {rel for paths in contract.values() for rel in paths}
        on_disk = {
            p.relative_to(PACKAGE_ROOT).as_posix()
            for p in [
                *(PACKAGE_ROOT / "src").rglob("*.py"),
                *(PACKAGE_ROOT / "scripts").rglob("*.py"),
            ]
            if "__pycache__" not in p.parts and p.name != "__init__.py"
        }
        assert on_disk, "no source files found — the scan is broken, not the contract"
        assert not (on_disk - listed), f"modules outside the layer contract: {on_disk - listed}"

    def test_pure_core_imports_neither_protocol_nor_infrastructure(self) -> None:
        contract = self._contract()
        offenders: dict[str, list[str]] = {}
        forbidden = re.compile(r"^\s*(?:from|import)\s+(bond_api|infrastructure)\b", re.MULTILINE)
        for rel in contract["pure_domain_core"]:
            found = forbidden.findall((PACKAGE_ROOT / rel).read_text(encoding="utf-8"))
            if found:
                offenders[rel] = found
        assert not offenders, f"pure domain core is not pure: {offenders}"

    def test_only_the_adapter_imports_bond_api(self) -> None:
        contract = self._contract()
        allowed = set(contract["protocol_adapter"]) | set(contract["thin_scripts"])
        importers = set()
        pattern = re.compile(r"^\s*(?:from|import)\s+bond_api\b", re.MULTILINE)
        for path in (PACKAGE_ROOT / "src").rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            if pattern.search(path.read_text(encoding="utf-8")):
                importers.add(path.relative_to(PACKAGE_ROOT).as_posix())
        assert importers, "expected at least the adapter to import bond_api"
        assert importers <= allowed, f"unexpected bond_api importers: {importers - allowed}"

    def test_nothing_anywhere_imports_infrastructure(self) -> None:
        pattern = re.compile(r"^\s*(?:from|import)\s+infrastructure\b", re.MULTILINE)
        offenders = [
            p.relative_to(PACKAGE_ROOT).as_posix()
            for p in PACKAGE_ROOT.rglob("*.py")
            if not any(part in _EXCLUDED_DIRS for part in p.relative_to(PACKAGE_ROOT).parts)
            and pattern.search(p.read_text(encoding="utf-8"))
        ]
        assert not offenders, f"template infrastructure imported by: {offenders}"


class TestFigureRegistries:
    """The declared figure set must be the figure set that is produced."""

    def _built(self) -> set[str]:
        return set(build_all_figures())

    def test_experiment_plan_lists_every_figure(self) -> None:
        plan = yaml.safe_load((PACKAGE_ROOT / "experiment_plan.yaml").read_text())
        declared = {name.removeprefix("fig:") for name in plan["expected_figures"]}
        assert declared == self._built(), (
            f"experiment_plan.yaml expected_figures drift: "
            f"missing {self._built() - declared}, extra {declared - self._built()}"
        )

    def test_domain_profile_lists_every_figure(self) -> None:
        profile = yaml.safe_load((PACKAGE_ROOT / "domain_profile.yaml").read_text())
        assert set(profile["figure_types"]) == self._built()

    def test_domain_profile_artifacts_cover_every_figure(self) -> None:
        profile = yaml.safe_load((PACKAGE_ROOT / "domain_profile.yaml").read_text())
        declared = {
            Path(item).stem for item in profile["artifact_expectations"] if item.endswith(".png")
        }
        assert declared == self._built()

    def test_every_manuscript_figure_reference_is_produced(self) -> None:
        """Prose may only point at a figure the code renders."""
        referenced = set()
        for section in sorted((PACKAGE_ROOT / "manuscript").glob("[0-9][0-9]_*.md")):
            text = section.read_text(encoding="utf-8")
            referenced |= set(re.findall(r"output/figures/([a-z_]+)\.png", text))
        assert referenced, "no figure references found in the manuscript"
        assert referenced <= self._built(), (
            f"unproduced figures cited: {referenced - self._built()}"
        )


class TestNoFabricatedPublicationIdentity:
    """No document may assert a publication location this package lacks.

    ``STANDALONE.md`` carried a generated index claiming
    ``github.com/docxology/the_spy_who_loved_me`` (404; this package's own
    repository, ``github.com/docxology/bond-the_spy_who_loved_me``, does exist
    and naming it is legal), Zenodo concept DOI
    ``10.5281/zenodo.20417136``, version DOI ``10.5281/zenodo.20931934``,
    Test PyPI ``the-spy-who-loved-me 2.5.2``, plus HuggingFace, IPFS, OSF,
    Netlify and Software Heritage locations. The tree has no DOI and no
    registry or archive identity, so every one of them was fabricated.

    The patterns below are identifiers and URLs, not the plain words — prose
    that *denies* a DOI ("no DOI, reserved or deposited") must stay legal. The
    package's own repository URL is the one location it does have, so
    ``github_repo`` excludes it and still catches every other location.
    """

    FABRICATED = {
        "zenodo_doi": r"10\.5281/zenodo",
        "zenodo_record": r"zenodo\.org/record",
        "pypi": r"pypi\.org/project",
        "huggingface": r"huggingface\.co/",
        "ipfs": r"gateway\.pinata\.cloud|/ipfs/Qm",
        "osf": r"osf\.io/",
        "netlify": r"\.netlify\.app",
        "software_heritage": r"archive\.softwareheritage\.org",
        "github_pages": r"docxology\.github\.io",
        "github_repo": r"github\.com/docxology/(?!bond-the_spy_who_loved_me(?:\.git)?(?:[^\w.-]|$))",
        "publication_index_block": r"BEGIN:PUBLICATION_INDEX",
    }

    def test_no_document_claims_a_publication_location(self) -> None:
        hits = _grep(self.FABRICATED)
        assert not hits, f"fabricated publication identity: {hits}"

    def test_the_package_names_its_own_repository(self) -> None:
        """The documents name the one location this package really has."""
        hits = _grep({"own_repo": r"github\.com/docxology/bond-the_spy_who_loved_me"})
        assert hits, "no document names the package's own repository"

    def test_config_still_records_the_honest_position(self) -> None:
        config = (PACKAGE_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8")
        assert "only git remote is this package's own repository" in config
        assert "No DOI has been minted" in config


class TestNoExemplarBoilerplate:
    """Scaffold text from the template exemplar must not survive in prose.

    The documented lineage check was ``rg -n "template[_]code_project"``,
    which could not see the actual boilerplate: ``STANDALONE.md`` described an
    *optimizer* project (``scripts/optimization_analysis.py``,
    ``output/data/optimization_results.csv``, "Replace the optimizer") and
    spelled the exemplar path ``templates/the_spy_who_loved_me``, so the gate
    matched nothing it needed to. ``.agents/.../SKILL.md`` billed the package
    as a "gradient descent, convergence analysis" exemplar.

    These patterns are the boilerplate itself, not one spelling of its name.
    """

    BOILERPLATE = {
        "template_lineage_token": r"template_code_project",
        "optimizer_script": r"optimization_analysis",
        "optimizer_results": r"optimization_results",
        "replace_the_optimizer": r"[Rr]eplace the optimizer",
        "copy_exemplar_helper": r"copy_exemplar",
        "gradient_descent": r"gradient descent",
        "template_pipeline_stage": r"scripts/pipeline/stage_\d\d_",
        "canonical_exemplar_claim": r"canonical code-driven research exemplar",
        "shared_infrastructure_claim": r"intentionally use shared template\s+infrastructure",
    }

    def test_no_boilerplate_remains(self) -> None:
        hits = _grep(self.BOILERPLATE)
        assert not hits, f"exemplar boilerplate still in the tree: {hits}"


class TestDocsAgreeWithTheRun:
    """Numbers hardcoded in prose must equal the numbers the code produces.

    ``AGENTS.md``'s "Known modelling caveats" states the beamformer scan grid
    and the canonical true bearing as literals, in a package whose whole
    manuscript protocol exists so that numbers are not literals. Keeping the
    literals is fine — leaving them unbound was not.
    """

    def test_agents_md_scan_grid_and_bearing_match_the_scenario(self) -> None:
        text = (PACKAGE_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        metrics = run_canonical()

        grid = re.search(r"([\d.]+)-degree\s+scan\s+grid", text)
        assert grid, "AGENTS.md no longer states a scan grid — update this gate"
        assert float(grid.group(1)) == pytest.approx(float(metrics["beam_scan_step_deg"]))

        bearing = re.search(r"true bearing \(([\d.]+)\s+degrees\)", text)
        assert bearing, "AGENTS.md no longer states a true bearing — update this gate"
        assert float(bearing.group(1)) == pytest.approx(float(metrics["beam_true_bearing_deg"]))

    def test_claim_ledger_sources_exist(self) -> None:
        """Every claim in ``data/claim_ledger.yaml`` must name a real file."""
        ledger = yaml.safe_load((PACKAGE_ROOT / "data" / "claim_ledger.yaml").read_text())
        claims = ledger["claims"]
        assert claims
        missing = []
        for claim in claims:
            source_file = str(claim["source"]).split()[0]
            if not (PACKAGE_ROOT / source_file).is_file():
                missing.append(f"{claim['claim_id']} -> {source_file}")
        assert not missing, f"claim ledger points at absent files: {missing}"

    def test_claim_ledger_symbols_exist(self) -> None:
        """And must name a symbol that is actually in that file."""
        ledger = yaml.safe_load((PACKAGE_ROOT / "data" / "claim_ledger.yaml").read_text())
        missing = []
        for claim in ledger["claims"]:
            parts = str(claim["source"]).split()
            source_file, symbols = parts[0], parts[1:]
            text = (PACKAGE_ROOT / source_file).read_text(encoding="utf-8")
            for symbol in symbols:
                token = symbol.split(".")[-1]
                if token.isidentifier() and token not in text:
                    missing.append(f"{claim['claim_id']} -> {symbol}")
        assert not missing, f"claim ledger names absent symbols: {missing}"

    #: claim_id -> a callable resolving the ledger's reported ``value``
    #: against the live canonical run (or the declared schedule).
    #:
    #: This implements V2: the ledger's numbers were never checked against the
    #: code, so ``scenario.py`` could change ``clearance_m`` from 1.5 and the
    #: ledger would still say 1.5 with the whole suite green.
    _LEDGER_VALUE_RESOLVERS = {
        "pfa-controlled": lambda c: c["detection_p_fa"],
        "capture-clearance": lambda c: c["tanker_clearance_m"],
        "liparus-hold-length": lambda c: c["tanker_hold_length_m"],
        # declared_constant: the sum of the per-phase schedule, not a metric.
        "capture-elapsed-time": lambda c: sum(_PHASE_DURATIONS.values()),
    }

    def test_claim_ledger_values_match_the_run(self) -> None:
        """Every numeric ledger ``value`` must equal the live metric or source."""
        import math

        ledger = yaml.safe_load((PACKAGE_ROOT / "data" / "claim_ledger.yaml").read_text())
        metrics = run_canonical()
        disagreements = []
        for claim in ledger["claims"]:
            claim_id, value = claim["claim_id"], claim.get("value")
            if value in ("generated", None):  # not a static claim; skip
                continue
            resolver = self._LEDGER_VALUE_RESOLVERS.get(claim_id)
            assert resolver is not None, (
                f"no resolver for ledger claim {claim_id} — extend _LEDGER_VALUE_RESOLVERS"
            )
            live = resolver(metrics)
            if not math.isclose(float(value), float(live), abs_tol=1e-6):
                disagreements.append(f"{claim_id}: ledger {value} vs live {live}")
        assert not disagreements, f"claim ledger values drifted from the run: {disagreements}"
