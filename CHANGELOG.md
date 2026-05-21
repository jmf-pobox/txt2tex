# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Migration Notes (Prior-Release Users)

This section summarises what to expect when upgrading. Most `.txt`
files compile unchanged; output LaTeX may differ visually.

**Parse-time changes — one new error to know about:**

- Reserved Z operator names (`id`, `dom`, `ran`, `inv`, `comp`, `mod`,
  `bigcup`, `bigcap`, `filter`) used as a declaration variable name in
  a `schema`, `axdef`, or `gendef` body now raise a clear
  `ParserError`. Previously the parser silently accepted them and the
  generator emitted the operator symbol (`\id`, `\dom`, …), producing
  fuzz-rejected output. If your `.txt` used `id : T` as a schema
  field, rename to `id1`, `idVal`, `myId`, etc.

**Rendering improvements — same input, better-looking or fuzz-cleaner output:**

| Construct | Before | After |
|---|---|---|
| Multi-decl `forall`/`exists`/`exists1` | `\forall x : T @ \forall y : U @ P` | `\forall x : T; y : U @ P` (Spivey) |
| Multi-decl `mu` | `(\mu x : T \| (\mu y : U \| ...))` (fuzz REJECTED) | `(\mu x : T; y : U \| ...)` (fuzz-clean) |
| Multi-decl `lambda` | nested + conditional paren-wrap | Spivey + unconditional paren-wrap in fuzz mode |
| Bindings | `\lblot name == e \rblot` (flush) | `\lblot~name == e~\rblot` (thin-spaced) |
| Relational algebra | `\sigma_p(R)`, `\pi_{A,B}(R)`, `\rho_{...}`, `\bowtie`, `\bowtie_p` | `\mathrm{Restrict}_p(R)`, `\mathrm{Project}\{A,B\}(R)`, `\mathrm{Rename}_{...}`, `\otimes`, `\mathrm{Join}_p` |

These are not breaking — your `.txt` parses the same; only the
rendered `.tex` differs. The Spivey-form, paren-wrap, dependent-domain,
and binding-spacing changes are strict improvements: same semantics
and fuzz now accepts several forms it previously rejected.
The relational-algebra keyword rendering is the one purely
stylistic change. Regenerate any `.tex` files produced by an earlier
version to pick up the new output.

**Strictly additive** (never affect existing `.txt` files):

- `LINEBREAK:` directive, `pk` annotation, Z bindings `{| ... |}`,
  schema renaming `S[a/b]`, horizontal schema definitions
  `Name defs Schema-Exp`, schema-calculus operators in `defs` RHS
  (`;`, `>>`, `hide`, `project`), GROUP/UNGROUP, multi-typed
  comprehensions with conjunction predicates over tuple projections,
  algebra WYSIWYG line breaks, dependent-domain detection.

### Fixed

- **Dependent-domain detection in Spivey-form quantifier collapse** (commit
  `92823b7`). `_collect_quantifier_chain` and `_collect_lambda_chain`
  previously collapsed all same-quantifier chains into a single Spivey schema
  text regardless of whether later declarations' domains referenced earlier-bound
  names. Fuzz parallel-binds co-declarations (Z RM §3.5), so such output was
  rejected. A new module `src/txt2tex/free_vars.py` provides
  `expr_free_vars(expr) → frozenset[str]`; the chain helpers use it to stop
  collapse at the first dependency, emit the independent prefix in Spivey form,
  and recurse on the tail (Z RM §3.9 split identity). Set comprehensions with
  dependent extra declarations now raise a clear `ValueError` (Z RM §3.10 has
  no split identity). 11 xfails in `tests/test_spivey_dependent_domain.py`
  flipped to PASS.

  Before (fuzz-rejected — `y`'s domain references `x` in the same schema text):

  ```text
  forall x : N; y : 1..x . y <= x
  ```

  ```latex
  \forall x : \nat; y : 1 \upto x @ y \leq x   % fuzz rejects
  ```

  After (fuzz-clean — nested form for the dependent declaration):

  ```latex
  \forall x : \nat @ \forall y : 1 \upto x @ y \leq x
  ```

- **Natural newline and `\` continuation after `|` in semicolon-chained
  quantifier bindings.** `_parse_quantifier_continuation` now honours an
  explicit `\` continuation or a bare WYSIWYG newline immediately after `|`,
  mirroring the logic already present in `_parse_quantifier` for single-binding
  quantifiers. Previously, `forall x : T; y : U; z : V | body` with a newline
  after `|` silently collapsed to a single line; the single-binding form
  `forall x : T | body` already worked. The fix applies to all four quantifier
  types (`forall`, `exists`, `exists1`, `mu`). The bullet (`.`) separator in
  constraint-plus-body form was already handled by the continuation path.

  Before (chained form silently dropped the newline):

  ```text
  forall s : Ship; o : Outcome; b : Battle |
    (o.ship = s.name land o.battle = b.name) => (s.launched <= b.date)
  ```

  ```latex
  % old output — newline after | ignored, everything on one line:
  \forall s : Ship; o : Outcome; b : Battle @ (o.ship = s.name ...
  ```

  After (newline honoured):

  ```latex
  \forall s : Ship; o : Outcome; b : Battle @ \\
  \t1 (o.ship = s.name \land o.battle = b.name) \implies ...
  ```

- **Q2(d) comprehension/quantifier parser bugs** (commits `20a6daa`, follow-on
  residual fix, and `fix(parser): add SEMICOLON/PIPE branches to _parse_lambda`).
  Three interrelated bugs prevented multi-typed relational-calculus expressions from being
  written natively without LaTeX escape:

  - The `is_bullet_indicator` heuristic (45 lines, `_parse_postfix` lines 3637–3681)
    conflated field-projection PERIOD (`s.x`) with the comprehension bullet separator
    (`. E` in `{ s : Ship | P . E }`). Deletion lets `safe_followers` handle
    termination correctly; bullet detection remains the outer parser's responsibility.
  - Two residual disambiguation bugs: chained `TupleProjection` inside `mu` greedily
    consumed the bullet PERIOD; the RBRACE-separator heuristic swallowed RHS
    projections in comparison expressions. Both fixed with targeted flags.
  - `_parse_lambda` lacked SEMICOLON/PIPE branches; multi-decl lambda now delegates
    to `_parse_quantifier_continuation`, producing nested `Quantifier(quantifier="lambda")`
    nodes. `latex_gen.py` QUANTIFIERS dict gains `"lambda": r"\lambda"`.

  All 13 tests in `tests/test_q2d_calculus_predicate_chain.py` pass. Before this fix:

  ```text
  { s : Ship; c : Class | s.name = c.name land s.displacement > 500 . (s, c) }
  ```

  raised a parser error. After:

  ```text
  \{ s : Ship; c : Class | s.name = c.name \land s.displacement > 500 \bullet (s, c) \}
  ```

  Multi-typed comprehensions, multi-decl `forall`/`exists`/`mu`/`lambda`, and
  conjunction predicates over tuple projections all now work. See `DESIGN.md` ADR
  for the open question on multi-decl lambda LaTeX form (nested vs Spivey canonical).

### Breaking Changes

Source-syntax breaks only. Visual rendering changes are listed under
**Changed (rendering)** below.

- **Reserved Z operator names rejected in declaration positions** (commit
  `7fb6567` and the parser change folded into it). `id`, `dom`, `ran`,
  `inv`, `comp`, `mod`, `bigcup`, `bigcap`, `filter` used as declaration
  variable names in `schema`, `axdef`, or `gendef` now raise
  `ParserError` with a clear message. Previously parsed silently and
  emitted broken LaTeX. Migration: rename the field (`id` → `id1`,
  `idVal`, etc.).

(Notes: `:=` and `relvars` are documented as removed below but were
added *and* removed within this branch's development; they never
reached the prior release, so they are not user-visible breaks.)

### Changed (rendering)

The source syntax is unchanged for everything below — same `.txt`
parses the same. Only the rendered LaTeX differs. Regenerate any
`.tex` produced by an earlier version to pick up the new output.

- **Natural-join emission `\bowtie` → `\otimes`.** Source `R bowtie S`
  now renders as `R \otimes S`. Theta-join `R bowtie [p] S` was
  similarly `\bowtie_p`; see entry below.

- **Relational algebra renders in keyword form.**
  `sigma[p](R)` now emits `\mathrm{Restrict}_{p}(R)` (previously
  `\sigma_p(R)`); `pi[A, B](R)` emits `\mathrm{Project}\{A, B\}(R)`
  (previously `\pi_{A,B}(R)`); `rho[A as B](R)` emits
  `\mathrm{Rename}_{A \to B}(R)` (previously `\rho_{A \to B}(R)`).

- **Theta-join function form.** `R bowtie [p] S` now emits
  `\mathrm{Join}_{p}(R, S)` (previously `R \otimes_{p} S`). Natural
  join without a predicate (`R bowtie S`) is unchanged: still
  `R \otimes S`.

- **Spivey-canonical multi-decl quantifiers** (commits `71ce521`,
  `92823b7`). Multi-decl `forall`/`exists`/`exists1`/`mu`/`lambda`
  chains now emit as one quantifier token with semicolon-separated
  SchemaText (`\forall x : T; y : U @ P`) instead of nested tokens
  (`\forall x : T @ \forall y : U @ P`). Matches Z RM §3.9 split
  identity. The previous nested form for multi-decl `mu` was actually
  fuzz-rejected; the new Spivey form is fuzz-clean — a strict
  improvement.

- **Lambda unconditional paren-wrap in fuzz mode** (commits `71ce521`,
  follow-on). Fuzz requires `(\lambda S @ E)` around every lambda.
  The generator previously wrapped only when `parent is not None`,
  which missed abbreviation RHS, set literals, sequence displays, and
  top-level zed predicates. Now unconditional in `use_fuzz=True`.
  Every lambda in the output gains surrounding parens — strict
  improvement; fuzz accepts cases it previously rejected.

- **`\div` operator surrounded by non-breaking spaces.** Source `R div S`
  previously emitted `R \div S`; it now emits `R~\div~S`. fuzz.sty renders
  `\div` as the sans-serif word "div" (not the ÷ glyph), and the default
  `\mathbin` spacing was too tight in dense binding-body contexts such as
  `numScripts(p) div numSessions(p)`. The `~` non-breaking spaces provide
  consistent visual separation without altering semantics. The line-break form
  similarly changed from `R \div \\\\ ...` to `R~\div~\\\\ ...`.

- **Z bindings thin-spaced inside brackets** (commit `1cd9761`).
  `{| name == e |}` previously emitted `\lblot name == e \rblot`
  (content flush against bracket symbols); now emits
  `\lblot~name == e~\rblot`.

### Added

- WYSIWYG line-break support for algebra and set operators. Natural newline
  or explicit `\` continuation is now recognised after `bowtie`, `cross`,
  `div`, `intersect`, `union`, `setminus`, `++`, `group`, and `ungroup`.
  In display position the broken chain wraps in `\begin{array}{l}...\end{array}`;
  inside a `where` predicate `\\` is emitted inline (same form as `land`/`lor`,
  fuzz type-checks cleanly). Example:

  ```text
  pi[name, displacement, numGuns](Class bowtie
    Ship bowtie
    rho[ship as name](pi[ship](sigma[battle = 'Guadalcanal'](Outcome))))
  ```

  Note: a `\` continuation cannot follow `setminus` directly because `\` is
  also the `setminus` token; break *before* `setminus` instead.

- `pk` declaration prefix for primary-key underlining (Phase 2.1 revised).
  `pk attrname : Type` in a schema or axdef body sets `is_primary_key=True`
  on the `Declaration` AST node; the generator emits `\underline{attrname}`
  using the LaTeX kernel command (no fuzz.sty dependency).  Composite primary
  keys use two `pk` lines; comma-separated names share one `pk` line.  24 new
  tests in `tests/test_14_relational_databases/test_primary_keys.py`.
  New example `examples/14_relational_databases/primary_keys.txt`.

### Removed (within-branch churn — no impact on prior-release users)

- **`relvars` declaration paragraph**: added in Phase 2.1 (commit
  `4bb13d9`), replaced by the `pk` annotation in commit `d93e061`. Did
  not ship in any released version. No migration needed for prior-release
  users (`.txt` from a released version cannot use `relvars`).

- **`:=` assignment operator**: added in commit `f640074` (Phase 2.2),
  dropped in commit `0422bd4` in favour of the smart `==` abbreviation.
  Did not ship in any released version. No migration needed.

### Added (earlier releases)

- Schema calculus operators (Phase 3.2): Z RM §3.11 composition (`;`),
  piping (`>>`), hiding (`hide`), and projection (`project`) on the RHS of
  `defs` paragraphs.  Three new `TokenType` members: `PIPE_PIPE` (`>>`),
  `HIDE`, and `PROJECT`; `hide` and `project` added to `KEYWORD_TO_TOKEN` and
  `RESERVED_WORDS`.  `>>` lexed as `PIPE_PIPE` only when preceded by
  whitespace to avoid conflict with closing RANGLE in nested sequence literals.
  Four new frozen AST dataclasses: `SchemaCompose(left, right)`,
  `SchemaPipe(left, right)`, `SchemaHide(schema, names)`, and
  `SchemaProject(left, right)`, all added to the `Expr` union.  Parser flag
  `_in_schema_expr_context` gates the new precedence cascade
  (`_parse_schema_pipe` → `_parse_schema_compose` →
  `_parse_schema_project_hide`), which is entered only from
  `_parse_horiz_def_rhs`; `_parse_parenthesized_expr_or_tuple` respects the
  flag so that `(S ; T) hide (x)` works correctly.  SEMICOLON remains a
  declaration separator inside `axdef`, `schema`, and `gendef` bodies
  unchanged.  Generator methods emit `\semi`, `\pipe`, `\hide`, `\project`
  (defined in `fuzz.sty` lines 295–302; no preamble change needed).  34 new
  tests in `tests/test_15_schema_calculus/`; new examples in
  `examples/15_schema_calculus/`; tutorial `docs/tutorials/12_schema_calculus.md`
  added; `USER_GUIDE.md`, `MISSING_FEATURES.md`, and `DESIGN.md` (ADR)
  updated.

- GROUP / UNGROUP operators (Phase 4.1): Date's nested-relation operators.
  `R group ({A, B, ...} as alias)` bundles attributes into a relation-valued
  attribute; `R ungroup alias` flattens it back.  Both operators use
  `\mathop{\mathrm{GROUP}}` / `\mathop{\mathrm{UNGROUP}}` per jms round-2
  refinement — `\mathop{}` gives proper binary-operator spacing without
  requiring `amsmath` (LaTeX kernel only).  Two new `TokenType` members
  (`GROUP`, `UNGROUP`); both added to `KEYWORD_TO_TOKEN` and `RESERVED_WORDS`
  in the lexer.  Two new frozen dataclasses: `Group(relation, attrs, alias)`
  and `Ungroup(relation, alias)`, both added to the `Expr` union.  Parser
  extends `_parse_cross` to handle both forms; helper methods
  `_parse_group_rhs` and `_parse_ungroup_rhs` are extracted subparsers.
  Generator methods `_generate_group` and `_generate_ungroup` emit the
  `\mathop{\mathrm{...}}` form; attribute and alias names pass through
  `_emit_attr_name` for relvar wrapping.  28 new tests (lexer, parser,
  generator, 4 negative cases with message + line + column, acceptance probe,
  regression); new example `examples/14_relational_databases/group_ungroup.txt`;
  tutorial section added; `USER_GUIDE.md` updated; `DESIGN.md` ADR added.

- Schema renaming (Phase 3.1): `S[old/new, ...]` per Z RM §3.11.  Renders
  as `S[old/new, ...]` in math mode — literal brackets and slashes, no
  special macro.  Disambiguation from generic instantiation `S[X]` (Phase
  1.1) uses a depth-0 scan for `/` inside the brackets before committing:
  any `SLASH` at depth 0 triggers rename parsing; absence triggers generic
  parsing.  New `SLASH` token type; lexer falls through to it after the
  existing `/=` and `/in` checks.  New `SchemaRename(schema: Expr,
  pairs: list[tuple[str, str]])` AST node added to `ast_nodes.py` and the
  `Expr` union.  `_parse_schema_rename_or_generic` routine in parser
  replaces the old generic instantiation loop in `_parse_postfix`;
  `_parse_generic_instantiation` and `_parse_schema_rename` are extracted
  subparsers.  Decoration interaction: `S'[a/b]` renames the primed schema
  (Phase 0 lexer bakes decoration into the identifier token value — no
  extra handling required).  Decorated component names in pairs (`S[a'/b]`,
  `S[a/b']`) also work.  25 new tests (AST, disambiguation, decorated
  schema, decorated pair names, acceptance probe, generator, 5 negative
  cases with message + line + column); new example
  `examples/10_schemas/schema_rename.txt`; tutorial 09 "Schema Renaming"
  section added; `USER_GUIDE.md` updated; `DESIGN.md` ADR added.

- Z binding brackets (Phase 2.3): `{| label == expr, ... |}` per Z RM §3.7.
  Renders as `\lblot label == expr, \ldots \rblot`; macros are defined in both
  `fuzz.sty` (lines 275-276) and `zed-lbr.sty`/`zed-cm.sty` — no preamble
  change.  Two new token types: `LBIND` (`{|`) and `RBIND` (`|}`), both
  two-character; lexer inserts `{|` check before bare `{` and `|}` check
  before bare `|`, after all existing multi-char `|` prefixes.  New `Binding`
  AST node with `pairs: list[tuple[str, Expr]]`; added to `Expr` union.
  Parser dispatches at atom level; `==` reuses the `ABBREV` token
  (context-disambiguated by position inside `{| ... |}`).  Components are
  comma-separated per Z RM §3.7; semicolons raise a clear error.  Empty
  binding `{| |}` accepted.  Generator emits via `_emit_attr_name` so
  declared relvars receive `\mathrm{}` wrapping in both labels and values.
  `RBIND` added to `safe_followers` in `_parse_postfix` to allow field
  projections like `s.name` before `|}`.  Set comprehension extended to
  support `;`-separated variable-type pairs (`s : Ship; c : Class`) for
  multi-typed set comprehension queries; `_parse_set_expression` skips leading newlines
  for multi-line comprehensions; closing `}` also skips newlines.  38 new
  tests (lexer, parser, generator, acceptance probes, negative cases,
  regression); new example `examples/14_relational_databases/bindings.txt`;
  Tutorial 11 extended with Z Binding Calculus section; `USER_GUIDE.md`
  binding subsection added; `DESIGN.md` ADR added.

- Relational algebra operators (Phase 2.2): `sigma[pred](R)` (restriction,
  `\sigma`), `pi[A, B](R)` (projection, `\pi`), `rho[A as B](R)` (renaming,
  `\rho`), `R bowtie S` (natural join, `\bowtie`), `R bowtie [p] S`
  (theta-join, `\bowtie_{p}`), `R div S` (division, `\div`), `T := R`
  (assignment, `\begin{zed}T := R\end{zed}`).  All use kernel LaTeX — no
  preamble change.  Relvar wrapping (`\mathrm{}`) fires correctly in all
  algebra contexts including subscripts and argument positions.  Six new AST
  nodes (`Restrict`, `Project`, `Rename`, `NaturalJoin`, `Divide`,
  `Assignment`); six new token types (`SIGMA`, `PI`, `RHO`, `BOWTIE`, `DIV`,
  `ASSIGN`); `:=` lexed before `::=` to avoid conflict; `bowtie` and `div`
  added to infix stop set.  69 new tests; new example
  `examples/14_relational_databases/algebra_basics.txt`; Tutorial 11 extended
  with Relational Algebra section; `USER_GUIDE.md` Relational Algebra subsection
  added; `DESIGN.md` ADR added.

- Relvar declaration paragraph (`relvars`) for relational database support (Phase 2.1).  `relvars Class, Ship, Battle, Outcome` declares relation
  variables; each declared name renders upright (`\mathrm{Name}`) wherever it
  appears as an identifier in a math context.  Attribute names (undeclared
  identifiers) stay italic (default math mode).  Decoration-outside rule:
  `Class'` → `\mathrm{Class}'`; subscripts: `Class_1` → `\mathrm{Class}_1`.
  Generator pre-walks the AST in O(N) to collect all `Relvars` items into
  `relvar_set: frozenset[str]`; each identifier emission is then an O(1)
  membership test.  New `RELVARS` token type, `Relvars` AST node, parser
  dispatch with full error handling (empty list, leading/trailing/double comma,
  missing comma).  `relvars` added to `KEYWORD_TO_TOKEN` and `RESERVED_WORDS`
  (decoration forbidden).  36 new tests; new example
  `examples/14_relational_databases/relvars_basic.txt`; Tutorial 11 added;
  `USER_GUIDE.md` "Relational Databases" section added.

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
  `in?`, `out!`, `x?'`, `s''`). This is the foundational change for Z schema
  operation notation (before/after state, inputs, outputs).
- String literal lexeme — a single-quoted value (`'sunk'`, `'survived'`) is
  now tokenised as `STRING` and parsed as `StringLit`. The generator emits the
  Z-convention quoting: `` `value' `` in fuzz mode and `\text{`value'}` in
  standard LaTeX mode. This is the foundational change for relational database
  notation support.
- Comma-separated variable lists in schema, axdef, and gendef declaration
  blocks (`count, count' : N` declares two variables sharing one type).
- Two new getting-started examples: `decorated_identifiers.txt` (schema
  decoration probe) and `string_literals.txt` (string literal syntax).
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
- Reference card (`docs/reference.pdf`) with proof examples
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
