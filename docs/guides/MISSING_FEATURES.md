# Missing Features

This document lists Z notation features not yet implemented in txt2tex, and
the limitations you may run into. Open work is tracked in
[GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues). Shipped
features are recorded in [CHANGELOG.md](../../CHANGELOG.md).

---

## Open Gaps

| Gap | Issue |
|-----|-------|
| `LET` construct for local definitions | [#116](https://github.com/jmf-pobox/txt2tex/issues/116) |
| User-defined operator templates (`_op_`, `op _`) | [#118](https://github.com/jmf-pobox/txt2tex/issues/118) |
| `NOFUZZ:` on `gendef` boxes (`gendefnofuzz`) | [#100](https://github.com/jmf-pobox/txt2tex/issues/100) |
| Positional tuple projection `p.1` inside a quantifier body renders as a bullet (bug) | [#114](https://github.com/jmf-pobox/txt2tex/issues/114) |
| Multi-declaration `lambda` without a `\|` constraint is rejected | [#115](https://github.com/jmf-pobox/txt2tex/issues/115) |
| Reflexive and symmetric closure (`rcl`, `scl`) | [#117](https://github.com/jmf-pobox/txt2tex/issues/117) |
| Unspaced `>` inside `sigma[...]` is rejected | [#121](https://github.com/jmf-pobox/txt2tex/issues/121) |
| Line breaks after `;` in set comprehensions are not preserved | [#122](https://github.com/jmf-pobox/txt2tex/issues/122) |

---

## LET Construct

Tracking: [#116](https://github.com/jmf-pobox/txt2tex/issues/116).

Local definitions in expressions and predicates:

```text
LET double == lambda x : N . x * 2 @
quad(5)
```

**Workaround**: Use document-level abbreviations instead.

---

## User-Defined Operator Names

Tracking: [#118](https://github.com/jmf-pobox/txt2tex/issues/118). See
[docs/deferred/user-defined-operators.md](../deferred/user-defined-operators.md)
for the engine design needed to ship the feature.

The engine does not yet accept underscored operator templates (`_⊕_`,
`_R_`, `op _`, `_ †`) as the LHS of an abbreviation or declaration.
None of these compile today:

```text
_disjoint_ [X] == { s, t : P X | s intersect t = {} . (s, t) }   # rejected
_subrefn_ : (Op cross Op)                                        # rejected
pre_ : Op -> Pred                                                # rejected
```

After such a definition (in real Z) the document could use the new
operator natively (`s disjoint t`, `Op1 subrefn Op2`). The declaration
syntax cannot express that in txt2tex today.

**Workarounds:**

1. **You want to *use* an operator that already exists in fuzz's
   toolkit** (`notin`, `subseteq`, `cat`, `oplus`, `dres`, `nrres`,
   `mapsto`, ...). Just write it. txt2tex already maps the keyword to
   the right LaTeX command. No directive needed; fuzz already knows
   the symbol.

2. **You want to show how an operator is defined** by a generic
   abbreviation. Use a regular identifier as the LHS name and add a
   TEXT note explaining the substitution:

   ```text
   TEXT: A generic abbreviation defines the relation Disjoint as the set of pairs (s, t) with no element in common.

   [X] Disjoint == { s, t : P X | s intersect t = {} . (s, t) }
   ```

   `uv run txt2tex --tex-only` type-checks this and emits:

   ```latex
   Disjoint[X] == \{~ s, t : \power X | s \cap t = \{\} @ (s, t) ~\}
   ```

   The set on the RHS is the right mathematical object. The LHS uses a
   parser-acceptable identifier (`Disjoint`). The TEXT prose tells the
   reader the intended operator name. The document shows the technique
   of generic abbreviation even though the surface notation
   `s Disjoint t` is not available.

3. **You want to introduce a new operator that later paragraphs use**
   (for example `_⊑_` for refinement). The full surface form is not
   available. Two workarounds:

   - Define a named relation and use prefix notation everywhere:
     `refines : Op cross Op` and write `(Op1, Op2) elem refines`
     instead of `Op1 refines Op2`.
   - Define a named function and use application notation:
     `refines : Op cross Op -> Pred` and write `refines(Op1, Op2)`.

   Neither matches Spivey's surface form. Both are parser-acceptable
   and mathematically equivalent.

4. **Last resort: drop into raw LaTeX with a `LATEX:` block.** The
   engine passes the body verbatim to fuzz. You can write the literal
   `\_ \notin \_ [X] == ...` form including any `%%` directive
   announcement you need. This bypasses every txt2tex check; reserve
   it for paragraphs that cannot be expressed in the supported
   notation.

---

## Known Limitations

1. **Superscript `^`**: Only for relation iteration (`R^n`), not arithmetic (`x^2`). Write `x * x` for squaring. If you need the literal `n^2` form to appear (for example in teaching material), mark the containing `axdef`/`schema`/`zed`-paragraph box with `NOFUZZ:` — see [USER_GUIDE.md § NOFUZZ](USER_GUIDE.md#nofuzz--marking-content-fuzz-cant-check). `NOFUZZ:` renders the box normally (fuzz just skips checking it) and is enforced by a reject-if-clean lint, so it can't be used to hide an actual type error. `gendef` boxes are not yet supported by `NOFUZZ:` ([#100](https://github.com/jmf-pobox/txt2tex/issues/100)); no LaTeX environment exists for them yet.
2. **Tuple projection**: Use named fields (`x.field`). Positional projection (`.1`, `.2`) is not supported. Inside a quantifier body the first `p.1` renders as a bullet (`p @ 1`), and fuzz rejects the output. Tracking: [#114](https://github.com/jmf-pobox/txt2tex/issues/114).
3. **fuzz parallel-binding in set comprehensions**: fuzz requires sequential binding of schema text (Z RM §3.5 allows parallel; fuzz tightens this). The generator automatically works around this for `forall`/`exists`/`exists1`/`mu`/`lambda` by reordering declarations. Set comprehensions using multiple schemas with cross-references raise a clear error directing you to rewrite as a single declaration sequence.
4. **`id` is reserved**: maps to `\id` (the identity relation operator). It cannot be used as a schema-component name, variable, or relation name. Use `tid`, `rid`, `entityId`, etc. instead. (Other Z RM names that are similarly reserved: `dom`, `ran`, `inv`, `pre` — anything in the standard Z toolkit.)
5. **Underscore in identifiers**: txt2tex applies a heuristic when generating LaTeX (fuzz mode):
    - Single-digit suffix (`x_1`, `z_5`): emits `x_1` as a subscript decoration. Standard Z subscripted variable.
    - Single-letter suffix (`length_L`, `f_x`): emits `length\_L` — a literal underscore in the rendered name, NOT a subscript.
    - Two-digit suffix (`x_10`, `z_42`): emits `x_{10}` as a braced subscript.
    - Two-letter / mixed suffix (`FK_EE`, `state_AB`): emits `FK\_{EE}` — literal underscore plus braces.
    - Three-plus-char suffix (`cumulative_total`): goes to the multi-word identifier path; emits as `\mathit{cumulative\_total}`.
   Consequence: short letter suffixes that LOOK like subscripts (`FK_E`) are NOT subscripted; they render with a literal underscore. Use parenthesised parametrisation (`FK(E)`) or rename without an underscore if you want a clean visual.
6. **Reflexive and symmetric closure**: `rcl` and `scl` are not supported. Tracking: [#117](https://github.com/jmf-pobox/txt2tex/issues/117). Write the union with the identity relation yourself (`R union id X`).
7. **Unspaced `>` or `<` in `sigma[...]`**: `sigma[price>10](R)` stops with an error. Write `sigma[price > 10](R)` with spaces. Tracking: [#121](https://github.com/jmf-pobox/txt2tex/issues/121).
8. **Line breaks after `;` in set comprehensions** are not preserved in the output. Tracking: [#122](https://github.com/jmf-pobox/txt2tex/issues/122).
9. **Multi-declaration `lambda` without a `|` constraint** (`lambda x : N; y : N . x + y`) is rejected with `Expected '|' after quantifier binding`. Add a constraint: `lambda x : N; y : N | true . x + y`. Tracking: [#115](https://github.com/jmf-pobox/txt2tex/issues/115).
