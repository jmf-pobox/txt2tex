# End-to-End Regression Test Plan

**Status**: PROPOSED
**Author**: adb (Ada B)
**Mission**: m-2026-04-13-002
**Date**: 2026-04-13

## 1. Scope

### In scope

- End-to-end regression coverage for all `.txt` files under `examples/`.
- The full pipeline: txt2tex generation → `.tex` fixture comparison → latexmk
  compilation → exit-code check → optional fuzz type-check pass.
- 141 source files across 15 directories (`00_getting_started` through
  `user_guide/`, plus `fuzz_tests/`).
- Integration with CI on every PR.

### Out of scope

- The 845-test unit suite under `tests/` — that suite stays unchanged.
- Restructuring `examples/` directories.
- Converting `tests/bugs/` fixtures to pass (they document known behaviour;
  see §4).

## 2. Current State

| Asset | Count |
|-------|-------|
| `.txt` source files in `examples/` | 141 |
| `.tex` committed fixtures | 143 |
| `.pdf` committed fixtures | 145 |

The two extra `.tex` / four extra `.pdf` files (delta with `.txt` count) are
legacy artefacts in `examples/infrastructure/` and `examples/00_getting_started/`
that have no `.txt` source. The regression suite ignores them.

CI today (`quality.yml`) installs `texlive-latex-base texlive-latex-extra
texlive-fonts-recommended` on `ubuntu-latest` but runs only the unit suite.
It does not invoke `txt2tex` on any example or compile any `.tex` to PDF.
fuzz and latexmk are not installed in CI. `make dev-doctor` reveals both as
present-or-missing on a developer machine; neither is gated in CI.

## 3. Fixture Strategy

### What is committed

- The generated `.tex` file for every `.txt` source is a first-class committed
  asset (project policy). These serve as the golden fixtures for text-diff
  assertions.
- `.pdf` files are also committed, but binary diffs are not actionable; the
  suite asserts on exit code and log cleanliness rather than byte equality.

### Determinism of `.tex` output

txt2tex's generator is purely functional over the AST: no timestamps, no
random seeds, no platform-varying paths. The `.tex` header is a fixed
template. Generation is therefore deterministic across platforms and Python
versions. The text-diff assertion is exact (`==`), not fuzzy.

One exception: examples whose `.txt` source includes `TITLE:` metadata
cause `latex_gen.py` (line 582) to emit `\hypersetup{pdfcreator={txt2tex
v<__version__>}}` in the generated `.tex`. A version bump therefore changes
the `.tex` output for every titled example. After any version increment,
`make regen-e2e` must be run for all titled examples and the updated fixtures
committed before Stage A can pass. This step is part of the release
checklist.

### What is not deterministic

PDF output contains a `CreationDate` and font-embedding artefacts that differ
across latexmk runs and platforms. The suite never byte-compares `.pdf` files.
Intermediate LaTeX files (`.aux`, `.log`) also vary; they are not committed
and are cleaned up after each test.

### Fixture regeneration

Behaviour changes that legitimately alter `.tex` output require regenerating
committed fixtures. The blessed workflow:

1. Run `txt2tex <file.txt>` locally for the affected examples.
2. Inspect the diff (`git diff examples/`) to confirm only intended changes.
3. Commit the updated `.tex` files on the feature branch alongside the code
   change.
4. CI picks up the new fixtures; the text-diff assertion passes.

A Make convenience target, `make regen-e2e`, automates step 1 for all 141
examples. It is a developer tool only; CI never calls it. The target is
implemented in Phase 2 (§7).

## 4. Assertion Strategy per Stage

### Stage A: Generation (`.txt` → `.tex`)

- Invoke `txt2tex <source.txt> --tex-only` (or equivalent flag that writes
  `.tex` without compiling).
- Read the generated `.tex` and the committed fixture.
- Assert exact text equality.
- On failure: diff the two files and surface the first N differing lines as
  the pytest failure message. This pinpoints which expression changed.

### Stage B: Compilation (`.tex` → `.pdf`)

- Invoke `latexmk -pdf -interaction=nonstopmode -halt-on-error <file.tex>`
  in the example's directory (with `TEXINPUTS` pointing at
  `examples/infrastructure/` for `fuzz.sty` and font files).
- Assert exit code 0.
- On failure: surface the last 40 lines of the `.log` file. LaTeX errors
  always appear near the bottom.

### Stage C: fuzz type-check (optional, Z-bearing examples only)

- Invoke `fuzz <file.tex>` where available.
- Assert exit code 0.
- Examples in `fuzz_tests/` are the primary targets; Z-notation examples in
  `06_definitions/`, `07_relations/`, `08_functions/`, `10_schemas/` are
  also candidates.
- Examples for which fuzz intentionally produces errors (the `bug3_*`
  fixtures in `tests/bugs/`) are excluded from this stage.

## 5. Handling Non-Standard Fixtures

### tests/bugs/ fixtures

The 26 files in `tests/bugs/` fall into three categories (per
`tests/bugs/README.md`):

- **Limitation tests** (3 files, `bug1_*`, `bug3_*`): expected failures.
  `bug3_compound_id.txt` generates valid LaTeX but fuzz rejects it by design.
  These must not appear in the e2e suite as passing examples. They are
  excluded from Stage A by directory; if included at all they belong in a
  separate parametrize group marked `xfail` with the documented reason.
- **Regression tests** (16 files): all pass generation. Include in Stage A
  but not Stage B or C, since they are not compiled to PDF.
- **Feature tests** (7 files): same as regression tests.

The simplest approach: exclude `tests/bugs/` from the e2e suite entirely.
The existing unit tests already cover the regression and feature cases.
If that changes, add a `@pytest.mark.xfail(reason="limitation: fuzz rejects
R^+", strict=True)` marker on the three limitation tests.

### fuzz optionality

fuzz is not installed on the GitHub Actions `ubuntu-latest` runner and has no
apt package. Stage C is **optional by default**: the suite skips it with
`pytest.skip("fuzz not available")` when `shutil.which("fuzz")` returns
`None`. CI passes without it. Stage C runs only on developer machines where
fuzz is present, and in any future CI runner that installs it.

latexmk is similarly optional for Stage B. The `quality.yml` runner currently
installs `texlive-latex-base` (which includes `pdflatex`), so Stage B can run
in CI if latexmk is added to the apt install list. This is a Phase 2
decision (see §7).

### examples that do not have a paired .tex fixture

Two `.tex` files exist without a corresponding `.txt`. These are legacy and
not generated by txt2tex. The discovery logic collects `.txt` files and pairs
each with `<stem>.tex`; the two orphan `.tex` files are never collected.

## 6. CI Integration

### Trigger

The e2e suite runs on every PR and every push to `main`, same triggers as the
existing quality gate.

### Timing budget

Stage A (generation, 141 examples): generation is fast — roughly 0.1–0.3 s
per example on a 2024 laptop. Total wall time ≈ 15–45 s for the full corpus,
parallelised with `pytest-xdist -n auto`. CI budget: under 2 minutes.

Stage B (latexmk compile, 141 examples): latexmk is expensive — 3–7 s per
example × 141 = 7–17 minutes serial. This is too slow to run on every PR.
**Recommendation**: Stage B runs only on scheduled weekly CI (`schedule:
cron: '0 4 * * 0'`) and on pushes to `main`, not on PRs. On PRs, the suite
runs Stage A only.

Stage C (fuzz): Not available in the CI runner in Phase 1. Deferred to Phase
3.

### Failure report format

A failing Stage A test outputs:

```text
FAILED tests/e2e/test_examples.py::test_generation[user_guide/07_truth_table]
AssertionError: Generated .tex differs from fixture.
First 10 differing lines:
  - \noindent $p \land q$
  + \noindent $p \lor q$
Fixture: examples/user_guide/07_truth_table.tex
Generated: /tmp/pytest-of-.../07_truth_table.tex
Regenerate with: make regen-e2e FILTER=user_guide/07_truth_table
```

A failing Stage B test outputs the last 40 lines of the LaTeX `.log` file
and the latexmk exit code.

### Fixture regeneration in CI

CI never regenerates fixtures. If Stage A fails on a PR it means the code
change altered output and the developer did not update the fixtures. The fix
is: run `make regen-e2e` locally, inspect the diff, commit the updated
`.tex` files.

## 7. Phased Implementation

### Phase 1: Generation fixture assertions (Stage A)

**Deliverable**: `tests/e2e/test_examples.py` with parametrized Stage A
coverage for all 141 examples. A new `make test-e2e` target. CI wired on
all triggers (PR + push to main).

**What to build**:

- Discover all `.txt` files under `examples/` (excluding
  `examples/infrastructure/`). Parametrize by relative path. Path collection
  happens at module level (or via `pytest_generate_tests`), not inside the
  test function body — this is required for correct `pytest-xdist` work
  distribution; a lazy generator inside the test body would not parallelize.
- For each: invoke `txt2tex <source.txt> --tex-only` via `subprocess.run`,
  writing the generated `.tex` to pytest's `tmp_path` (not to the example's
  source directory); compare the `tmp_path` output to the committed fixture.
  Writing to `tmp_path` avoids parallel-write conflicts under `pytest-xdist`
  and keeps the working tree clean.
- `conftest.py` fixture that determines the repo root (`git rev-parse
  --show-toplevel`) so paths are absolute regardless of `cwd`.
- A `make regen-e2e` target that regenerates all `.tex` fixtures in place.
- `make test-e2e` that invokes `pytest tests/e2e/ -n auto`.
- No changes to `make check`.

**Success criteria**: all 141 Stage A tests pass on CI (ubuntu-latest,
Python 3.12 and 3.13). Wall time under 2 minutes with `-n auto`.

### Phase 2: Compilation assertions (Stage B)

**Deliverable**: Stage B tests added to `tests/e2e/test_examples.py`.
New `test-e2e-full` Make target. Scheduled weekly CI job.

**What to build**:

- Add latexmk to the CI apt install list (`latexmk`).
- Skip Stage B if `shutil.which("latexmk")` is `None`.
- For each example that passed Stage A: run latexmk, assert exit code 0,
  surface `.log` tail on failure.
- `make test-e2e-full` runs both Stage A and Stage B.
- Add a `schedule:` trigger to `quality.yml` running `make test-e2e-full`
  weekly (Sunday 04:00 UTC).

**Success criteria**: all 141 Stage B tests pass on the weekly run. Per-run
wall time under 20 minutes (with `-n4` parallelism).

### Phase 3: fuzz type-check assertions (Stage C)

**Deliverable**: Stage C tests added, triggered only when fuzz is present.

**What to build**:

- Add a `pytest.ini` marker `fuzz` so `pytest -m fuzz` runs Stage C only.
- Identify Z-bearing examples (heuristic: `.tex` contains `\begin{zed}` or
  `\begin{schema}` or `\usepackage{fuzz}`).
- Skip Stage C unless `shutil.which("fuzz")` is non-`None`.
- Assert fuzz exit code 0.
- `make test-e2e-fuzz` for developer use only.

**Success criteria**: Stage C passes locally for all non-limitation examples
in `fuzz_tests/` and `06_definitions/` through `10_schemas/`.

## 8. Relationship to `make check`

**Recommendation**: keep `make test-e2e` separate from `make check`.

`make check` is the local development gate: fast (< 60 s), runs on every
save, must not block iteration. Folding 141 parametrized subprocess invocations
into it would push it past 90 seconds on a developer laptop and past the
acceptable threshold for a pre-commit loop.

`make test-e2e` is wired into CI (Stage A on every PR) but not into
`make check`. Developers can invoke it manually before pushing. The contract
is: if a code change alters `.tex` output, `make test-e2e` fails locally
before the PR is opened, and the developer regenerates fixtures with
`make regen-e2e`.

`make check` is not changed by this plan.

## 9. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Flaky tests from `--tex-only` invoking the CLI as a subprocess | Low | Medium | Pin `txt2tex` invocation to `uv run txt2tex` with the project's locked deps; use `subprocess.run` with a fixed `PATH`. |
| Stage A finds 5–10 examples whose committed `.tex` is stale | High | Low | Acceptable first-pass failure; regenerate fixtures as part of Phase 1 work. |
| latexmk on ubuntu-latest behaves differently than macOS | Medium | Medium | Pin TeX Live version in apt; add a `texlive-full` fallback if fonts are missing. Run Stage B locally on macOS before enabling CI. |
| fuzz not installable in any CI runner | High | Low | Stage C is explicitly optional; the suite degrades gracefully. |
| user_guide/ grows faster than expected, adding compilation time | Low | Low | Weekly schedule for Stage B absorbs growth; `-n auto` parallelism scales. |
| Fixture regeneration committed accidentally | Low | Medium | `make regen-e2e` writes only to `examples/`; git diff is human-reviewed before commit. No CI automation touches fixtures. |
| Version bump breaks Stage A for titled examples | Medium | Low | `make regen-e2e` is part of the release checklist; titled examples embed `__version__` via `\hypersetup{pdfcreator=...}` and must be regenerated after every version increment. |
| Performance regression goes undetected | Medium | Medium | No timing assertion exists; an O(n²) generator regression would not be caught by Stage A. Out of scope for this plan — deferred to a future profiling harness. |
| LaTeX warnings suppressed in Stage B | Medium | Low | `latexmk` exits 0 on `Overfull \hbox` or undefined citation warnings; Stage B asserts only on exit code. Warning surveillance (parsing `.log` for `Warning:` lines) is out of scope for Phase 2; deferred to Phase 3 or a dedicated log-audit step. |

## 10. Open Questions for jra / rmh

1. **`--tex-only` flag**: Does `txt2tex` currently support a flag that writes
   the `.tex` file and exits without compiling? If not, Phase 1 needs either
   a new flag (rmh's domain) or a workaround (mock the compile step via env
   var or skip-compile flag). The test plan assumes this flag exists or will
   be added.

2. **Stage B in CI on PRs**: The plan defers Stage B to weekly CI to control
   cost. If jra prefers Stage B on every PR, the CI runner needs latexmk and
   a budget of 15–20 minutes per run, which is within GitHub Actions free
   tier for this repo size. Needs explicit sign-off.

3. **tests/bugs/ in e2e**: The plan excludes `tests/bugs/` from the e2e
   suite. If the intent is to gate regression fixes via e2e, include them
   with `xfail` markers. Needs a policy decision before implementation.
