# Phase 1 Plan — Family-Line Split of `latex_gen.py` and `parser.py`

Operational plan for the Phase 1 refactor outlined in
[DESIGN-ROADMAP.md](DESIGN-ROADMAP.md).  Behaviour does not change.
Only file boundaries move.

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
   of this — if a `.tex` file's byte count shifts, the move broke
   something.  Regenerate the fixtures only when the *generator*
   semantics change deliberately; this phase has no such changes.
2. **Mixins over free functions.** The handlers in `latex_gen.py` and
   `parser.py` carry state on `self` (`self._in_z_paragraph`,
   `self._in_relational_context`, `self._overflow_warnings`, etc.).
   The lowest-risk move is to extract handlers into mixin classes
   that the final `LaTeXGenerator` and `Parser` inherit from.  All
   state stays on the final class; mixins are organisation only.
3. **Dispatch by import side-effect.** `latex_gen.py` already uses
   `@generate_expr.register(NodeType)`.  This decorator registers
   handlers when the module is imported.  As long as
   `codegen/__init__.py` imports every submodule, every handler is
   reachable.
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

4. **Decide the dispatch import location.**  The `@singledispatch`
   dispatcher must live in one well-known place.  Recommendation:
   `codegen/_dispatch.py` exports `generate_expr`; every handler
   file imports it.  The `LaTeXGenerator` class lives in
   `codegen/__init__.py` and composes the mixins.

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

### Finalisation of Phase 1A

After Move 11, `latex_gen.py` should be ~200 lines or fewer — it
contains only the `LaTeXGenerator` class shell, its `__init__`, and
top-level orchestration (`generate_document`, `generate_expr` entry,
state initialisation).  Optional: rename `latex_gen.py` to
`codegen/__init__.py` proper and update every import site.  Defer
this rename to a final clean-up commit so the diff stays mechanical.

## Phase 1B — `parser.py` split (Moves 12–22)

The parser uses recursive-descent: each rule method calls its
neighbours (`_parse_expr` → `_parse_iff` → `_parse_implies` → … →
`_parse_atom`).  When methods move to mixins, the calls between
them still resolve through `self`, so the call graph is preserved
without explicit re-wiring.

### Batch 5 (Moves 12–14) — paragraphs, schemas, proofs

- **Move 12** → `parser/paragraphs.py`
  Rules for: `_parse_given`, `_parse_free_type`, `_parse_abbreviation`,
  `_parse_axdef`, `_parse_gendef`, `_parse_zed_block`,
  `_parse_syntax_block`.

- **Move 13** → `parser/schemas.py`
  Rules for: `_parse_schema`, `_parse_schema_body`,
  `_parse_where_clause`, `_parse_horiz_def`, `_parse_schema_calculus`,
  `_parse_schema_rename_or_generic`.

- **Move 14** → `parser/proofs.py`
  Rules for: `_parse_proof_tree`, `_parse_infrule`,
  `_parse_argue_chain` (covers ARGUE / EQUIV / EQUAL).

**Gate 5.** `make check && make test-e2e`.  Commit.

### Batch 6 (Moves 15–17) — algebra, expressions, types

- **Move 15** → `parser/algebra.py`
  Rules for: `_parse_restrict` (sigma), `_parse_project` (pi),
  `_parse_relation_rename` (R[B/A]), `_parse_natural_join`,
  `_parse_divide`, `_parse_group`, `_parse_ungroup`,
  `_parse_group_aggregate`.

- **Move 16** → `parser/expressions.py`
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

- **Move 17** → `parser/types.py`
  Rules for: `_parse_function_type`, `_parse_relation_type`,
  `_parse_generic_instantiation`, `_parse_free_type_constructor`,
  `_parse_generic_params`.

**Gate 6.** `make check && make test-e2e`.  Commit.

### Batch 7 (Moves 18–20) — bindings, text blocks, postfix

- **Move 18** → `parser/bindings.py`
  Rules for: `_parse_binding_literal` (`{|...|}`), `_parse_theta`,
  `_parse_multi_typed_comprehension`.

- **Move 19** → `parser/text_blocks.py`
  Rules for: `_parse_text_block`, `_parse_puretext_block`,
  `_parse_latex_block`, `_parse_b_block`, `_parse_truth_table`,
  `_parse_parts_directive`, `_parse_pagebreak`, `_parse_linebreak`,
  `_parse_section`, `_parse_subsection`.

- **Move 20** → `parser/postfix.py`
  Postfix-handling helpers: `_parse_postfix` and its branches for
  function application, generic instantiation, relation rename,
  schema rename.  Co-located with the relational-context flag
  threading.

**Gate 7.** `make check && make test-e2e`.  Commit.

### Batch 8 (Moves 21–22) — lexer-state, error-formatting

- **Move 21** → `parser/lexer_state.py`
  Token-cursor helpers: `_current`, `_peek_ahead`, `_advance`,
  `_match`, `_skip_newlines`, `_bracket_contains_slash`,
  `_is_operand_start`, `_at_end`.  These are the I/O of the parser
  and are heavily called from every rule.

- **Move 22** → `parser/errors.py`
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
   - Same for `parser.py` → `parser/_orchestrator.py`.
   - Update every import site (`grep -rn "from txt2tex.latex_gen
     import"`).
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
# Both gates must pass cleanly.
make check            # lint + lint-md + format-check + type + type-pyright + test
make test-e2e         # 159 fixture comparisons, byte-for-byte

# Sanity check on what moved.
git diff --stat HEAD~3..HEAD   # file moves should dominate
```

`make test` is included in `make check` (the `test` target is a
dependency), so explicitly running `make test` separately is
redundant — the gate above covers it.  If you prefer the explicit
form, `make test && make check && make test-e2e` is equivalent for
this phase.

## Rollback strategy

Each gate-marked commit is one batch of three moves.  If a future
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
