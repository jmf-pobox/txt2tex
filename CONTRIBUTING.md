# Contributing to txt2tex

This page is for people who change txt2tex. If you only want to use it, see the
[README](README.md).

Open work is tracked in
[GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues). That is the single
list of what needs doing. Check it before you start, and open an issue for
anything you find that is not listed.

## 1. Get set up

```bash
# Clone the repository
git clone https://github.com/jmf-pobox/txt2tex.git
cd txt2tex

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install txt2tex and the development tools
uv sync --group dev

# Check that it works
uv run txt2tex examples/01_propositional_logic/hello_world.txt
```

You also need:

- **LaTeX** (TeX Live or MacTeX) to build PDFs. See
  [Installation](README.md#installation).
- **fuzz**, the Z type checker, so `make fuzz-check` can run. See
  [Installation](README.md#installation). Without it, that target skips itself.
- **Node.js** (for `npx`) so `make lint-md` can run. Without it, that target
  skips itself.

Run `make help` to list every Makefile target.

Run `make dev-doctor` to check the toolchain. It reports whether `fuzz`,
`latexmk`, and `tex-fmt` are installed. It also runs `ethos doctor`, so it
fails if [ethos](https://github.com/punt-labs/ethos) is missing. ethos is only
needed for the agent team (section 10). Run `make dev-setup` to install it.

## 2. Branches and pull requests

`main` is protected. Every change goes through a branch and a pull request.
Merging requires:

- The `quality` checks to pass on Python 3.12 and 3.13
- All review threads resolved

Name branches with a prefix that says what the change is:

| Prefix | Use for |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `chore/` | Dependencies, tooling, housekeeping |
| `docs/` | Documentation only |
| `refactor/` | Code changes with no change in output |

```bash
git checkout -b feat/short-description main
# ... make changes ...
git commit -m "feat(parser): short description"
git push -u origin HEAD
# Open a pull request on GitHub
```

Commit messages follow
[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`,
`docs:`, `refactor:`, `test:`, `ci:`, `chore:`. Add a scope when it helps, for
example `fix(lexer): ...`.

### Review loop

Each push to a pull request triggers automated reviews (GitHub Copilot and
Cursor Bugbot) and the CI checks. Expect several rounds:

1. Push the branch.
2. Wait for CI and the review comments.
3. Fix every unresolved comment, even small ones, unless the comment is wrong.
4. Resolve the thread on GitHub and push.
5. Repeat until CI is green, every thread is resolved, and a new push brings no
   new findings.

Merge with a merge commit (`gh pr merge <N> --merge`). Do not squash. Do not
bypass branch protection.

After the merge, update your clone and delete the branch:

```bash
git checkout main && git pull
git branch -d feat/short-description
```

## 3. Quality gates

Run this before every commit. Fix every message it prints.

```bash
make check
```

`make check` runs these, in order:

| Target | What it does |
|--------|--------------|
| `make lint` | `ruff check` over all Python sources |
| `make lint-md` | `markdownlint-cli2` over all Markdown files |
| `make format-check` | Fails if `ruff format` would change anything |
| `make type` | `mypy` in strict mode on `src/txt2tex` and `tests` |
| `make type-pyright` | `pyright` in strict mode |
| `make test` | The pytest suite (excludes the e2e tests below) |

Other targets:

- `make format` rewrites Python files into the ruff style.
- `make test-cov` runs the tests with a coverage report. CI runs this instead of
  `make test`. A change must not lower the coverage of the files it touches.
- `make check-cov` is `make check` with coverage and without `lint-md`.
- `make fuzz-check` runs every `examples/**/*.txt` through
  `txt2tex --tex-only` and fails if fuzz rejects any of them. CI runs it as a
  separate job. If `fuzz` is not on your `PATH`, it prints a message and skips.
- `make complexity-report` writes `docs/complexity-report.md` and
  `docs/complexity-report.json`. Run it now and then, and after large changes.
  It is not a per-commit gate.

CI runs `make lint`, `make format-check`, `make type`, `make type-pyright`, and
`make test-cov` on Python 3.12 and 3.13, plus `make fuzz-check` once. CI does
not run `make lint-md` or the e2e tests.

### End-to-end tests

Every `.txt` file under `examples/` has a committed `.tex` file next to it. The
e2e test converts each `.txt` with `txt2tex --tex-only` and compares the result
byte for byte with the committed `.tex`.

```bash
make test-e2e     # run the comparison in parallel
make regen-e2e    # rewrite every committed .tex from its .txt
```

The e2e tests are too slow for `make check`, and CI does not run them. Run
`make test-e2e` yourself after any change that can alter generated LaTeX.

If the output changed on purpose, run `make regen-e2e`, then read
`git diff examples/`. Commit only the changes you meant to make. Never run
`make regen-e2e` to make a failing test pass without reading the diff.

The test ignores the `pdfcreator={txt2tex v...}` version stamp that titled
examples carry, so a version bump alone does not fail it. The comparison stops
at `.tex`. It does not compile to PDF or run fuzz. `make fuzz-check` covers
fuzz.

## 4. Where code lives

Source is in `src/txt2tex/`. The pipeline is lexer, parser, LaTeX generator.

| Path | What it holds |
|------|---------------|
| `cli.py` | The `txt2tex` command and its flags |
| `repl.py` | The interactive mode (`txt2tex -i`) |
| `compile.py` | Copies the bundled style files and runs LaTeX to make the PDF |
| `lexer.py`, `tokens.py` | Turns text into tokens |
| `parser.py`, `parser_pkg/` | Turns tokens into an AST. `parser_pkg/` holds the rules by construct (expressions, schemas, proofs, text blocks, and so on) |
| `ast_nodes.py` | The AST node types |
| `latex_gen.py`, `codegen/` | Turns the AST into LaTeX. `codegen/` holds the handlers by construct, plus the parenthesis policy and the overflow warnings |
| `free_vars.py` | Free variables of an expression |
| `errors.py` | Error messages with source lines and hints |
| `constants.py` | Shared constants |
| `latex/` | Bundled `fuzz.sty`, `zed-*.sty`, and `.mf` font files |

See [docs/DESIGN.md](docs/DESIGN.md) for the architecture, operator precedence,
and the reasons behind design choices.

Code standards:

- Type hints on every function. mypy runs in strict mode.
- `from __future__ import annotations` at the top of every file.
- All imports at the top of the file. No inline imports.
- Lines are at most 88 characters. Strings use double quotes.
- Fail fast. Raise an error on bad input instead of guessing.

Edit source files one at a time by hand. Do not rewrite many files with
`sed`, `awk`, or a script, even for a rename. Scripted edits have corrupted
files in this repository.

## 5. Tests

Tests are in `tests/`:

- `tests/test_NN_<topic>/` holds tests grouped by notation topic (propositional
  logic, sets, relations, schemas, and so on).
- Files directly under `tests/` cover cross-cutting features and single bug
  fixes (for example `test_cli.py` and `test_repl.py`).
- `tests/test_e2e_regression.py` is the e2e comparison from section 3.
- `tests/bugs/` holds small `.txt` inputs for bugs, limitations, and features.
  [tests/bugs/README.md](tests/bugs/README.md) lists them and their status.

Write the test first for every bug fix and feature. Run it and watch it fail.
Then make the change and watch it pass. A test must check the actual output,
for example the exact LaTeX fragment, not just that some marker appears.

To run part of the suite:

```bash
make test ARGS="tests/test_05_sets/"
make test ARGS="tests/test_cli.py -v"
```

### Reporting and fixing a bug

1. Write the smallest input that shows the bug. Save it as
   `tests/bugs/bugN_short_name.txt`.
2. Confirm it fails: `uv run txt2tex tests/bugs/bugN_short_name.txt`.
3. Open a GitHub issue using the bug report template in
   `.github/ISSUE_TEMPLATE/`.
4. Add the input and the issue number to
   [tests/bugs/README.md](tests/bugs/README.md).
5. Fix the bug with a regression test, and mention the issue in the commit.
6. When a bug class could exist in more than one place, search for the same
   pattern across the whole code base. Check every LaTeX render path
   (`codegen/` and `latex_gen.py`) and both entry points (the command line and
   the REPL).

## 6. Examples and committed output

`examples/` holds working examples, one folder per topic. Each `.txt` file has a
matching `.tex` and `.pdf` that are committed too. The `.tex` files are the
fixtures for the e2e test. The `.pdf` files are what readers see on GitHub.

When you add or change an example:

1. Write the `.txt` file.
2. Convert it: `uv run txt2tex examples/<folder>/<name>.txt`. This writes the
   `.tex` and the `.pdf`.
3. Commit all three files.
4. Run `make fuzz-check` so fuzz type-checks the new example.

To build every example, run `cd examples && make`. To build one folder, run
`cd examples && make 01_propositional_logic`.

Every syntax feature documented in
[docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md) needs a working example.

### Checking the PDFs

`scripts/qa_check_all.sh` (also `make qa`) runs `scripts/qa_check.sh` on every
PDF under `examples/`, skipping `reference/` and `infrastructure/`. It needs
`pdftotext` (from poppler). For each PDF and its `.tex` file it checks:

- Garbled em dashes caused by a broken relational image `R(| S |)`
- Bare math keywords such as `forall` inside `zed`, `axdef`, `schema`,
  `gendef`, and `argue` environments
- Possible run-on text (a warning only)
- Unconverted `[cite ...]` directives
- A complete document (`\documentclass`, `\begin{document}`, `\end{document}`)
- Matching `\begin` and `\end` for each Z environment

Run it before a release. Use `make qa-one PDF=path/to/file.pdf` to check one
file.

## 7. Documentation conventions

- Keep the README for people who use txt2tex. Developer material goes in this
  file.
- Update `CHANGELOG.md` under `## [Unreleased]` for every change a user can
  see. The format is [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
- Update the README or the guides when behavior changes.
- Add a decision record to `docs/DESIGN.md` when a change involves a design
  choice with rejected alternatives.
- Every command or LaTeX snippet in the docs must come from a real run. Run
  `uv run txt2tex --tex-only file.txt`, then copy the relevant fragment from
  the generated `.tex` file. The command itself prints only status lines.
- Check Markdown with `make lint-md`.

File names under `docs/`:

| Kind | Pattern | Examples |
|------|---------|----------|
| Reference and design docs | `UPPERCASE_WITH_UNDERSCORES.md` | `DESIGN.md`, `USER_GUIDE.md`, `FUZZ_VS_STD_LATEX.md` |
| Tutorials | `NN_lowercase_with_underscores.md` | `00_getting_started.md`, `01_propositional_logic.md` |

Rules:

1. No hyphens in file names. Use underscores.
2. Keep names descriptive and short, two to four words.
3. Use the same abbreviation in every file.

Where docs live:

- `docs/DESIGN.md` is the architecture and design decisions.
- `docs/guides/` holds reference guides for users.
- `docs/tutorials/` holds the step-by-step tutorials.
- `docs/development/` holds notes for contributors, including
  [AGENTS.md](docs/development/AGENTS.md).

## 8. Releasing

1. Set the new version in `src/txt2tex/__version__.py`. `pyproject.toml` reads
   it from there, so that is the only place to change.
2. In `CHANGELOG.md`, rename `## [Unreleased]` to the new version and date, and
   add a fresh empty `## [Unreleased]` above it.
3. Run `make regen-e2e`. Titled examples embed the version in their `.tex`
   (`pdfcreator={txt2tex vX.Y.Z}`). Read `git diff examples/`, and commit the
   updated files.
4. Run `make check` and `make test-e2e`.
5. Build and check the package:

   ```bash
   make build
   ```

   This runs `uv build` and `twine check dist/*`.

6. Install the built wheel in a clean environment and run it:

   ```bash
   uv run --isolated --with dist/txt2tex-*.whl -- txt2tex --help
   ```

7. Merge the release pull request.
8. Upload to PyPI:

   ```bash
   uvx twine upload dist/*
   ```

9. Create `release-notes.md` in the repository root. Copy the section for this
   version from `CHANGELOG.md` into it. Do not commit this file.
10. Tag the release and create the GitHub release:

    ```bash
    git tag vX.Y.Z
    git push origin vX.Y.Z
    gh release create vX.Y.Z --title "vX.Y.Z" --notes-file release-notes.md
    ```

    Delete `release-notes.md` afterwards.

11. Check the result at <https://pypi.org/project/txt2tex/>, then install it in
    a fresh environment:

    ```bash
    uv tool install txt2tex
    txt2tex --help
    ```

If something goes wrong:

- A version error from PyPI means the version already exists. Bump it and
  rebuild.
- Missing dependencies mean they are not in `[project] dependencies` in
  `pyproject.toml`.
- A command that does not run means the entry point in `[project.scripts]` is
  wrong.

## 9. Deferred lint rules

Ruff runs with a long list of rule sets (see `[tool.ruff.lint]` in
`pyproject.toml`). Two sets are left off because the number of violations is
high compared with the value of fixing them. If you touch the code involved,
consider fixing the violations.

Get the current counts with:

```bash
uv run ruff check --select TRY,PL --statistics .
```

The counts below are from that command.

### TRY (tryceratops): exception handling

| Rule | Violations | Description | Example |
|------|------------|-------------|---------|
| TRY003 | 204 | Raise vanilla args | `raise ParserError(f"Expected {x}")` should use custom exception subclasses |
| TRY300 | 1 | Consider `else` after `try` | A `return` inside a `try` body |

Why deferred: fixing it needs many custom exception subclasses (for example
`ExpectedTokenError` and `UnexpectedCharError`) in place of f-string messages
with `ParserError` and `LexerError`. The current messages are clear without
that overhead.

Revisit if error handling grows, for example if code needs to recover from
specific errors. Custom exceptions would help then.

### PL (pylint): code structure

| Rule | Violations | Description | Typical locations |
|------|------------|-------------|-------------------|
| PLR2004 | 260 | Magic value comparison | `if len(suffix) == 2`, `if depth > 10` |
| PLR0912 | 35 | Too many branches | Parser dispatch methods, lexer token handling |
| PLR0915 | 26 | Too many statements | Complex generation methods |
| PLR0911 | 16 | Too many return statements | Multi-case dispatch methods |
| PLW2901 | 12 | Redefined loop name | Loop variable reused |
| PLR1714 | 2 | Repeated equality comparison | Could use `in` operator |
| PLR0913 | 1 | Too many arguments | A helper with many parameters |
| PLR5501 | 1 | Collapsible `else if` | Fixable with `ruff --fix` |
| PLC0414 | 1 | Useless import alias | `import x as x` |

**PLR2004 (magic values).** These are comparisons like:

```python
if len(suffix) == 2:  # PLR2004: magic value 2
if depth > 10:        # PLR2004: magic value 10
```

Why deferred: many are thresholds specific to the notation, such as indent
levels and string lengths. A named constant adds words without adding clarity.
Some would gain from a constant, for example `MAX_NESTING_DEPTH`.

Revisit by adding a section to `constants.py` for thresholds that repeat or
carry meaning.

**PLR0912, PLR0915, PLR0911 (structural complexity).** 77 violations that
overlap with C90 (mccabe complexity). Functions flagged include:

- `_scan_token`, the lexer main dispatch (many branches by nature)
- `_parse_document_item`, the parser main dispatch
- `_generate_proof_node_infer`, complex proof tree rendering

Why deferred: these functions dispatch over many token and node types. Splitting
them would scatter logic that belongs together. C90 already covers them, with
`max-complexity = 30` and targeted `noqa` comments.

**PLR1714 (repeated equality).** Two violations of this shape:

```python
# Current:
if x == "a" or x == "b" or x == "c":
# Suggested:
if x in ("a", "b", "c"):
```

Easy fix when you are nearby.

**PLW2901 (redefined loop name).** 12 violations: a loop variable is reused in a
nested context. It is usually safe but can confuse a reader. Rename the inner
variable when you are nearby.

### Refactoring guardrails

- Run `make check` after every small change.
- Keep commits small, 1 to 5 files and under 100 lines.
- Make structure-only changes with identical observable behavior. Run
  `make test-e2e` to confirm the generated `.tex` did not change.

## 10. Agent team

The maintainers use [ethos](https://github.com/punt-labs/ethos) to run a team of
Claude Code agents: a principal who designs and reviews, a Z notation
consultant, and specialists for Python, build tooling, documentation, command
line design, and security review. Their definitions live in `.punt-labs/ethos/`
and load when you start Claude Code in this repository.

```bash
make dev-setup    # install ethos and regenerate .claude/agents/
make dev-doctor   # check ethos and the dev toolchain
make ethos-team   # show the team
```

You do not need ethos to contribute. txt2tex runs without it. See
[docs/development/AGENTS.md](docs/development/AGENTS.md) for who owns what and
how to delegate work to them.
