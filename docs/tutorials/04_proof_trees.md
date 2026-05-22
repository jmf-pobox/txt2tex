# Tutorial 4: Proof Trees

<!-- markdownlint-disable-next-line MD036 -->
**Lecture 4: Deductive Proofs**

Learn natural deduction and write formal proofs that fuzz-typecheck and
render as branching `\infer` trees in the PDF.

**Prerequisites:** Tutorials 1–3
**Examples:** `examples/04_proof_trees/`
**Reference:** `docs/guides/PROOF_SYNTAX.md`

---

## 1. What a proof tree is

A **proof tree** is a structured argument: a conclusion sits at the
bottom, premises sit above it joined by an inference bar labelled with
the rule applied, and each premise is itself the conclusion of a sub-
proof. The leaves of the tree are either axioms or **discharged
assumptions** introduced inside the proof.

In a `PROOF:` block, you write the tree **top-down** in the source
file: the final conclusion comes first, its premises are written
*below it and indented*, and so on recursively. The generator emits
the tree using LaTeX `\infer` macros so that the rendered PDF reads
bottom-up — exactly the natural-deduction layout.

> **Read this once and keep it in mind:** the source file is conclusion-first;
> the rendered tree is conclusion-last. Indentation in the source
> corresponds to going *up* the tree in the rendered output.

---

## 2. The three syntactic concepts you need

Every proof in this tutorial — and every proof in the examples
directory — is built from three concepts. Learn them in order.

### 2.1 Conclusion-first nesting

A line in a `PROOF:` block is a **conclusion**. Lines indented under
it are its **premises**. Indentation is the parent–child relation
between a rule and its inputs.

```text
PROOF:
conclusion [rule label]
  premise_1
  premise_2
```

Here `conclusion` is derived by the rule named in `[rule label]` from
`premise_1` and `premise_2`.

### 2.2 The `::` marker for multi-premise rules

If a rule takes **two or more premises** (e.g. `land-intro` takes two,
`lor-elim` takes three), each premise line must be marked with `::` so
the generator emits a real branching `\infer` node. Without `::`, the
generator treats consecutive lines as a **linear chain** — each line
becomes the single premise of the line above it.

**Wrong — linear chain (silently produces a unary tree):**

```text
PROOF:
p land q [land intro]
  p
  q
```

**Right — siblings under a binary rule:**

```text
PROOF:
p land q [land intro]
  :: p
  :: q
```

Rule of thumb: **if the rule has more than one premise, every premise
line gets `::`**. If you forget, the tree silently degrades and the
extra premises become orphan ancestors of the last one.

### 2.3 Discharge: `[N] X [assumption]` paired with `Y [from N]`

Some rules **discharge an assumption** introduced earlier in the
proof — `=>-intro` discharges the antecedent, `false-elim` discharges
the assumed formula being shown contradictory, `lor-elim` discharges
the two case formulas. The discharge is encoded by a pair:

- **Assumption marker:** `[N] X [assumption]` — declares "X is
  assumed here under label N." Appears as a sibling of the rule's
  body, directly under the discharging rule.
- **Leaf reference:** `Y [from N]` — at any leaf where the assumption
  is used, write the formula followed by `[from N]`.

```text
PROOF:
p => p [=> intro from 1]
  [1] p [assumption]
  :: p [from 1]
```

Here the `=> intro from 1` rule discharges assumption `[1] p`. Inside
its body, the conclusion `p` references the assumption with
`[from 1]`. Both the assumption marker and the body live as children
of the discharging rule.

When the rule introducing the discharge is `=>-intro` or
`false-elim`, the assumption marker and the body together act as the
discharging step's "premises" in the rendered tree. This is the same
pattern used throughout `txt2tex-hw/solutions.txt` and the example
files.

**Note about the `::` on the body.** §2.2 says unary rules take a
single indented child with no `::`. Discharging rules are unary in
the natural-deduction sense — they have one composite premise, the
derivation under the assumption. The `::` written on the body line
(e.g. `:: p [from 1]` above) is *not* signalling a multi-premise rule;
it is a **structural separator** between the bare assumption marker
`[N] X [assumption]` and the body derivation. Use `::` on the body
of any discharging rule (`=>-intro from N`, `false-elim from N`,
`lor-elim from N`).

---

## 3. `case X:` for `lor`-elimination

`lor`-elimination has three premises: the disjunction, and one
sub-proof per disjunct. Each sub-proof discharges the corresponding
case formula. The syntax uses `case X:` to introduce each branch.

```text
PROOF:
r [lor elim from 2]
  :: p lor q [from 2]
  case p:
    :: r [...derivation of r from p...]
  case q:
    :: r [...derivation of r from q...]
```

Inside a `case p:` block, you can reference the case formula with
`p [from 2]` (using the same label that the enclosing `lor elim from
N` discharges). The case-introduced formula is available throughout
its block as if it were a hypothesis with that label.

**Label sharing.** The discharge label `N` on `lor elim from N` is
shared by three things in the enclosing proof: the disjunction
itself (`[N] p lor q [assumption]` or `:: p lor q [from N]`), and the
two case-introduced formulas inside the `case p:` and `case q:`
blocks. All three are discharged together by the single `lor elim
from N` step. References from any leaf use `[from N]` regardless of
which of the three formulas is being cited — context (the branch the
leaf sits in) disambiguates.

**See:** `examples/04_proof_trees/excluded_middle.txt` for many fully
worked examples using `case X:` blocks.

---

## 4. Inference rules — math and txt2tex form side by side

Each rule below shows the standard natural-deduction presentation and
its txt2tex encoding. Memorise the **arity** (number of premises) of
each rule — that determines whether `::` is needed.

### Conjunction (`land`)

**`land`-intro** (binary):

```text
  P    Q
─────────── [land intro]
  P land Q
```

txt2tex form (both premises siblings under the conclusion):

```text
:: P land Q [land intro]
  :: P [...]
  :: Q [...]
```

**`land`-elim** (unary; choose the projection):

```text
P land Q              P land Q
──────── [land elim 1]      ──────── [land elim 2]
   P                          Q
```

txt2tex form (single premise, no `::` needed at that step):

```text
:: P [land elim 1]
  P land Q [...]
```

### Disjunction (`lor`)

**`lor`-intro** (unary; choose the side):

```text
   P                       Q
─────────── [lor intro 1]      ─────────── [lor intro 2]
 P lor Q                    P lor Q
```

txt2tex form:

```text
:: P lor Q [lor intro 1]
  P [...]
```

**`lor`-elim** (ternary — uses `case X:`):

```text
 P lor Q     [P]…R      [Q]…R
────────────────────────────── [lor elim from N]
              R
```

txt2tex form (see §3 above).

### Implication (`=>`)

**`=>`-intro** (unary, discharging — uses the `[N] X [assumption]`
pair from §2.3):

```text
  [P]
   ⋮
   Q
─────── [=> intro from N]
 P => Q
```

txt2tex form (assumption marker and body are siblings under the rule):

```text
P => Q [=> intro from N]
  [N] P [assumption]
  :: Q [...derivation of Q, may reference [from N]...]
```

**`=>`-elim** (binary, a.k.a. modus ponens):

```text
P    P => Q
─────────── [=> elim]
     Q
```

txt2tex form:

```text
:: Q [=> elim]
  :: P [...]
  :: P => Q [...]
```

### Negation (`lnot`)

`lnot P` is encoded as `P => false`, so negation rules reuse
implication and `false`-rules.

**`lnot`-intro** (via `=>-intro` discharging P):

```text
  [P]
   ⋮
 false
───────── [=> intro from N]   (read as lnot intro)
 lnot P
```

**Contradiction** (`false`-intro, binary):

```text
P    lnot P
─────────── [false-intro]
   false
```

txt2tex form:

```text
:: false [false-intro]
  :: P [...]
  :: lnot P [...]
```

**`false`-elim** (unary, discharges the assumption being refuted):

```text
   false
─────────── [false elim from N]
    Q
```

---

## 5. Worked examples

Each example is conclusion-first, uses `::` for every multi-premise
rule, and pairs `[N] … [assumption]` markers with `[from N]`
references at leaves.

### Example 1 — Modus ponens

Goal: derive `q` from `p` and `p => q` (no discharge, both `p` and
`p => q` are external premises).

```text
PROOF:
q [=> elim]
  :: p [premise]
  :: p => q [premise]
```

The rendered `\infer` node for `q` has two visible premises.

### Example 2 — `(p land (p => q)) => (p land q)`

Goal: prove the implication. Outer `=>`-intro discharges `[1]`. Inner
body builds `p land q` by `land-intro` from `p` and `q`; `q` itself
comes from `=>`-elim.

```text
PROOF:
(p land (p => q)) => (p land q) [=> intro from 1]
  [1] p land (p => q) [assumption]
  :: p land q [land intro]
    :: p [land elim 1]
      p land (p => q) [from 1]
    :: q [=> elim]
      :: p => q [land elim 2]
        p land (p => q) [from 1]
      :: p [land elim 1]
        p land (p => q) [from 1]
```

Every multi-premise rule (`land intro`, `=> elim`) has its two
premises marked with `::`. Every unary `land elim` has its single
premise indented below it (no `::` needed). Every use of the
discharged assumption ends in `[from 1]`.

### Example 3 — Contradiction

Goal: from `p land lnot p`, derive `q` (the explosion principle).

```text
PROOF:
(p land lnot p) => q [=> intro from 1]
  [1] p land lnot p [assumption]
  :: q [false elim from 2]
    [2] lnot q [assumption]
    :: false [false-intro]
      :: p [land elim 1]
        p land lnot p [from 1]
      :: lnot p [land elim 2]
        p land lnot p [from 1]
```

Two discharges in one proof: `[1]` by `=> intro`, `[2]` by
`false elim`. Both follow the same pattern.

### Example 4 — Case analysis on a disjunction

Goal: prove `((p => r) land (q => r)) => ((p lor q) => r)`. The inner
`lor elim` does case analysis.

```text
PROOF:
((p => r) land (q => r)) => ((p lor q) => r) [=> intro from 1]
  [1] (p => r) land (q => r) [assumption]
  :: (p lor q) => r [=> intro from 2]
    [2] p lor q [assumption]
    :: r [lor elim from 2]
      :: p lor q [from 2]
      case p:
        :: r [=> elim]
          :: p [from 2]
          :: p => r [land elim 1]
            (p => r) land (q => r) [from 1]
      case q:
        :: r [=> elim]
          :: q [from 2]
          :: q => r [land elim 2]
            (p => r) land (q => r) [from 1]
```

The `lor elim from 2` rule has the disjunction `p lor q [from 2]` as
its left premise and the two `case` blocks as its right premises.
Inside each case, the case-introduced formula is referenced with
`[from 2]`.

---

## 6. Indentation conventions

- The outermost conclusion is **unindented** (no leading spaces).
- Each child line is indented **two spaces** beyond its parent.
- Lines under a `case X:` block are indented two spaces beyond the
  `case` keyword.
- Within a single tree, every conclusion's children are at the same
  indent level.

The generator parses by indentation, so consistent indentation matters
for the tree shape. Inconsistent indentation will either parse
incorrectly or fail to type-check.

---

## 7. Common pitfalls

### 7.1 Forgetting `::` on multi-premise rules

**Symptom:** the rendered tree shows a *linear chain* — each rule has
exactly one premise, even rules that should be binary or ternary.
Intermediate lines appear stacked vertically instead of side by side.

**Fix:** add `::` in front of every premise of every multi-premise
rule. The number of `::` lines under a conclusion must equal the
rule's arity.

### 7.2 Treating an assumption marker as a derivation step

The line `[N] X [assumption]` is **not** itself derived from anything
— it introduces a hypothesis. It appears as a sibling of the body
under the discharging rule, never as a child of a `::` marker.

### 7.3 Missing `[from N]` at a leaf

If you write the assumption formula at a leaf without `[from N]`, the
generator emits a bare assumption corner without tying it to the
discharge — the tree renders, but the assumption is not visibly
discharged. Always pair `[N] X [assumption]` with `Y [from N]` at
every leaf use.

### 7.4 Rule-label typography

Use the `[rule-name from N]` form (with a hyphen between rule and
suffix) wherever the rule has a `from N` discharge. For example,
prefer `[false-intro]` over `[false intro]`, and `[=>-elim]` over
`[=> elim]`. The generator currently renders multi-word labels
without a hyphen with looser spacing in the bracket — see
`tests/bugs/bug4_proof_label_typography.txt`. This is cosmetic, not a
correctness issue, but the hyphenated form looks better.

---

## 8. Summary

You've learned:

- Proof trees are conclusion-first in the source, conclusion-last in
  the rendered output.
- `::` marks each premise of a multi-premise rule. Without it,
  consecutive lines form a linear chain.
- `[N] X [assumption]` and `Y [from N]` are paired to encode
  discharge.
- `case X:` introduces branches inside a `lor elim`.
- The natural-deduction rules' arity determines whether you need `::`.

**Next Tutorial:** [Tutorial 5: Z Notation Definitions](05_z_definitions.md)

---

**Practice:** work through `examples/04_proof_trees/`, especially
`simple_proofs.txt`, `nested_proofs.txt`, and `excluded_middle.txt`.
For any proof you write, check the rendered PDF: every multi-premise
rule should show its premises side by side under the inference bar,
not stacked vertically as a chain.
