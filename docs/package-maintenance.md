# Maintain the LIPARUS package

This checkout is `the_spy_who_loved_me` 0.1.0. The declared Python
range is `>=3.11`; [`.python-version`](../.python-version) selects
Python 3.15 for the checkout.

[`pyproject.toml`](../pyproject.toml) declares the package version and a relative
dependency on a sibling checkout named `bond-api`. The [lockfile](../uv.lock)
records the dependency layout. For version or packaging audits, distinguish
that sibling dependency from the maintained film package in this checkout.

[CITATION.cff](../CITATION.cff), [codemeta.json](../codemeta.json), and
[.zenodo.json](../.zenodo.json) carry citation and release metadata. The
repository's publication checks distinguish a metadata file from a published
record.

## Verify documentation and metadata

From this checkout, with Lychee installed, verify local Markdown links:

```sh
git diff --check
lychee --offline README.md AGENTS.md STANDALONE.md 'docs/**/*.md'
```

The [repository contract tests](../tests/test_repo_contracts.py) contain
checks for version consistency, publication identity, and leftover template
boilerplate. They also cover other aspects of the package. Report the scope
of the checks you ran rather than treating a subset as a full suite run.
