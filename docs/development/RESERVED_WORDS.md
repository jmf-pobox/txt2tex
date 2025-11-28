# Reserved Words and Operator Mappings

**Last Updated:** 2025-11-26
**Purpose:** Complete reference of all ASCII keywords/operators and their Unicode/LaTeX mappings

---

## Overview

This document lists all reserved words (keywords) and operators in txt2tex. These identifiers have special meaning and cannot be used as variable names.

**Design Principle:** All operators have ASCII keyword alternatives to enable whiteboard-style input without requiring Unicode characters.

---

## Logical Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `and` | ∧ (U+2227) | `\land` | Logical conjunction | 2 |
| `or` | ∨ (U+2228) | `\lor` | Logical disjunction | 2 |
| `not` | ¬ (U+00AC) | `\lnot` | Logical negation | 2 |
| `=>` | → (U+2192) | `\implies` | Logical implication | 2 |
| `<=>` | ↔ (U+2194) | `\iff` / `\Leftrightarrow` | Logical equivalence (context-dependent) | 2 |
| `forall` | ∀ (U+2200) | `\forall` | Universal quantifier | 3 |
| `exists` | ∃ (U+2203) | `\exists` | Existential quantifier | 3 |
| `exists1` | ∃₁ | `\exists_1` | Unique existence quantifier | 3 |

**Notes:**
- `<=>` renders as `\iff` in predicates (schemas, axioms, proofs)
- `<=>` renders as `\Leftrightarrow` in EQUIV blocks (equational reasoning)

---

## Set Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `in` | ∈ (U+2208) | `\in` | Set membership | 3 |
| `notin` | ∉ (U+2209) | `\notin` | Set non-membership | 3 |
| `subset` | ⊆ (U+2286) | `\subseteq` | Subset (includes equality) | 3 |
| `subseteq` | ⊆ (U+2286) | `\subseteq` | Subset (alternative keyword) | 3 |
| `psubset` | ⊂ (U+2282) | `\subset` | Strict/proper subset (excludes equality) | 39 |
| `union` | ∪ (U+222A) | `\cup` | Set union | 3 |
| `intersect` | ∩ (U+2229) | `\cap` | Set intersection | 3 |
| `cross` | × (U+00D7) | `\cross` | Cartesian product | 11.5 |
| `\` | ∖ (U+2216) | `\setminus` | Set difference | 11.5 |

---

## Set Functions

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `P` | ℙ (U+2119) | `\power` | Power set | 11.5 |
| `P1` | ℙ₁ | `\power_1` | Non-empty power set | 11.5 |
| `F` | 𝔽 (U+1D53D) | `\finset` | Finite power set | 11.5 |
| `F1` | 𝔽₁ | `\finset_1` | Non-empty finite power set | 11.5 |
| `bigcup` | ⋃ (U+22C3) | `\bigcup` | Distributed union | 32 |
| `bigcap` | ⋂ (U+22C2) | `\bigcap` | Distributed intersection | 32 |

---

## Relation Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `<->` | ↔ (U+2194) | `\rel` | Relation type | 10 |
| `\|->` | ↦ (U+21A6) | `\mapsto` | Maplet constructor | 10 |
| `<\|` | ◁ (U+25C1) | `\dres` | Domain restriction | 10a |
| `\|>` | ▷ (U+25B7) | `\rres` | Range restriction | 10a |
| `<<\|` | ⩤ (U+2A64) | `\ndres` | Domain subtraction | 10a |
| `\|>>` | ⩥ (U+2A65) | `\nrres` | Range subtraction | 10a |
| `comp` | — | `\comp` | Relational composition (semicolon) | 10 |
| `;` | — | `\comp` | Relational composition | 10 |
| `o9` | ∘ (U+2218) | `\circ` | Forward/backward composition | 10 |
| `~` | — | `\inv` | Relational inverse (postfix) | 10 |
| `(+)` | ⊕ (U+2295) | `\limg` | Relational image | 10 |
| `+)` | — | `\rimg` | Relational image (right) | 10 |

---

## Relation Functions

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `dom` | — | `\dom` | Domain of relation | 10 |
| `ran` | — | `\ran` | Range of relation | 10 |
| `inv` | — | `\inv` | Inverse of relation | 10 |
| `id` | — | `\id` | Identity relation | 10 |

---

## Function Type Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `->` | → (U+2192) | `\fun` | Total function | 10 |
| `+->` | ⇸ (U+21F8) | `\pfun` | Partial function | 10 |
| `77->` | ⇻ (U+21FB) | `\ffun` | Finite partial function | 34 |
| `>->` | ↣ (U+21A3) | `\inj` | Total injection | 10 |
| `-\|>` | ⇾ (U+21FE) | `\pinj` | Partial injection | 10 |
| `>+>` | ⤔ (U+2914) | `\pinj` | Partial injection (alternative) | 10 |
| `-->>` | ↠ (U+21A0) | `\surj` | Total surjection | 10 |
| `+->>` | ⤀ (U+2900) | `\psurj` | Partial surjection | 10 |
| `>->>` | ⤖ (U+2916) | `\bij` | Total bijection | 10 |

---

## Sequence Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `<>` | ⟨⟩ (U+27E8/U+27E9) | `\langle \rangle` | Empty sequence | 12 |
| `<...>` | ⟨...⟩ | `\langle ... \rangle` | Sequence literal | 12 |
| `seq` | — | `\seq` | Sequence type | 12 |
| `seq1` | — | `\seq_1` | Non-empty sequence type | 12 |
| `^` | ⌢ (U+2322) | `\cat` | Sequence concatenation (space-sensitive) | 24 |
| `filter` | ↾ (U+21BE) | `\filter` | Sequence filter | 35 |
| `head` | — | `\head` | First element | 12 |
| `tail` | — | `\tail` | All but first | 12 |
| `last` | — | `\last` | Last element | 12 |
| `front` | — | `\front` | All but last | 12 |
| `rev` | — | `\rev` | Reverse | 12 |

---

## Bag Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `[[...]]` | ⟦...⟧ (U+27E6/U+27E7) | `\lbag ... \rbag` | Bag literal | 12 |
| `bag` | — | `\bag` | Bag type | 12 |
| `bag_union` | ⊎ (U+228E) | `\uplus` | Bag union | 35 |

---

## Arithmetic Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `+` | + | `+` | Addition / Transitive closure | 0, 10 |
| `-` | − (U+2212) | `-` | Subtraction / Negation | 0 |
| `*` | × (U+00D7) | `\times` | Multiplication / Reflexive-transitive closure | 0, 10 |
| `div` | ÷ (U+00F7) | `\div` | Division | 0 |
| `mod` | — | `\bmod` | Modulo | 0 |
| `++` | ⊕ (U+2295) | `\oplus` | Override/function update | 10 |

---

## Comparison Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `=` | = | `=` | Equality | 0 |
| `!=` | ≠ (U+2260) | `\neq` | Inequality | 2 |
| `<` | < | `<` | Less than | 0 |
| `>` | > | `>` | Greater than | 0 |
| `<=` | ≤ (U+2264) | `\leq` | Less than or equal | 0 |
| `>=` | ≥ (U+2265) | `\geq` | Greater than or equal | 0 |

---

## Inference Rule Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `shows` | ⊢ (U+22A2) | `\vdash` | Sequent judgment (turnstile) | Phase 42 |

**Note:** Used in INFRULE blocks for natural deduction inference rules. Cannot be used as a variable name.

---

## Special Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `#` | — | `\#` | Cardinality (prefix) | 3 |
| `lambda` | λ (U+03BB) | `\lambda` | Lambda expression | 11d |
| `mu` | μ (U+03BC) | `\mu` | Definite description | 11d |
| `.` | — | `.` | Tuple projection / Schema selection | 0 |
| `..` | — | `\upto` | Range operator | 13 |

---

## Type Keywords

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `Z` | ℤ (U+2124) | `\num` | Integers | 0 |
| `N` | ℕ (U+2115) | `\nat` | Natural numbers | 0 |
| `N1` | ℕ₁ | `\nat_1` | Positive naturals | 11.5 |

---

## Structural Keywords

| ASCII Keyword | Description | Phase |
|--------------|-------------|-------|
| `given` | Basic type declaration | 4 |
| `axdef` | Axiomatic definition block | 5 |
| `schema` | Schema definition block | 6 |
| `gendef` | Generic definition block | 9 |
| `zed` | Unboxed Z notation block | Phase 4 enhancement |
| `where` | Predicate section separator | 5 |
| `end` | Block terminator | 5 |
| `if` | Conditional expression start | 16 |
| `then` | Conditional expression middle | 16 |
| `else` | Conditional expression alternative | 16 |
| `otherwise` | Conditional expression default | 16 |

---

## Abbreviation and Free Type Operators

| ASCII Keyword | Unicode Alternative | LaTeX Output | Description | Phase |
|--------------|---------------------|--------------|-------------|-------|
| `==` | — | `\defs` | Abbreviation definition | 4 |
| `::=` | — | `::=` | Free type definition | 4 |
| `\|` | — | `\mid` | Free type branch separator | 4 |

---

## Special Syntax

### Text Blocks
- `TEXT:` - Prose paragraph in output
- `TRUTH TABLE:` - Truth table block
- `EQUIV:` - Equivalence chain block
- `PROOF:` - Proof tree block

### Line Continuation
- Indented lines continue the previous line (for predicates, expressions)

### Comments
- `--` - Line comment (in text blocks only)

---

## Reserved Words Summary

**Total Reserved Keywords:** 91+

**Categories:**
- Logical operators: 8
- Set operators/functions: 14
- Relation operators/functions: 20
- Function types: 9
- Sequence operators: 9
- Bag operators: 2
- Arithmetic: 6
- Comparison: 6
- Inference rule operators: 1
- Special operators: 5
- Type keywords: 3
- Structural: 8
- Miscellaneous: 3

---

## Implementation Notes

### Lexer Recognition
All reserved words are recognized by the lexer in `src/txt2tex/lexer.py`:
- Keywords in `_scan_identifier()` method
- Multi-character operators checked before single-character operators
- Longest-match principle applied (e.g., `+->` checked before `->`)

### Z Keywords Set
Reserved words that prevent prose mode triggering (line 871-904 in lexer.py):
```python
z_keywords = {
    "and", "or", "not", "union", "intersect", "in", "notin",
    "subset", "subseteq", "psubset", "cross", "dom", "ran", "inv", "id",
    "comp", "forall", "exists", "exists1", "mu", "lambda",
    "given", "axdef", "schema", "gendef", "zed",
    "where", "end", "if", "then", "else", "otherwise", "mod",
    # ... and more
}
```

### LaTeX Mapping
All operators map to LaTeX commands in `src/txt2tex/latex_gen.py`:
- `BINARY_OPS` dictionary (line 60-140)
- `PRECEDENCE` dictionary (line 175-215)
- Multiple replacement locations for text processing

---

## Usage Guidelines

### Avoid as Variable Names
Do NOT use reserved words as identifiers:
```
❌ BAD:  given = 5           (reserved word)
❌ BAD:  subset = {1, 2}     (reserved word)
❌ BAD:  union = A union B   (reserved word)
❌ BAD:  shows : F ShowId    (reserved word - use "podcasts" or similar)

✅ GOOD: givenSet = 5
✅ GOOD: mySubset = {1, 2}
✅ GOOD: unionSet = A union B
✅ GOOD: podcasts : F ShowId
```

### Case Sensitivity
All reserved words are lowercase. Capitalized versions are valid identifiers:
```
✅ seq   - reserved (sequence type)
✅ Seq   - valid identifier
✅ SEQ   - valid identifier
```

### Multi-Character Operators
Some operators use multiple characters:
```
✅ 77->          - finite partial function (continuous, no spaces)
✅ bag_union      - bag union (underscore connects words)
✅ exists1        - unique existence (digit suffix, no space)
```

---

## See Also

- [USER_GUIDE.md](USER_GUIDE.md) - User-facing syntax guide
- [DESIGN.md](DESIGN.md) - Operator precedence and parsing details
