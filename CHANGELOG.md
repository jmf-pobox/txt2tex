# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Horizontal schema definitions (`defs` keyword) per Z RM §3.8.
  `Name [generics]? defs RHS` produces `\begin{zed} Name \defs RHS \end{zed}`.
  Two RHS forms are supported:
  - Schema reference (plain, Delta-decorated, or Xi-decorated):
    `OpAlias defs Delta Counter` → `OpAlias \defs \Delta Counter`
  - Inline schema text `[ decl-list | pred-list ]`:
    `NatPair defs [ x, y : N | x < y ]`
  Generic type parameters on the LHS are written in square brackets:
  `StackAlias[X] defs GenStack[X]`.  Multiple predicates in the inline text
  are separated by `;` in the source and joined with `\land` in the output.
  The `\defs` macro is defined in `fuzz.sty` line 280 as `\widehat=` — no
  preamble addition is needed.  New `HorizDef` and `SchemaText` AST nodes;
  `DEFS` token type; `defs` in `RESERVED_WORDS` (decoration forbidden).
  41 new tests; new example `examples/10_schemas/horizontal_defs.txt`
  (round-trips through fuzz cleanly).  Tutorial section in
  `docs/tutorials/09_schemas.md` and `USER_GUIDE.md` subsection added.

- θ-expression (`theta` keyword) per Z RM §3.10.  `theta S` constructs the
  binding whose components are the in-scope variables matching schema S's
  signature.  Decorated forms such as `theta S'` and `theta Booking'` are
  supported.  The keyword lexes as `THETA`, decoration is forbidden
  (`theta'` raises `LexerError`), and the generator emits `\theta S` — the
  standard Greek letter, compatible with both `fuzz.sty` and `--zed` mode.
  New `Theta(expr)` AST node in `ast_nodes.py` (frozen dataclass).
  25 new tests; new example `examples/10_schemas/theta_binding.txt` (round-trips
  through fuzz cleanly).  Tutorial section and `USER_GUIDE.md` subsection added.

- Schema inclusion in `axdef`, `schema`, and `gendef` declaration lists; `Delta`
  and `Xi` shorthand per Z RM §3.7 and §5.2. Three forms are supported:
  - bare: `Counter` on its own line brings the schema's components into scope
  - `Delta Airline` — before/after state convention, emits `\Delta Airline`
  - `Xi Card` — read-only operation convention, emits `\Xi Card`
  Generic instantiation in inclusions (`Delta Stack[Int]`) is also supported.
  The parser disambiguates bare inclusions from typed declarations with a
  scan-ahead rule: if a colon appears before the next newline, the line is a
  typed declaration; otherwise it is a schema inclusion.  `count, limit : N`
  is unambiguously a typed declaration regardless of whether schema names
  `count` or `limit` exist.
- `DELTA` and `XI` token types added to `TokenType`; `Delta` and `Xi` keywords
  added to `KEYWORD_TO_TOKEN` and `RESERVED_WORDS` (decoration of these
  keywords is forbidden by lexer, matching Z RM intent).
- `SchemaInclusion` AST node in `ast_nodes.py` with `name`, `decoration`, and
  `generics` fields.
- Two new examples in `examples/10_schemas/`: `delta_xi_inclusion.txt` (Δ/Ξ
  airline booking probe) and `schema_as_predicate.txt` (schema conjunction).
  Both round-trip through fuzz cleanly.
- `examples/Makefile` now includes `10_schemas` as a named target with short
  alias `10`.
- New tutorial section "Schema Inclusion and Δ/Ξ" in
  `docs/tutorials/09_schemas.md`.
- New section "Schema Inclusion (Bare, Δ, Ξ)" in `docs/guides/USER_GUIDE.md`
  documenting all three forms, disambiguation rule, and schema-as-predicate.

- Identifier decoration (primes `'`, inputs `?`, outputs `!`) — Z RM §3.3
  trailing-suffix rule. The identifier lexer now consumes any run of `'`, `?`,
  `!` characters in any order after the alnum/underscore base (e.g., `count'`,
  `in?`, `out!`, `x?'`, `s''`). This is the foundational change for SBM
  (State-Based Modelling) course support.
- String literal lexeme — a single-quoted value (`'sunk'`, `'survived'`) is
  now tokenised as `STRING` and parsed as `StringLit`. The generator emits the
  Z-convention quoting: `` `value' `` in fuzz mode and `\text{`value'}` in
  standard LaTeX mode. This is the foundational change for DAT (Database
  Design) course support.
- Comma-separated variable lists in schema, axdef, and gendef declaration
  blocks (`count, count' : N` declares two variables sharing one type).
- Two new getting-started examples: `decorated_identifiers.txt` (SBM schema
  probe) and `string_literals.txt` (DAT string literal syntax).
- `examples/Makefile` now includes `00_getting_started` as a named target
  with the short alias `00`.

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
