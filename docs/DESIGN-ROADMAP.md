# Design Roadmap

A working note on where the txt2tex codebase is, where production
compilers in its weight class have gone, and what the next refactors
should be.  Not a plan of record; an alignment document so future
work has a shared yardstick.

## Where we are today

The pipeline is correctly decomposed at the top level:

```text
source.txt → Lexer → tokens → Parser → AST → LaTeXGenerator → output.tex
```

Each stage has a clear input and output type, and the boundaries
between stages are clean: nothing in `latex_gen.py` reaches back into
the lexer, nothing in `parser.py` knows about LaTeX output.

Inside the stages, however, there is essentially no further structure.
Approximate line counts as of v1.3.1:

| Module | Lines | Internal organisation |
|---|---:|---|
| `latex_gen.py` | ~6.8 k | one class, ~150 methods |
| `parser.py` | ~6.4 k | one class, ~120 methods |
| `lexer.py` | ~1.6 k | one class |
| `ast_nodes.py` | ~1.5 k | flat list of `@dataclass(frozen=True)` definitions |
| `cli.py` | ~350 | one function |

The `latex_gen.py` file already uses `@generate_expr.register(NodeType)`
for dispatch — so the *machinery* for modular handlers is there, but
every registered handler lives in that single file.  The
parser is the same: clean recursive-descent design, but all 120
production rules in one class with no internal boundaries.

The consequence is concrete and measurable.  Changes that should be
local touch many places:

- A paren-policy adjustment for one operator: 5–10 sites in
  `latex_gen.py`, all manually kept in sync.
- A new AST node: parser method + generator handler + free-vars
  case + DAT-expression-detector entry — four files, no compile-time
  link between them.
- A precedence-table correction: change `PRECEDENCE` dict, then
  audit every `_needs_parens` call site to verify it still does the
  right thing, then update the reference card and DESIGN ADRs.  The
  six review rounds before v1.3.0 caught nine separate precedence
  defects, every one of which was a local change made without
  updating a peer site.

## How production compilers in this weight class organise

Five patterns recur across rustc, clang, swift, TypeScript, and GCC.
They are listed here in roughly decreasing order of leverage for a
codebase the size of txt2tex.

### 1. Dispatch by AST node type, sharded across files

Each AST node family lives in its own file and registers its
handlers with a central dispatcher at import time.  The dispatcher
itself stays small (often a single dict or `@singledispatch` table);
the bulk of the code is in topic-cohesive files.

**rustc:** `compiler/rustc_codegen_ssa/src/mir/` has `block.rs`,
`statement.rs`, `operand.rs`, etc., each handling one MIR construct.

**clang:** `lib/CodeGen/CGExpr.cpp`, `CGExprAgg.cpp`, `CGStmt.cpp`,
`CGCall.cpp`, `CGObjC.cpp` — codegen sharded by expression family.

**TypeScript:** `src/compiler/transformers/` has one file per
language feature being lowered (`es2015.ts`, `es2017.ts`,
`module/system.ts`, …).

**Why it matters for txt2tex:** the dispatch is already in place
via `@singledispatch`; sharding handlers across files is a literal
file-move with no behaviour change, and the resulting boundaries
match how a reader navigates the code ("where is GROUP rendered?"
→ `codegen/algebra.py`, not "grep `Group` in a single multi-thousand-line file").

### 2. Pass-based pipeline

Transformations are modelled as **passes** — self-contained units
with explicit input/output types and an ordering relation.  LLVM's
`PassManager`, rustc's MIR-passes pipeline, Swift's SILGen passes,
and clang's `Sema` checks all share this shape.  Passes can be
composed, reordered, A/B tested, and individually unit-tested.

The contrast: txt2tex does everything in one walk over the AST.
Paren generation, indentation, math-class spacing, fuzz-routing,
identifier emission, and string concatenation all happen in the
same method bodies in `latex_gen.py`.  When one concern needs to
change — for example, the `\mathop{\mathrm{Group}}` wrapping fix
from this cycle — there is no single site to change; the rule has
to be implemented inside the handler that knows about both Group
nodes and surrounding spacing.

**Pattern in practice:** rather than `_generate_group_aggregate`
producing a string directly, it produces a `RenderedNode` and a
later pass wraps `\mathop` based on operator-class metadata.

### 3. Multiple IRs

Production compilers translate through several typed intermediate
representations:

```text
source → tokens → parse-AST → typed-AST → mid-IR → low-IR → backend
```

Each layer has its own data types and invariants.  You cannot
accidentally use a parse-AST node where a typed-AST node is
required, because the types differ.  Name resolution, type
checking, and codegen are isolated to specific layers.

**rustc:** HIR (high-level), THIR (typed high-level), MIR
(mid-level), LLVM IR (backend).  Each transition is a discrete
phase with explicit semantics.

**Swift:** AST, Sema-typed AST, SIL, lowered SIL, LLVM IR.

**txt2tex's current shape:** there is only the AST.  Name
resolution, free-variables computation, fuzz-compatibility routing,
relational-context detection, paren decisions, and final string
emission all happen against the same node type, by reading state
from the generator.  This is workable at 17 K lines but does not
scale to the kind of static analysis txt2tex will want for richer
diagnostics ("the variable `id` is reserved", "the rename
direction looks reversed", etc.).

### 4. One file per construct family

The right granularity is "expressions in one file, declarations in
another, schemas in another" — not one file per AST node (too
granular) and not one file per stage (too coarse, which is where
txt2tex is now).

**clang:** `lib/AST/` has `Expr.cpp`, `Stmt.cpp`, `Decl.cpp`,
`DeclCXX.cpp`, `Type.cpp` — five files for the entire AST instead of
one giant `AST.cpp`.

**Swift:** `lib/AST/Decl.cpp`, `Expr.cpp`, `Pattern.cpp`,
`Stmt.cpp`, `Type.cpp`.

A txt2tex-shaped equivalent:

```text
src/txt2tex/
  lexer/
    __init__.py          # Lexer class entry point
    tokens.py            # token types
    keywords.py          # KEYWORD_TO_TOKEN, RESERVED_WORDS
    decorations.py       # ', ?, !, primed-form handling
    delimiters.py        # brackets, braces, parens
    numbers.py
    operators.py         # multi-char operator scanning
  parser/
    __init__.py          # Parser facade
    paragraphs.py        # given / free-type / abbreviation / axdef /
                         #   gendef / schema / zed / syntax
    schemas.py           # body, where-clause, defs RHS, schema
                         #   calculus (;, >>, hide, project)
    proofs.py            # PROOF: / INFRULE: / ARGUE: / EQUIV: / EQUAL:
    algebra.py           # sigma / pi / join / div / R[B/A] /
                         #   GROUP / UNGROUP / aggregators
    expressions.py       # binary / unary / function-app / quantifiers /
                         #   lambdas / conditionals / set-comprehensions
    types.py             # function arrows, relation types, generic
                         #   instantiation, free-type constructors
    bindings.py          # {| ... |} literal, theta, multi-typed comp
    text_blocks.py       # TEXT: / PURETEXT: / LATEX: / B: / PARTS: /
                         #   PAGEBREAK: / LINEBREAK:
  ast/
    __init__.py          # re-export
    expressions.py       # BinaryOp, UnaryOp, FunctionApp, Lambda, …
    declarations.py      # GivenType, FreeType, Abbreviation, AxDef, …
    schemas.py           # Schema, HorizDef, SchemaCalculus, …
    proofs.py            # ProofTree, InfRule, ArgueChain, …
    algebra.py           # Restrict, Project, RelationRename,
                         #   NaturalJoin, Divide, Group, Ungroup,
                         #   GroupAggregate
  codegen/
    __init__.py          # LaTeXGenerator facade + dispatch registry
    paren_policy.py      # PRECEDENCE, _needs_parens, RIGHT_ASSOCIATIVE,
                         #   math-class rules
    paragraphs.py
    schemas.py
    proofs.py
    algebra.py
    expressions.py
    types.py
    bindings.py
    text_blocks.py
    overflow.py          # _check_overflow + helpers
    fuzz_routing.py      # _DAT_EXPRESSION_TYPES + the inline-math
                         #   escape-hatch
  semantic/              # name resolution, free vars, reserved-word
                         #   checks
    free_vars.py
    reserved_words.py    # currently buried in lexer; deserves its
                         #   own home for semantic queries
  diagnostics/
    errors.py            # ParserError, LexerError, ErrorFormatter
    formatter.py
```

The handler count does not change.  The file count goes from ~10
to ~40.  Every handler is reachable by a directly relevant
filename — `Where is INFRULE rendered? codegen/proofs.py`.  No
greps required.

### 5. Stable internal API between layers

Compilers police the boundaries between phases.  The interface
between lex and parse is "list of tokens".  The interface between
parse and codegen is "AST module".  You cannot peek at lexer
internals from codegen — the type system, the namespace structure,
or sometimes the language's privacy model prevents it.

Python has no enforcement here, so the discipline is structural:
make the wrong import obvious by directory layout.  When `codegen/
schemas.py` is forced to `from txt2tex.parser.schemas import ...`,
that import is loud enough to prompt a "what are you doing"
question in review.

## Plan of record

### Phase 1 (✅ done, 2026-05-25) — Family-line split of `latex_gen.py` and `parser.py`

**Status.** Delivered on branch `refactor/phase1-family-split`,
twelve commits (Move 0 + nine batches + docs + tooling).  Every
batch verified at three gates: `make check`, `make test-e2e`
(159/159 fixtures byte-identical), and `make refactor-diff`
(190/190 examples + tests/bugs byte-identical vs main).

**Final line counts.**

| File | main (baseline) | after Phase 1 | reduction |
|---|---|---|---|
| `src/txt2tex/latex_gen.py` | 6,864 | 598 | 91.3% |
| `src/txt2tex/parser.py` | 6,367 | 846 | 86.7% |

The two former monoliths are now orchestrator shells.  Handler
implementations live under `src/txt2tex/codegen/` (11 mixin files,
~7.4k lines) and `src/txt2tex/parser_pkg/` (9 mixin files plus a
`_base.py` shape declaration, ~6.9k lines).  No file in `src/txt2tex/`
exceeds 2,800 lines; the largest are `codegen/text_pipeline.py`
(the ASCII-to-LaTeX conversion subsystem) and
`parser_pkg/expressions.py` (the full recursive-descent grammar).

**Scope.** Move handlers from the monolithic files into the
directory structure above.  Behaviour does not change: every test
that passes today must pass after the move, byte-for-byte on the
e2e fixtures.  The `LaTeXGenerator` and `Parser` classes remain;
their methods are physically relocated and `from ... import ...`
ties them back together.

**Mechanics.**  Python's `@singledispatch.register(NodeType)` works
across modules — registration is by import side-effect, so as long
as `codegen/__init__.py` imports every submodule, every handler is
registered.  Parser methods are slightly harder because the
recursive-descent calls form a graph (`_parse_expr` calls
`_parse_iff` calls `_parse_implies` …); the move keeps the methods
on a single class spread across files via a mixin pattern, or
extracts them into free functions taking the parser instance.

**Acceptance criteria — all met.**

- ✅ `make check` and `make test-e2e` pass byte-for-byte unchanged.
- ✅ `make refactor-diff` (new gate, see Phase 1 deliverables)
  confirms 190 / 190 inputs across `examples/` + `tests/bugs/` are
  byte-identical against `main`.
- ⚠️ One file exceeds 1,500 lines: `codegen/text_pipeline.py` at
  1,782 lines.  This is the self-contained ASCII-to-LaTeX
  conversion pipeline; splitting it would have required
  Extract-Method work outside the Phase 1 discipline.  Deferred to
  Phase 2 or a dedicated pass.
- ✅ Every test in `tests/` continues to import from the public
  `txt2tex.latex_gen.LaTeXGenerator` / `txt2tex.parser.Parser`
  surface — no test files were touched.
- ✅ `git diff main..HEAD --stat` shows file moves dominating;
  line counts across the family-line split are roughly constant.

**Tooling added during Phase 1.**

- `scripts/refactor_diff.py` + `scripts/refactor_diff_vs_ref.sh` —
  byte-for-byte comparison of `.tex` output across a 190-input
  corpus against an arbitrary git ref.  Exposed as `make
  refactor-diff` / `make refactor-capture` / `make refactor-verify`.
- `codegen/_dispatch.py` `CodegenDispatch` and
  `parser_pkg/_base.py` `ParserBase` — type-only shape classes
  that mirror the composed-class interface so each mixin file
  type-checks in isolation.

**Non-goals.**

- No behavioural change.
- No new IR, no passes, no new diagnostics.
- The dispatch mechanism stays as it is.

**Why first.**  Every subsequent refactor benefits from the
narrower file boundaries.  Pulling paren policy out (Phase 2) is
easier when `paren_policy.py` is already a thing.  Adding a
typed-AST layer (Phase 3) is easier when each codegen handler
lives next to the AST node family it consumes.  This phase has
the highest leverage per unit of work.

### Phase 2 — Extract paren / precedence policy into its own module

**Problem.**  The paren-generation rules are currently entangled
with LaTeX emission: `_needs_parens` lives on the `LaTeXGenerator`
class, the `PRECEDENCE` dict is a class variable, and right-
associativity is partly in `RIGHT_ASSOCIATIVE` (documentary only)
and partly hard-coded inside `_needs_parens`.

Six of the 9 precedence-related defects caught during the v1.3.0
review rounds were caused by this entanglement — the rules were
correct in `PRECEDENCE` but applied inconsistently by handlers.

**Scope.**  Pull paren-policy into `codegen/paren_policy.py` as
pure functions over `(parent: ASTNode, child: ASTNode) -> bool`.
The function knows nothing about LaTeX strings.  Codegen handlers
call `paren_policy.needs_parens(self.node, child)` instead of
computing it locally.

**Acceptance criteria.**

- Paren policy is unit-tested in isolation, without going through
  the LaTeX generator.
- Adding a new operator requires editing exactly one file
  (`paren_policy.py`).
- The reference card's Operator Precedence section is generated
  *from* the policy module, not maintained in parallel.

**Why second.** Phase 1 makes this physically possible (the file
exists).  This phase makes precedence regressions a unit-test-
caught failure instead of an integration-test-caught failure, and
eliminates the reference-card-versus-code drift class entirely.

### Phase 3 — Rendered-tree IR between AST and string emission

**Problem.**  Codegen currently does many things at once: name
resolution, paren wrapping, math-class spacing, fuzz-routing,
indentation, and string concatenation.  When one concern needs to
change, the change is interleaved with the others.  The
`\mathop{\mathrm{Group}}` wrapping fix from this cycle is an
example: the rule "binary-operator-class needs `\mathop`" was
implemented inside `_generate_group_aggregate` instead of being a
general transformation on the rendered tree.

**Scope.**  Introduce a `RenderedNode` IR between AST and string
output:

```text
ast.Node → codegen.render(node) → RenderedNode → string_emit → str
```

`RenderedNode` carries math-class metadata, paren state, and any
LaTeX-side decisions.  Passes operate on this tree:

- `wrap_binary_ops_with_mathop`
- `insert_parens_per_precedence`
- `route_dat_expressions_to_inline_math`
- `apply_concat_spacing`
- `apply_overflow_warnings`

Each pass is independently testable on `RenderedNode → RenderedNode`.
The final string emission is a single pure pass over the rendered
tree.

**Acceptance criteria.**

- New rendering rules are added by writing a new pass, not by
  editing every handler.
- The rendering output is reproducible: given the same AST and the
  same pass list, the same string comes out.
- The `_check_overflow` machinery moves to a pass (currently it is
  called manually from a few handler sites — easy to forget).

**Why third.** This is the largest of the three changes, and it
benefits most from Phases 1 and 2 being done first.  Without the
file-level decomposition, the IR types end up in a single
`render.py` that is no more navigable than `latex_gen.py` is now.
Without the paren-policy module, the paren pass cannot be written
cleanly.

### Phase 4 and beyond

Once Phase 3 lands, several things become tractable that are not
today:

- **Static analysis passes** for diagnostics: "this `id`
  declaration shadows the relational identity operator", "this
  rename direction looks reversed because the LHS isn't a fresh
  name in the relation's schema", "this proof's PROOF: rule
  doesn't match the conclusion's connective".  These are passes
  over the typed AST.

- **Optimisations on the rendered tree**: common-subexpression
  hoisting for long predicates, automatic line-break insertion
  based on textual length, dead-code elimination for unused
  abbreviations in long documents.

- **Multiple output backends**: HTML, Markdown-with-MathJax,
  plain text — each as a separate string-emission pass over the
  same `RenderedNode` tree.

- **Incremental parsing** (à la TypeScript's language service):
  re-parse only the changed paragraph, reuse AST subtrees from
  the previous parse.  Useful for the REPL and for a future
  language-server.

None of Phase 4 is on the critical path.  The roadmap stops at
Phase 3 because that is the boundary where the current
architectural choices stop limiting velocity.

## What this roadmap is not

It is not a request to rewrite the codebase.  The current code is
correct, well-tested, and shipping.  17 K SLOC is small enough that
the absence of internal modularity has been tolerable to date.

It is a plan for *the next time it isn't tolerable*.  When the
next major feature lands — for example, a richer type-checking
layer, or a second output backend, or a language-server frontend —
the structural choices in Phases 1–3 will determine whether that
feature takes a week or a month.

The Phase 1 split alone changes the codebase's surface from
"one large file you have to scroll" to "a directory tree you can
navigate."  That is the change that resolves the embarrassment
factor; the deeper changes are improvements on top of an already
respectable structure.
