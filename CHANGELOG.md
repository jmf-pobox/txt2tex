# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-04-14

### Added

- `EQUAL:` block for expression equality chains — steps joined by `=` instead
  of `⇔`. Use for natural-number, set, and sequence equational reasoning
  (e.g., induction base cases). The `connector` field on `ArgueChain` selects
  the connective: `"iff"` (default, `EQUIV:`/`ARGUE:`) or `"eq"` (`EQUAL:`).
- Parenthesisation policy implementation (ADR §4, five gaps closed):
  - Arithmetic operators (`+`, `-`, `*`, `mod`) in PRECEDENCE table
  - `UNARY_PRECEDENCE` dict as machine-readable policy for unary binding
  - Set-comprehension predicate now receives parent context; always-paren
    rules fire for nested quantifiers (fixes Q8(b) assessment feedback)
  - Cross-product paren exemption documented with Z RM §2.5 citation
  - Parametrised precedence test matrix (2240 cases, self-maintaining)
- Phase 1 end-to-end regression suite (`make test-e2e`) — 141 examples
  under pytest-xdist with exact `.tex` fixture diffs
- Markdownlint adopted and wired into `make check`
- CLI help epilog distinguishing default/`--tex-only`/`-i`/`--check-env` modes
- Two-page reference card (`docs/cheatsheet.pdf`) with proof examples
- Three getting-started examples (`examples/00_getting_started/`)
- Ethos agent team for development workflow (`.punt-labs/ethos/`)
- `py.typed` marker (PEP 561)
- `install.sh` for macOS and Linux

### Changed

- Migrated toolchain from hatch to uv
- Added Makefile with quality gate targets (`make check`, `make test`, etc.)
- Bumped minimum Python version from 3.10 to 3.12
- Updated CI workflow to use uv via `astral-sh/setup-uv`

### Removed

- HTML export with KaTeX rendering (`--html`, `--validate` flags)
- Bibliography parser (`bib_parser.py`) — only used by KaTeX export
- 19 development-era cruft files from `examples/`

### Fixed

- `o9` (forward composition) now emits `\semi` instead of `\circ` — all nine
  emission sites updated. `comp` (backward, `\comp`) was already correct.
- Broken tutorial navigation links (relative paths inside `docs/tutorials/`)
- Stale filenames in `examples/README.md`
- Wrong tutorial cross-references in two example category READMEs

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
