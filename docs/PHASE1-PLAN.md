# Phase 1 Plan — Family-Line Split of `latex_gen.py` and `parser.py`

**Status: ✅ done, 2026-05-25.** Operational plan for the Phase 1
refactor outlined in [DESIGN-ROADMAP.md](DESIGN-ROADMAP.md).
Behaviour does not change.  Only file boundaries moved.

Delivered as twelve commits on branch
`refactor/phase1-family-split`: Move 0 (dispatch infrastructure) +
nine numbered batches + the IO-contract tooling commit + this
plan's own close-out edit.  Each batch is independently revertible
via `git revert`.

**Final line counts.**

| File | main (baseline) | after Phase 1 | reduction |
|---|---|---|---|
| `src/txt2tex/latex_gen.py` | 6,864 | 598 | 91.3% |
| `src/txt2tex/parser.py` | 6,367 | 846 | 86.7% |

**Verification.** Every gate green:

- `make check` — lint + markdown + format + mypy + pyright + 4,700
  unit tests.
- `make test-e2e` — 159 / 159 `examples/**/*.tex` fixtures
  byte-identical.
- `make refactor-diff` — 190 / 190 `examples/` + `tests/bugs/`
  outputs byte-identical against `main`.

## Goal

Replace the two monolithic source files with directory trees whose
files match the construct-family boundaries a reader expects.  At the
end of the phase:

- `src/txt2tex/codegen/` contains the former `latex_gen.py` split into
  ~10 files.
- `src/txt2tex/parser/` contains the former `parser.py` split into
  ~10 files.
- `make check` and `make test-e2e` pass at every gate.
- Every committed move is reversible by `git revert` without touching
  any subsequent commit.

## Discipline — formal refactoring only

Every change in this phase must satisfy Fowler's definition of a
refactoring: **a change to the internal structure of software that
preserves observable behaviour**.  Concretely, that restricts Phase 1
to two named refactorings from the catalog:

- **Move Method** ([Fowler, Refactoring 2/e p. 162](https://refactoring.com/catalog/moveFunction.html)) —
  a method is moved from one class to another.  The original method
  may be replaced by a delegation, or removed entirely if no caller
  remains.  In this phase, every handler move is a Move Method from
  the monolithic `LaTeXGenerator` / `Parser` class to a topic-cohesive
  mixin class, with the final class inheriting the mixin so the
  composite remains call-compatible with all existing callers.

- **Extract Class** ([Fowler, Refactoring 2/e p. 182](https://refactoring.com/catalog/extractClass.html)) —
  a coherent subset of a class's methods (and shared private fields,
  if any) is moved into a new class.  The mixin classes in this phase
  are extractions: each construct family becomes a new class
  (`SchemaCodegen`, `AlgebraParser`, …) holding only methods related
  to that family.

Anything outside these two named refactorings is **out of scope** for
Phase 1.  Specifically:

- No **Rename Method**.  Method names stay byte-identical, even if a
  current name looks awkward in its new file.  Renames happen in a
  separate commit after the phase closes.
- No **Change Signature**.  Parameter lists, return types, default
  values, type annotations — all preserved.
- No **Extract Method** or **Inline Method**.  Method bodies are
  copied verbatim into the new file; nothing is split out or merged
  in.
- No **Replace Magic Literal**, no docstring rewrites, no comment
  cleanup, no formatting changes beyond whatever `ruff format`
  re-emits identically.
- No **Introduce Parameter Object**, no **Replace Conditional with
  Polymorphism**, no behaviour-equivalent algorithmic changes.

This discipline is what makes the e2e fixture comparison meaningful as
a verification gate.  If a `.tex` byte differs after a move, the move
violated the discipline — it was not a pure Move Method or Extract
Class.  Stop, identify the deviation, and either revert the deviation
or document it as an intentional behavioural change requiring fixture
regeneration *and* a separate commit.

## Principles

1. **Behaviour is unchanged.** The e2e fixture comparison is the test
   of this — if the generated `.tex` differs byte-for-byte from the
   committed fixture, the move broke something.  Regenerate the
   fixtures only when the *generator* semantics change deliberately;
   this phase has no such changes.
2. **Mixins over free functions.** The handlers in `latex_gen.py` and
   `parser.py` carry state on `self` (`self._in_z_paragraph`,
   `self._in_relational_context`, `self._overflow_warnings`, etc.).
   The lowest-risk move is to extract handlers into mixin classes
   that the final `LaTeXGenerator` and `Parser` inherit from.  All
   state stays on the final class; mixins are organisation only.
3. **Dispatch by import side-effect.** `latex_gen.py` already uses
   `@generate_expr.register(NodeType)` on methods of the generator
   class — the underlying mechanism is `functools.singledispatchmethod`
   (single-dispatch dispatch table bound to a method, not a free
   function).  The decorator registers handlers when the module is
   imported.  As long as `codegen/__init__.py` imports every
   submodule (and each submodule defines its handlers as methods on
   a mixin class), every handler is reachable.
4. **One thematic file per move.**  A move is the extraction of one
   construct family into one new file.  Smaller moves are easier to
   review and revert.
5. **Gate every three moves.**  Run `make check` and `make test-e2e`
   after each batch of three moves.  Any failure stops the phase
   until it is understood.

## Setup (Move 0 — preflight)

Before any code moves:

1. **Baseline.**  On a clean `main`, run:

   ```bash
   make check
   make test-e2e
   ```

   Both must be green.  Record `git rev-parse HEAD` as the baseline.

2. **Branch.** `git checkout -b refactor/phase1-family-split` from
   the baseline.

3. **Create the directory shells:**

   ```bash
   mkdir -p src/txt2tex/codegen src/txt2tex/parser_pkg
   touch src/txt2tex/codegen/__init__.py
   touch src/txt2tex/parser_pkg/__init__.py
   ```

   Note: `parser/` collides with `src/txt2tex/parser.py`; use
   `parser_pkg/` as a temporary name during the move, then rename
   to `parser/` after `parser.py` is empty.  Same for `codegen/`
   versus `latex_gen.py` — alternatively, leave the directory name
   as `latex_gen/` for the entire phase.  Pick one before starting
   and stick with it.

4. **Decide the dispatch location.**  The `singledispatchmethod`
   table must live in one well-known place.  Recommendation:
   `codegen/_dispatch.py` defines a `_Dispatcher` base class whose
   single method `generate_expr` carries the dispatch decorator.
   Every mixin file imports `_Dispatcher` and registers handlers
   against it via `@_Dispatcher.generate_expr.register(NodeType)`.
   The final `LaTeXGenerator` class lives in `codegen/__init__.py`
   and inherits both the mixins and `_Dispatcher`.

5. **Smoke-test the mixin pattern.**  Before doing real moves,
   verify the mixin composition works:

   ```python
   # codegen/_dispatch.py
   from functools import singledispatchmethod
   class _Dispatcher:
       @singledispatchmethod
       def generate_expr(self, node, parent=None): ...
   ```

   ```python
   # codegen/__init__.py
   class LaTeXGenerator(SchemaCodegen, AlgebraCodegen, ..., _Dispatcher):
       ...
   ```

   Move ONE handler to a mixin file first, run `make check`, and
   confirm it dispatches correctly.  Roll forward only after this
   smoke test passes.

## Phase 1A — `latex_gen.py` split (Moves 1–11)

Each "Move N" creates one new file under `codegen/` and removes the
corresponding methods from `latex_gen.py`.  Imports are added to
`codegen/__init__.py` so the mixin composition picks up the new
class.

### Batch 1 (Moves 1–3) — paragraphs, schemas, proofs

- **Move 1** → `codegen/paragraphs.py`
  Handlers for: `GivenType`, `FreeType`, `Abbreviation`, `AxDef`,
  `GenDef`, `ZedBlock`, `SyntaxBlock`.

- **Move 2** → `codegen/schemas.py`
  Handlers for: `Schema`, schema body / where-clause emission,
  `HorizDef`, schema-calculus operators inside `defs` RHS
  (`;`, `>>`, `hide`, `project`).

- **Move 3** → `codegen/proofs.py`
  Handlers for: `ProofTree`, `InfRule`, `ArgueChain` (covers
  `ARGUE:`, `EQUIV:`, `EQUAL:`).

**Gate 1.** `make check && make test-e2e`.  Commit the batch as a
single commit `refactor(codegen): split paragraphs/schemas/proofs
into codegen/ submodules`.

### Batch 2 (Moves 4–6) — algebra, expressions, types

- **Move 4** → `codegen/algebra.py`
  Handlers for: `Restrict`, `Project`, `RelationRename`,
  `NaturalJoin`, `Divide`, `Group`, `Ungroup`, `GroupAggregate`.

- **Move 5** → `codegen/expressions.py`
  Handlers for: `BinaryOp`, `UnaryOp`, `FunctionApp`, `Quantifier`,
  `Lambda`, `Conditional`, `SetComprehension`, `GuardedCases`,
  `GuardedBranch`, `Range`, `Number`, `Identifier`.

- **Move 6** → `codegen/types.py`
  Handlers for: `FunctionType`, `RelationType`,
  `GenericInstantiation`, free-type constructor emission.

**Gate 2.** `make check && make test-e2e`.  Commit as
`refactor(codegen): split algebra/expressions/types into codegen/
submodules`.

### Batch 3 (Moves 7–9) — bindings, text blocks, overflow

- **Move 7** → `codegen/bindings.py`
  Handlers for: `Binding` (`{|...|}` literal), `Theta`,
  multi-typed comprehension with binding.

- **Move 8** → `codegen/text_blocks.py`
  Handlers for: `TextBlock` (`TEXT:`), `PureText` (`PURETEXT:`),
  `LatexBlock` (`LATEX:`), `BBlock` (`B:`), `TruthTable`,
  `Parts`, `PageBreak`, `LineBreak`, `Section`, `Subsection`.

- **Move 9** → `codegen/overflow.py`
  Functions: `_check_overflow`, `get_warnings`, `emit_warnings`,
  `clear_warnings`, `DEFAULT_OVERFLOW_THRESHOLD`.

**Gate 3.** `make check && make test-e2e`.  Commit as
`refactor(codegen): split bindings/text-blocks/overflow into codegen/
submodules`.

### Batch 4 (Moves 10–11) — fuzz routing, paren policy

- **Move 10** → `codegen/fuzz_routing.py`
  Helpers: `_DAT_EXPRESSION_TYPES`, `_expression_contains_dat_construct`,
  `_should_route_to_inline_math`, inline-math wrapping helpers.

- **Move 11** → `codegen/paren_policy.py`
  Class variables and helpers: `PRECEDENCE`, `UNARY_PRECEDENCE`,
  `RIGHT_ASSOCIATIVE`, `BINARY_OPS`, `_needs_parens`,
  `_quantifier_needs_parens`, `_map_binary_operator`.

  This is the only batch with two moves rather than three — these
  two helpers are the foundation Phase 2 will build on, and moving
  them together keeps the related code adjacent.

**Gate 4.** `make check && make test-e2e`.  Commit as
`refactor(codegen): extract fuzz routing and paren policy modules`.

### Batch 5 (Moves A, B) — Phase 1A close-out: atoms and text pipeline

Original Batches 1–4 leave `latex_gen.py` at ~2,500 lines.  The
plan's "~200 lines or fewer" target requires two further moves
that were not enumerated in the original Phase 1A listing:

1. Nine simple expression handlers
   (`StringLit`, `SetLiteral`, `Subscript`, `Superscript`, `Tuple`,
   `RelationalImage`, `SequenceLiteral`, `TupleProjection`,
   `BagLiteral`) that the original Batch 2 (Move 5) listing did not
   enumerate.  ~250 lines.
2. The plain-text → LaTeX processing pipeline that implements
   `TEXT:` / `PURETEXT:` / `LATEX:` emission.  ~1,500 lines, ~25
   helpers, two `ClassVar` allow-lists.  Self-contained subsystem:
   takes a `str`, returns a `str`.

These two moves are gated together as Batch 5.

- **Move A** → `codegen/expressions.py` (append; no new file)
  Handlers for: `StringLit`, `SetLiteral`, `Subscript`,
  `Superscript`, `Tuple`, `RelationalImage`, `SequenceLiteral`,
  `TupleProjection`, `BagLiteral`.  Same byte-identical Move
  Method discipline; the existing `_ExpressionsCodegen` mixin
  grows by 9 handlers.

- **Move B** → `codegen/text_pipeline.py` (new file)
  Extract the entire ASCII-to-LaTeX text pipeline as one cohesive
  unit:

  - **Orchestrator** — `_process_paragraph_text`
  - **Operator conversion** — `_convert_operators_bare`,
    `_convert_unicode_symbols`, `_convert_comparison_operators`,
    `_convert_sequence_literals`, `_convert_operators_to_latex`
  - **Dollar-math handling** — `_pre_sanitise_dollars`,
    `_restore_dollar_sanitise`, `_process_explicit_dollar_math`
  - **Pattern processors** — `_process_citations`,
    `_process_manual_markup`, `_process_logical_formulas`,
    `_process_parenthesized_logic`, `_process_standalone_keywords`,
    `_process_superscripts`, `_process_relational_image`,
    `_process_set_expressions`, `_process_quantifiers`,
    `_process_type_declarations`, `_process_function_applications`,
    `_process_simple_expressions`, `_process_inline_math`
  - **LaTeX command policy** — `_classify_latex_commands`,
    `_ALLOWED_LATEX_COMMANDS`, `_BLOCKED_LATEX_COMMANDS`
  - **Balanced-bracket finders** — `_find_balanced_braces`,
    `_find_balanced_parens`, `_find_balanced_angles`
  - **Text escaping** — `_replace_outside_math`,
    `_escape_underscores_outside_math`,
    `_escape_special_chars_outside_math`, `_escape_latex`,
    `_escape_latex_text`

  This is the largest single extract in Phase 1.  Splitting it is
  not worth the churn: the pipeline is leaf-cohesive (every helper
  calls only its peers and a few generic `re`/`str` operations)
  and is consumed by exactly three callers (`_generate_paragraph`,
  `_generate_pure_paragraph`, and `_generate_part`), all of which
  live in `text_blocks.py` and reach into the pipeline through
  `self._process_paragraph_text`.

**Gate 5 (Phase 1A close-out).** `make check && make test-e2e &&
make refactor-diff` must all pass.  Commit as a single batch:
`refactor(codegen): close out Phase 1A — atoms and text pipeline`.

### Finalisation of Phase 1A

After Move B, `latex_gen.py` should be ~250 lines or fewer — it
contains only the `LaTeXGenerator` class shell, its `__init__`,
top-level orchestration (`generate_document`, `generate_fragment`,
`_generate_document_items_with_consolidation`, `_generate_zed_content`),
the three `_has_line_breaks*` helpers, the small zed-mode
formatting helpers (`_get_*_separator`, `_get_type_latex`,
`_get_closure_operator_latex`, `_format_multiword_identifier`,
`_get_indentation`), and the three operator-table `ClassVar`s that
are still referenced from the orchestrator (`UNARY_OPS`,
`QUANTIFIERS`, `_FUZZ_FUNCTION_LIKE_UNARY`).

Optional: rename `latex_gen.py` to `codegen/__init__.py` proper
and update every import site.  Defer this rename to a final
clean-up commit so the diff stays mechanical.

## Phase 1B — `parser.py` split (Moves 12–22)

The parser uses recursive-descent: each rule method calls its
neighbours (`_parse_expr` → `_parse_iff` → `_parse_implies` → … →
`_parse_atom`).  When methods move to mixins, the calls between
them still resolve through `self`, so the call graph is preserved
without explicit re-wiring.

### Batch 5 (Moves 12–14) — paragraphs, schemas, proofs

- **Move 12** → `parser_pkg/paragraphs.py`
  Rules for: `_parse_given`, `_parse_free_type`, `_parse_abbreviation`,
  `_parse_axdef`, `_parse_gendef`, `_parse_zed_block`,
  `_parse_syntax_block`.

- **Move 13** → `parser_pkg/schemas.py`
  Rules for: `_parse_schema`, `_parse_schema_body`,
  `_parse_where_clause`, `_parse_horiz_def`, `_parse_schema_calculus`,
  `_parse_schema_rename_or_generic`.

- **Move 14** → `parser_pkg/proofs.py`
  Rules for: `_parse_proof_tree`, `_parse_infrule`,
  `_parse_argue_chain` (covers ARGUE / EQUIV / EQUAL).

**Gate 5.** `make check && make test-e2e`.  Commit.

### Batch 6 (Moves 15–17) — algebra, expressions, types

- **Move 15** → `parser_pkg/algebra.py`
  Rules for: `_parse_restrict` (sigma), `_parse_project` (pi),
  `_parse_relation_rename` (R[B/A]), `_parse_natural_join`,
  `_parse_divide`, `_parse_group`, `_parse_ungroup`,
  `_parse_group_aggregate`.

- **Move 16** → `parser_pkg/expressions.py`
  Rules for: `_parse_expr`, `_parse_iff`, `_parse_implies`,
  `_parse_lor`, `_parse_land`, `_parse_lnot`, `_parse_comparison`,
  `_parse_set_op`, `_parse_cross`, `_parse_intersect`,
  `_parse_additive`, `_parse_multiplicative`, `_parse_range`,
  `_parse_unary`, `_parse_postfix`, `_parse_atom`, quantifier
  parsers, lambda parser, conditional parser, set-comprehension
  parser.

  This is the biggest move (the expression parser dominates the
  parser by line count).  If it pushes the batch's diff over
  ~2,000 lines, split it into `expressions/core.py` and
  `expressions/quantifiers.py` as a preparatory move first.

- **Move 17** → `parser_pkg/types.py`
  Rules for: `_parse_function_type`, `_parse_relation_type`,
  `_parse_generic_instantiation`, `_parse_free_type_constructor`,
  `_parse_generic_params`.

**Gate 6.** `make check && make test-e2e`.  Commit.

### Batch 7 (Moves 18–20) — bindings, text blocks, postfix

- **Move 18** → `parser_pkg/bindings.py`
  Rules for: `_parse_binding_literal` (`{|...|}`), `_parse_theta`,
  `_parse_multi_typed_comprehension`.

- **Move 19** → `parser_pkg/text_blocks.py`
  Rules for: `_parse_text_block`, `_parse_puretext_block`,
  `_parse_latex_block`, `_parse_b_block`, `_parse_truth_table`,
  `_parse_parts_directive`, `_parse_pagebreak`, `_parse_linebreak`,
  `_parse_section`, `_parse_subsection`.

- **Move 20** → `parser_pkg/postfix.py`
  Postfix-handling helpers: `_parse_postfix` and its branches for
  function application, generic instantiation, relation rename,
  schema rename.  Co-located with the relational-context flag
  threading.

**Gate 7.** `make check && make test-e2e`.  Commit.

### Batch 8 (Moves 21–22) — lexer-state, error-formatting

- **Move 21** → `parser_pkg/lexer_state.py`
  Token-cursor helpers: `_current`, `_peek_ahead`, `_advance`,
  `_match`, `_skip_newlines`, `_bracket_contains_slash`,
  `_is_operand_start`, `_at_end`.  These are the I/O of the parser
  and are heavily called from every rule.

- **Move 22** → `parser_pkg/errors.py`
  Error-construction helpers: `_unexpected_token`, `_raise_*`,
  position tracking.  Already partly in `errors.py`; this move
  consolidates parser-side error construction with the existing
  `ErrorFormatter`.

**Gate 8.** `make check && make test-e2e`.  Commit.

### Finalisation of Phase 1B

After Move 22, `parser.py` should be ~150 lines or fewer — the
`Parser` class shell, its `__init__`, and the `parse()` entry
method.  Same optional rename as Phase 1A: defer to a final
clean-up commit.

## Phase 1 close-out

After all 8 gates pass:

1. **Verify the acceptance criteria** from DESIGN-ROADMAP.md:
   - `make check` and `make test-e2e` both pass.
   - No file in `src/txt2tex/` exceeds 1,500 lines.
     (Verify with `find src/txt2tex -name '*.py' -exec wc -l {} + |
     sort -rn | head -5`.)
   - Tests import from the new layout (the test suite should be
     unchanged — the public API has not moved).
   - `git diff main..HEAD --stat` shows file-move-dominated diffs.
     Line-counts per family file should match the methods extracted;
     spurious deltas indicate the move accidentally edited content.

2. **Optional rename pass** for cleanliness:
   - `git mv src/txt2tex/latex_gen.py src/txt2tex/codegen/_orchestrator.py`
     (or fold the shell into `codegen/__init__.py`).
   - Same for `parser.py` → `parser_pkg/_orchestrator.py`, then
     `git mv src/txt2tex/parser_pkg src/txt2tex/parser` once
     `parser.py` is gone.
   - Update every import site:

     ```bash
     grep -rn "from txt2tex.latex_gen import" src/ tests/
     grep -rn "from txt2tex.parser import" src/ tests/
     ```

   - This is one commit at the end.  Keep it separate from the
     mechanical moves.

3. **Update `docs/DESIGN-ROADMAP.md`** — mark Phase 1 done; record
   the new line-count table for the construct-family files.

4. **Open the PR.**  Title: `refactor: family-line split of
   latex_gen.py and parser.py (Phase 1)`.  Body: one paragraph
   stating "behaviour unchanged, e2e fixtures byte-for-byte
   identical" plus the commit list.  No release needed; the
   change is invisible to users.

## Per-gate checklist

Run this at every numbered gate.  Any failure stops the phase.

```bash
# Both gates must pass cleanly.  The e2e suite collects examples
# dynamically; the count grows as new examples are added.
make check            # lint + lint-md + format-check + type + type-pyright + test
make test-e2e         # every example .txt → .tex byte-for-byte

# Sanity check on what just moved.  Each batch is one commit, so
# inspect the single most recent commit:
git show --stat       # file moves should dominate
```

`make test` is included in `make check` (the `test` target is a
dependency), so explicitly running `make test` separately is
redundant — the gate above covers it.  If you prefer the explicit
form, `make test && make check && make test-e2e` is equivalent for
this phase.

## Rollback strategy

Each gate-marked commit is one batch — three moves in most batches,
two in Gates 4 (Moves 10–11) and 8 (Moves 21–22).  If a future
discovery reveals a bug introduced by the split:

- `git revert <batch-commit>` reverts that batch cleanly.
- Subsequent batches do not depend on each other for correctness
  (only for tidiness), so a mid-phase revert leaves the codebase in
  a still-shippable mixed state.

Avoid `git reset --hard` in the middle of the phase — the commits
are the audit trail of which extractions were done.

## What this plan is not

It is not an optimisation pass.  No method is renamed, no signature
changes, no error-message text is touched, no docstrings are
rewritten.  Anything that would show up as `+`/`-` rather than
"renamed" in `git diff --stat` is out of scope for Phase 1.  Save
that work for Phases 2 and 3.
