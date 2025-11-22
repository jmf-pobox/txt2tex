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
The first non-indented line after `PROOF:` is the final conclusion:
```
PROOF:
p and q => q [=> intro from 1]
```

### 3. Assumptions with Labels
Assumptions are marked with `[number]` and the keyword `[assumption]`:
```
[1] p and q [assumption]
```
- The `[1]` is a **label** used to reference this assumption later
- Everything indented under this is "within the scope" of the assumption

### 4. Regular Proof Steps
```
q [and elim]
```
- Statement followed by justification in brackets
- Indentation shows dependency

### 5. Sibling Premises (`::`  marker)
When multiple things need to be proven together (side-by-side in tree):
```
:: p [and elim]
:: q [from case]
p and q [and intro]
```
The `::` means "these are siblings that together support the next step"

### 6. Case Analysis
For or-elimination and case splits:
```
case p:
  :: p => r [and elim 1]
    :: (p => r) and (q => r) [from 1]
  :: r [=> elim]
    [3] p [assumption]
case q:
  :: q => r [and elim 2]
    :: (p => r) and (q => r) [from 1]
  :: r [=> elim]
    [3] q [assumption]
```

**Key pattern for cases with multiple sibling steps:**
- When a case has multiple `::` siblings that build up to a conclusion
- The LAST sibling step automatically wraps earlier siblings as its premises
- Do NOT add explicit "from above" references - they create duplication
- Each case should derive the same conclusion through different paths

### 7. Justifications

Justifications are free-form text enclosed in brackets `[...]`. Any text is accepted, but the following are standard natural deduction rules:

**Basic rules:**
- `[assumption]` - marks assumptions
- `[premise]` - given fact

**Conjunction (and):**
- `[and elim]`, `[and elim left]`, `[and elim right]`, `[and elim 1]`, `[and elim 2]` - and elimination
- `[and intro]` - and introduction

**Disjunction (or):**
- `[or elim]` - or elimination (case analysis)
- `[or intro]`, `[or intro left]`, `[or intro right]`, `[or intro 1]`, `[or intro 2]` - or introduction

**Implication (=>):**
- `[=> intro from N]` - implication introduction, discharging assumption [N]
- `[=> elim]` - implication elimination (modus ponens)

**Negation (not):**
- `[not intro from N]` - negation introduction (proof by contradiction), discharging assumption [N]
- `[not elim]` - negation elimination

**Absurdity (false):**
- `[false elim]` - ex falso quodlibet (from false, derive anything)
- `[contradiction]`, `[contradiction with X]` - deriving false from contradictory statements

**Classical logic:**
- `[LEM]` - Law of Excluded Middle (p or not p axiom)
- `[double negation elim]` - classical rule: not not p implies p

**Derived rules:**
- `[identity]` - trivial identity step (p proves p)
- `[negation intro from N]` - alternative form of not intro

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
**Goal**: Prove `p and q => q`

```
PROOF:
p and q => q [=> intro from 1]
  [1] p and q [assumption]
      q [and elim]
```

**Explanation**:
1. To prove `A => B`, assume A and prove B
2. We assume `p and q` (label it [1])
3. From `p and q`, extract `q` using and-elimination
4. This proves the implication, discharging assumption [1]

### Example 2: With Sibling Premises
**Goal**: Prove `p and (p => q) => (p and q)`

```
PROOF:
p and (p => q) => (p and q) [=> intro from 1]
  [1] p and (p => q) [assumption]
      :: p [and elim]
      :: p => q [and elim]
      q [=> elim]
      p and q [and intro]
```

**Explanation**:
- Assume `p and (p => q)` as [1]
- Extract both `p` and `p => q` (marked as siblings with `::`)
- Apply modus ponens to get `q`
- Combine `p` and `q` to get `p and q`

### Example 3: Distribution with Cases
**Goal**: Prove `p and (q or r) => (p and q) or (p and r)`

```
PROOF:
p and (q or r) => (p and q) or (p and r) [=> intro from 1]
  [1] p and (q or r) [assumption]
      :: p [and elim]
        :: p and (q or r) [from 1]
      :: q or r [and elim]
        :: p and (q or r) [from 1]
      :: (p and q) or (p and r) [or elim]
        case q:
          :: q [case assumption]
          :: p and q [and intro]
          :: (p and q) or (p and r) [or intro]
        case r:
          :: r [case assumption]
          :: p and r [and intro]
          :: (p and q) or (p and r) [or intro]
```

**Explanation**:
- Assume `p and (q or r)` as [1]
- Extract `p` and `q or r` as siblings
- For case analysis on `q or r`:
  - **Case q**: Use case assumption `q`, build `p and q`, then introduce to disjunction
  - **Case r**: Use case assumption `r`, build `p and r`, then introduce to disjunction
- Both cases yield the same result

**Important note on case structure**: When a case has multiple sibling steps (marked with `::`) that derive the case conclusion, the LAST step automatically includes earlier steps as premises. You do NOT need to explicitly reference "from above" - the earlier sibling derivations are automatically available to the final step in the case.

### Example 4: Modus Tollens
**Goal**: Prove `(p => q) and not q => not p`

```
PROOF:
(p => q) and not q => not p [=> intro from 1]
  [1] (p => q) and not q [assumption]
      p => q [and elim]
      not q [and elim]
      not p [negation intro from 2]
        [2] p [assumption]
            q [=> elim]
            false [contradiction]
```

**Explanation**:
- Assume `(p => q) and not q` as [1]
- To prove `not p`, assume `p` (as [2]) and derive contradiction
- From `p` and `p => q`, get `q`
- But we have `not q`, so contradiction
- Therefore `not p`, discharging assumption [2]

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

For cases, generate multiple inference branches combined with or-elimination.
