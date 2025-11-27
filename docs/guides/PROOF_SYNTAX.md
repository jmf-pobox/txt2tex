# Phase 5: Proof Trees - Path C Syntax Specification

## Overview

Path C uses a **hybrid approach** combining:
- Vertical indentation for nested reasoning
- `::` markers for sibling premises (things proven together)
- `[label]` for assumptions that get discharged
- Natural reading order (top-to-bottom)

## Basic Structure

```
PROOF:
conclusion [justification]
  [label] assumption [assumption]
      derived-statement [justification]
      ...
```

## Syntax Elements

### 1. Proof Header
```
PROOF:
```
Marks the beginning of a proof tree.

### 2. Conclusion (Top Level)
The conclusion is the top-level statement of the proof. It may appear:
- At the beginning (most common): Shows what we're proving, with the proof deriving it
- At the end: Some proofs build up to the conclusion as the final step

```
PROOF:
p land q => q [=> intro from 1]
  [1] p land q [assumption]
      q [land elim]
```

In this example, `p land q => q` is the conclusion we're proving.

### 3. Assumptions with Labels
Assumptions are marked with `[number]` and the keyword `[assumption]`:
```
[1] p land q [assumption]
```
- The `[1]` is a **label** used to reference this assumption later
- Everything indented under this is "within the scope" of the assumption

### 4. Regular Proof Steps
```
q [land elim]
```
- Statement followed by justification in brackets
- Indentation shows dependency

### 5. Sibling Premises (`::`  marker)
When multiple things need to be proven together (side-by-side in tree):
```
:: p [land elim]
:: q [from case]
p land q [land intro]
```
The `::` means "these are siblings that together support the next step"

### 6. Case Analysis
For lor-elimination and case splits:
```
case p:
  :: p => r [land elim 1]
    :: (p => r) land (q => r) [from 1]
  :: r [=> elim]
    [3] p [assumption]
case q:
  :: q => r [land elim 2]
    :: (p => r) land (q => r) [from 1]
  :: r [=> elim]
    [3] q [assumption]
```

**Key pattern for cases with "from above":**
- Use `[from above]` to reference facts established before the case analysis
- The `::` marker indicates sibling premises that together support a step
- Each case should derive the same conclusion through different reasoning paths
- Facts derived before the case split remain available within all cases

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

### Example 1: Simple Implication
**Goal**: Prove `p land q => q`

```
PROOF:
p land q => q [=> intro from 1]
  [1] p land q [assumption]
      q [land elim]
```

**Explanation**:
1. To prove `A => B`, assume A and prove B
2. We assume `p land q` (label it [1])
3. From `p land q`, extract `q` using land-elimination
4. This proves the implication, discharging assumption [1]

### Example 2: With Sibling Premises
**Goal**: Prove `p land (p => q) => (p land q)`

```
PROOF:
p land (p => q) => (p land q) [=> intro from 1]
  [1] p land (p => q) [assumption]
      :: p [land elim]
      :: p => q [land elim]
      q [=> elim]
      p land q [land intro]
```

**Explanation**:
- Assume `p land (p => q)` as [1]
- Extract both `p` and `p => q` (marked as siblings with `::`)
- Apply modus ponens to get `q`
- Combine `p` and `q` to get `p land q`

### Example 3: Distribution with Cases
**Goal**: Prove `p land (q lor r) => (p land q) lor (p land r)`

```
PROOF:
p land (q lor r) => (p land q) lor (p land r) [=> intro from 1]
  [1] p land (q lor r) [assumption]
      p [land elim 1]
      q lor r [land elim 2]
      (p land q) lor (p land r) [lor elim]
        case q:
          :: p [from above]
          :: q [from case]
          p land q [land intro]
          (p land q) lor (p land r) [lor intro 1]
        case r:
          :: p [from above]
          :: r [from case]
          p land r [land intro]
          (p land q) lor (p land r) [lor intro 2]
```

**Explanation**:
- Assume `p land (q lor r)` as [1]
- Extract `p` and `q lor r` from the assumption
- Perform case analysis on `q lor r`:
  - **Case q**: Use `p` from above and case assumption `q`, build `p land q`, then introduce to disjunction
  - **Case r**: Use `p` from above and case assumption `r`, build `p land r`, then introduce to disjunction
- Both cases derive the same conclusion

**Important note on case structure**: Within each case, use `[from above]` to reference facts established before the case analysis began. The `::` sibling markers indicate multiple facts that together support the next inference step.

### Example 4: Modus Tollens
**Goal**: Prove `(p => q) land lnot q => lnot p`

```
PROOF:
(p => q) land lnot q => lnot p [=> intro from 1]
  [1] (p => q) land lnot q [assumption]
      p => q [land elim]
      lnot q [land elim]
      lnot p [negation intro from 2]
        [2] p [assumption]
            q [=> elim]
            false [contradiction]
```

**Explanation**:
- Assume `(p => q) land lnot q` as [1]
- To prove `lnot p`, assume `p` (as [2]) and derive contradiction
- From `p` and `p => q`, get `q`
- But we have `lnot q`, so contradiction
- Therefore `lnot p`, discharging assumption [2]

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
```
p land q[land elim]  // Parser reads this as p with subscript "land q[land"
```

**Correct:**
```
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
