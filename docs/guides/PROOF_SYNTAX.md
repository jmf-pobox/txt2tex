# Proof Trees — Syntax Specification

> **For learners:** read
> **[Tutorial 4: Proof Trees](../tutorials/04_proof_trees.md)** first.
> It explains the format with worked examples. This document is the
> authoritative specification — keep it for reference.

## Overview

Proof trees in txt2tex use:

- **Conclusion-first nesting**: each line is a conclusion; indented
  lines beneath it are its premises (or the assumption marker for a
  discharging rule).
- **`::` markers for multi-premise rules**: every premise of a
  rule with arity ≥ 2 must be prefixed with `::`. Without `::`,
  consecutive indented lines form a *linear chain* — each line
  becomes the sole premise of the line above it.
- **`[N] X [assumption]` paired with `Y [from N]`**: declares a
  discharged assumption and references it at every leaf.
- **`case X:` blocks** for `lor`-elimination.

Natural reading order in the source is top-down (conclusion first);
the rendered `\infer` tree reads bottom-up — exactly the
natural-deduction layout.

## Basic Structure

```text
PROOF:
conclusion [justification]
  [label] assumption [assumption]
      derived-statement [justification]
      ...
```

## Related: `INFRULE:` (rule schema display)

`PROOF:` builds a derivation tree from premises up to a conclusion.  Use
the sibling keyword `INFRULE:` when you want to *display* an inference
rule itself — a labelled premise/conclusion pair, not a derivation.

```text
INFRULE:
P
P => Q
---
Q [modus ponens]
```

Renders as a horizontal `\derive` rule: premises above the line,
conclusion below, optional label on the right.  Each line above the
three-dash separator is a premise; the line below is the conclusion.
The `[label]` is optional; without it the rule is unlabelled.

Multiple premises are supported by listing them on separate lines.
See `examples/04_proof_trees/infrule_modus_ponens.txt` for working
examples.

`INFRULE:` is for showing what a rule *is*; `PROOF:` is for applying
rules to derive a result.

## Syntax Elements

### 1. Proof Header

```text
PROOF:
```

Marks the beginning of a proof tree.

### 2. Conclusion (Top Level)

The conclusion is the top-level statement of the proof. It appears
**first**: the rest of the proof derives it. Premises (or the
discharged assumption + body for a discharging rule) are indented
beneath.

```text
PROOF:
p land q => q [=> intro from 1]
  [1] p land q [assumption]
  :: q [land elim 1]
    p land q [from 1]
```

`p land q => q` is the conclusion. `=>-intro from 1` discharges the
assumption `[1] p land q` and produces the implication; the body of
the implication is `q [land elim 1]`, derived at a single leaf
referencing the assumption with `[from 1]`.

### 3. Assumptions with Labels

Assumptions are marked with `[number]` and the keyword `[assumption]`:

```text
[1] p land q [assumption]
```

- The `[1]` is a **label** used to reference this assumption later
- Everything indented under this is "within the scope" of the assumption

### 4. Regular Proof Steps

```text
q [land elim]
```

- Statement followed by justification in brackets
- Indentation shows dependency

### 5. Sibling Premises (`::`  marker)

When a rule takes two or more premises, each premise line is prefixed
with `::` and nested **below** the rule's conclusion:

```text
:: p land q [land intro]
  :: p [...]
  :: q [...]
```

The `::` means "this is a premise of the conclusion above me." The
generator emits a real branching `\infer` node with one premise per
`::` line. Without `::`, indented siblings collapse into a linear
chain (each line becomes the sole premise of the line above) — the
rule's other premises are silently dropped.

**Arity matters**: `land intro`, `=> elim`, `false-intro`, `<=> intro`,
and `lor elim` are all multi-premise and require `::`. Unary rules
like `land elim 1`, `lor intro 1`, and `false elim` do not — their
single premise can be a plain indented line.

### 6. Case Analysis

`lor`-elimination is ternary: the disjunction itself plus one
sub-proof per disjunct. Encode it with a `lor elim from N` rule whose
premises are the disjunction (via `[from N]`) and `case X:` blocks.
Each case block introduces the disjunct as a local assumption that
shares label N.

```text
:: r [lor elim from 2]
  :: p lor q [from 2]
  case p:
    :: r [...derivation using p [from 2]...]
  case q:
    :: r [...derivation using q [from 2]...]
```

Inside a `case p:` block, references to the case formula use the same
label N as the enclosing `lor elim from N` — e.g. `p [from 2]`. Facts
derived outside the case analysis remain available via their own
`[from M]` references.

**Label sharing under `lor elim from N`.** A single discharge label N
is shared by three formulas: the disjunction itself (referenced as
`p lor q [from N]`), and the two case-introduced formulas (`p [from
N]` inside `case p:` and `q [from N]` inside `case q:`). All three
are discharged together by the single `lor elim from N` step. The
context — which leaf, in which branch — disambiguates which formula
each `[from N]` reference cites.

### 6a. Discharging-rule body and the `::` marker

`=>-intro`, `false-elim`, `lor-elim` are *discharging* rules. In
natural deduction they are unary in the sense of having one
composite premise (the derivation under the assumption). The
`::` marker on the body line of a discharging rule (e.g. `:: q
[land elim 2]` in `=>-intro from 1`) is a **structural delimiter**
between the bare assumption marker `[N] X [assumption]` and the
body — not a multi-premise signal. Use `::` on the body of every
discharging rule even though arity is 1 in the natural-deduction
sense.

For non-discharging unary rules like `land elim 1`, `lor intro 1`,
or `false elim` (without `from N`), the single premise is a plain
indented child — no `::` needed.

### 7. Justifications

Justifications are free-form text enclosed in brackets `[...]`. Any text is accepted, but the following are standard natural deduction rules:

**Basic rules:**

- `[assumption]` - marks assumptions
- `[premise]` - given fact

**Conjunction (land):**

- `[land elim]`, `[land elim left]`, `[land elim right]`, `[land elim 1]`, `[land elim 2]` - land elimination
- `[land intro]` - land introduction

**Disjunction (lor):**

- `[lor elim]` - lor elimination (case analysis)
- `[lor intro]`, `[lor intro left]`, `[lor intro right]`, `[lor intro 1]`, `[lor intro 2]` - lor introduction

**Implication (=>):**

- `[=> intro from N]` - implication introduction, discharging assumption [N]
- `[=> elim]` - implication elimination (modus ponens)

**Negation (lnot):**

- `[lnot intro from N]` - negation introduction (proof by contradiction), discharging assumption [N]
- `[lnot elim]` - negation elimination

**Absurdity (false):**

- `[false elim]` - ex falso quodlibet (from false, derive anything)
- `[contradiction]`, `[contradiction with X]` - deriving false from contradictory statements

**Classical logic:**

- `[LEM]` - Law of Excluded Middle (p lor lnot p axiom)
- `[double negation elim]` - classical rule: lnot lnot p implies p

**Derived rules:**

- `[identity]` - trivial identity step (p proves p)
- `[negation intro from N]` - alternative form of lnot intro

**Informal annotations:**

- `[from above]` - reference to earlier step in proof
- `[from case]` - reference to case hypothesis
- `[from X]` - reference to specific statement or premise X
- `[derived]` - derived result
- `[known fact]` - external or previously established fact
- `[definition]` - by definition
- `[arithmetic]`, `[algebra]`, `[simplification]`, `[factoring]` - mathematical reasoning steps

**Note**: The parser accepts any text within brackets as a justification. The above list represents commonly used patterns in natural deduction and mathematical proofs.

## Complete Examples

These examples are kept consistent with
[Tutorial 4](../tutorials/04_proof_trees.md) and the hand-coded
reference proofs in the project. Every multi-premise rule uses `::`
on each premise; every discharged assumption pairs `[N] X
[assumption]` with `Y [from N]` at every leaf use.

### Example 1: Simple Implication

**Goal**: Prove `p land q => q`

```text
PROOF:
p land q => q [=> intro from 1]
  [1] p land q [assumption]
  :: q [land elim 2]
    p land q [from 1]
```

The outer `=>-intro from 1` discharges `[1] p land q`. Its body is
`q`, derived by the unary `land elim 2` from a leaf use of the
assumption.

### Example 2: Modus Ponens via Conjunction

**Goal**: Prove `(p land (p => q)) => (p land q)`

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

`land intro` is binary, so both `p` and `q` carry `::`. Inside, `q
[=> elim]` is also binary, so its two premises (`p => q` and `p`)
each carry `::`. Every land-elim is unary (single indented premise).
Every leaf use of the assumption is tagged `[from 1]`.

### Example 3: Distribution with Cases

**Goal**: Prove `(p land (q lor r)) => ((p land q) lor (p land r))`

```text
PROOF:
(p land (q lor r)) => ((p land q) lor (p land r)) [=> intro from 1]
  [1] p land (q lor r) [assumption]
  :: (p land q) lor (p land r) [lor elim from 2]
    :: q lor r [land elim 2]
      p land (q lor r) [from 1]
    case q:
      :: (p land q) lor (p land r) [lor intro 1]
        :: p land q [land intro]
          :: p [land elim 1]
            p land (q lor r) [from 1]
          :: q [from 2]
    case r:
      :: (p land q) lor (p land r) [lor intro 2]
        :: p land r [land intro]
          :: p [land elim 1]
            p land (q lor r) [from 1]
          :: r [from 2]
```

The inner `lor elim from 2` rule has three premises: the disjunction
`q lor r` (via `[from 2]`) plus the two `case` blocks. Each case
derives the target disjunction from the case-introduced formula
referenced as `q [from 2]` / `r [from 2]`.

### Example 4: Modus Tollens

**Goal**: Prove `((p => q) land lnot q) => lnot p`

```text
PROOF:
((p => q) land lnot q) => lnot p [=> intro from 1]
  [1] (p => q) land lnot q [assumption]
  :: lnot p [false elim from 2]
    [2] p [assumption]
    :: false [false-intro]
      :: q [=> elim]
        :: p => q [land elim 1]
          (p => q) land lnot q [from 1]
        :: p [from 2]
      :: lnot q [land elim 2]
        (p => q) land lnot q [from 1]
```

Two discharges nested. `=> intro from 1` discharges `[1]`;
`false elim from 2` discharges `[2]`. Inside, `false-intro` is
binary (`q` and `lnot q`) and `=> elim` is binary (`p => q` and `p`).
Every multi-premise rule has `::` on its premises.

## Indentation Rules

1. **No indent**: Final conclusion
2. **One indent** (2 spaces): Assumptions marked with `[label]`
3. **Two indents** (4 spaces): Derivations within assumption scope
4. **Additional indents**: Nested assumptions or case branches

## AST Structure Needed

```python
@dataclass
class ProofTree:
    conclusion: ProofStep

@dataclass
class ProofStep:
    expression: Expr
    justification: str | None
    label: int | None  # For assumptions: [1], [2], etc.
    is_assumption: bool
    is_sibling: bool  # Marked with ::
    children: list[ProofStep]

@dataclass
class CaseAnalysis:
    cases: list[tuple[str, list[ProofStep]]]  # ("q", steps), ("rcl", steps)
```

## Parser Limitations

### Critical: Spacing After Identifiers Before Brackets

**IMPORTANT**: The parser requires a space between an identifier and an opening bracket `[` to avoid ambiguity with subscript notation.

**Incorrect (will fail):**

```text
p land q[land elim]  // Parser reads this as p with subscript "land q[land"
```

**Correct:**

```text
p land q [land elim]  // Space before [ makes it clear this is a justification
```

This limitation affects:

- Proof justifications: Always write `expression [justification]` with a space
- Any context where brackets follow an identifier

**Workaround**: Add at least one space before the `[` bracket when it's meant to be a justification or label, not a subscript operator.

## LaTeX Generation Strategy

Convert to `\infer` macros from zed-proof.sty:

```latex
$$
\infer[\Rightarrow\text{-intro}]{p \land q \Rightarrow q}{
  \infer[\land\text{-elim}]{q}{p \land q}
}
$$
```

For siblings (marked with `::`), generate side-by-side premises:

```latex
\infer[rule]{conclusion}{
  premise1 & premise2 & premise3
}
```

For cases, generate multiple inference branches combined with lor-elimination.

## Related Block Types

### EQUIV: / ARGUE: (Equivalence Chains)

For step-by-step propositional reasoning where each step is joined by
$\Leftrightarrow$, use `EQUIV:` or its alias `ARGUE:`. See the User Guide.

### EQUAL: (Equality Chains)

For step-by-step equational reasoning where each step is joined by `=`,
use `EQUAL:`. This is appropriate when the steps are expressions of the same
Z type — natural-number arithmetic, sequence lengths, function values — rather
than propositions.

```text
EQUAL:
length s
length (tail s) + 1 [by definition of length]
```

`EQUAL:` produces `=` between steps; `EQUIV:` produces `\Leftrightarrow`.
Use `EQUAL:` for numeric calculations and `EQUIV:` for logical equivalences.
