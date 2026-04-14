# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Parenthesisation policy gaps #1, #2, #3** (ADR §4 *Known gaps*):
  - **Gap #1** — Arithmetic operators `+`, `-`, `*`, `/`, `mod` are now
    explicit entries in `LaTeXGenerator.PRECEDENCE` with correct relative
    levels (`*`/`/`/`mod` = 11, `+`/`-` = 10). Previously these fell to
    the default 999, which could produce wrong parens when arithmetic
    expressions appeared as children of same-default-level operators.
  - **Gap #2** — `LaTeXGenerator.UNARY_PRECEDENCE` dict is the
    machine-readable policy for unary binding strength (level 20, above
    all binary operators). Fuzz-mode quirks in `_generate_unary_op`
    (cardinality `#` with function application, `bigcup`/`bigcap` with
    prefix-function operands) are documented with citations to fuzz
    manual §2.3-2.4 rather than inline magic strings. The logic is
    otherwise unchanged so no output regression occurs.
  - **Gap #3** — `_generate_set_comprehension` now passes `parent=node`
    when generating the predicate expression, so nested quantifiers
    inside `{ x : T | exists ... }` receive their parent context and the
    always-paren rule fires correctly. This fixes the Q8(b) assessment
    feedback where the grader expected parens around an existential
    predicate inside a set comprehension.

### Changed

- Migrated toolchain from hatch to uv.
- Added Makefile with standard quality gate targets (`make check`, `make test`, etc.).
- Bumped minimum Python version from 3.10 to 3.12.
- Updated CI workflow to use uv via `astral-sh/setup-uv`.
- Consolidated pytest config into pyproject.toml (removed pytest.ini).
- Replaced `[project.optional-dependencies] dev` with `[dependency-groups] dev`.

### Added (earlier)

- `py.typed` marker (PEP 561)
- CHANGELOG.md
- `EQUAL:` block syntax for expression equality chains. Steps are joined by `=`
  rather than `\Leftrightarrow`, making it correct for natural-number and
  expression-valued chains (e.g., `length s = length (tail s) + 1`). The
  `connector` field on `ArgueChain` selects the connective: `"iff"` (default,
  used by `EQUIV:`/`ARGUE:`) or `"eq"` (used by `EQUAL:`).
- Renamed internal flag `_in_equiv_block` to `_in_argue_block` in `LaTeXGenerator`
  to reflect that it covers `EQUIV:`, `ARGUE:`, and `EQUAL:` contexts.
- Documented the parenthesisation policy as a settled ADR in `docs/DESIGN.md`
  (§4 *Parenthesisation Policy*): precedence-driven with an enumerable
  always-paren set for quantifier bodies containing connectives and nested
  quantifiers in set-comprehension constraints. Z RM citations included.
  Five known gaps tracked for follow-up work (arithmetic precedence entries,
  unary precedence unification, set-comprehension parent-arg fix, cross-product
  rationale capture, and a parametrised precedence-matrix test).

### Removed

- HTML export with KaTeX rendering (`--html`, `--validate` flags)
- Bibliography parser (`bib_parser.py`) — was only used by KaTeX export

### Fixed

- `o9` (forward composition) now emits `\semi` instead of `\circ`. `\semi` is
  the fuzz Chapter 3 macro for schema/relation forward composition. `\circ` is
  a standard math operator not defined by fuzz.sty. This affected expression
  generation, text-block substitution, justification escaping, and proof-tree
  label processing — all nine emission sites updated uniformly. `comp` (backward
  relational composition, fuzz `\comp`) is unaffected: it maps to a distinct
  fuzz Chapter 4 macro and was already correct.
- Stale version `0.1.0` in `__init__.py` (now imports from `__version__.py`)

## [1.1.0] - 2025-12-01

### Added

- Interactive REPL mode for live conversion
- HTML export with KaTeX rendering (two-pass generation for TOC, citations, bibliography)
- WYSIWYG line break support after bullet separator
- PDF metadata via hypersetup
- Developer workflow guide
- Branch protection support files

### Fixed

- Bullet separator continuation and operator precedence
- Spacing around operators in justifications
- latexmk `-gg` flag for consistent bibliography generation
- tex-fmt integrated into CLI (removed txt2pdf.sh)

## [1.0.0] - 2025-11-29

### Added

- Lexer, parser, and LaTeX generator architecture
- Z notation support: schemas, axdefs, gendefs, free types, abbreviations
- Proof tree rendering with natural deduction
- Truth tables, equivalence chains, ARGUE blocks
- Set comprehensions, relations, functions, sequences, bags
- Quantifiers (forall, exists, exists1, mu, lambda)
- Conditional expressions (if/then/else/otherwise)
- fuzz typechecking integration
- latexmk for multi-pass compilation
- Overflow warning system for wide content
- 141 working examples across 13 categories
- Comprehensive test suite (1300+ tests)
- CI with ruff, mypy, pyright, pytest
- PyPI publishing as `txt2tex`

## [0.9] - 2025-11-23

### Added

- Complexity metrics with radon and xenon
- Regression tests for section headers with prose-starter words
- USER_GUIDE examples (61 working examples)

### Changed

- Relocated test files into topic-based directories
- Tightened linting standards (S, BLE, A, ARG, ERA, PIE, RET, RSE, PERF, PTH, ISC, FBT, C90, PT, SLF)
- Decomposed `_process_inline_math` into 11 pipeline stages

## [0.8] - 2025-10-30

Initial tagged release with core parsing and LaTeX generation for propositional logic, predicate logic, sets, and basic Z notation.
