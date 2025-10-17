# txt2tex User Guide

A comprehensive guide to writing mathematical specifications in txt2tex whiteboard notation.

## Table of Contents

1. [Document Structure](#document-structure)
2. [Text Blocks](#text-blocks)
3. [Propositional Logic](#propositional-logic)
4. [Predicate Logic](#predicate-logic)
5. [Equality](#equality)
6. [Sets and Types](#sets-and-types)
7. [Definitions](#definitions)
8. [Relations](#relations)
9. [Functions](#functions)
10. [Sequences](#sequences)
11. [Schema Notation](#schema-notation)
12. [Proof Trees](#proof-trees)

---

## Document Structure

### Sections
```
=== Introduction and Propositions ===
```
Generates: `\section*{Introduction and Propositions}`

### Solutions
```
** Solution 1 **

Content here...
```
Generates: `\bigskip\noindent\textbf{Solution 1}\medskip`

### Part Labels
```
(a) First part
(b) Second part
(c) Third part
```
Each part gets proper spacing and formatting with `(a)\par\vspace{11pt}`.

---

## Text Blocks

txt2tex provides four types of text blocks for different purposes:

### TEXT: - Smart Text with Formula Detection

Use for normal prose where you want mathematical expressions automatically detected and converted:

```
TEXT: This is a plain text paragraph with => and <=> symbols.
TEXT: The set { x : N | x > 0 } contains positive integers.
TEXT: We know that forall x : N | x >= 0 is true.
```

**Features:**
- Operators converted: `=>` → $\Rightarrow$, `<=>` → $\Leftrightarrow$
- Formulas automatically detected: `{ x : N | x > 0 }` → $\{ x : \mathbb{N} \mid x > 0 \}$
- Sequence literals converted: `<a, b, c>` → $\langle a, b, c \rangle$

### PURETEXT: - Raw Text with LaTeX Escaping

Use for bibliography entries or prose with punctuation that would confuse the lexer:

```
PURETEXT: Simpson, A. (2025) "Lecture notes" & references.
PURETEXT: Author's name, "quoted text", and more.
```

**Features:**
- Escapes LaTeX special characters: `&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`, `\`
- NO formula detection
- NO operator conversion
- Preserves punctuation like quotes, commas, parentheses

### LATEX: - Raw LaTeX Passthrough

Use for custom LaTeX commands, environments, or formatting not supported by txt2tex:

```
LATEX: \begin{center}\textit{Custom formatting}\end{center}
LATEX: \vspace{1cm}
LATEX: \mycustomcommand{arg1}{arg2}
```

**Features:**
- NO escaping - raw LaTeX passed directly through
- Perfect for tikz diagrams, custom environments, special commands

### PAGEBREAK: - Insert Page Break

```
PAGEBREAK:
```

Generates: `\newpage` to start a new page in the PDF.

---

## Propositional Logic

*Lecture 1: Introduction and propositions*

### Basic Operators

```
not p            →  ¬p          (negation)
p and q          →  p ∧ q       (conjunction)
p or q           →  p ∨ q       (disjunction)
p => q           →  p ⇒ q       (implication)
p <=> q          →  p ⇔ q       (equivalence)
```

### Precedence (highest to lowest)

1. `not` (unary)
2. `and`
3. `or`
4. `=>`
5. `<=>` (lowest)

### Examples

```
not p and q      →  (¬p) ∧ q
p and q => r     →  (p ∧ q) ⇒ r
p => q => r      →  p ⇒ (q ⇒ r)    [right-associative]
```

### Truth Tables

```
TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T
```

Generates a centered LaTeX tabular environment with proper formatting.

### Equivalence Chains

```
EQUIV:
p and q
<=> q and p [commutative]
<=> q and p [idempotent]
```

Generates `align*` environment with justifications flush-right.

#### Justifications in Equivalence Chains

Justifications are **free-form text** in square brackets after each step. You can write any reasoning you want:

```
EQUIV:
not (p and q)
<=> (not p) or (not q) [De Morgan]
<=> (not p) or (not q) [idempotence]
<=> (not p) or (not q) or (not r) [associativity]
<=> true [excluded middle]
```

**Common justifications:**
- `[De Morgan]` - De Morgan's laws
- `[distributivity]`, `[distribution]` - Distributive property
- `[commutative]`, `[commutativity]` - Commutative property
- `[associativity]`, `[associative]` - Associative property
- `[idempotence]`, `[idempotent]` - Idempotent property
- `[excluded middle]` - Law of excluded middle
- `[one-point rule]` - One-point rule for quantifiers
- `[arithmetic]` - Arithmetic simplification
- Any custom text describing your reasoning

**Operator conversion:** Logical operators in justifications are automatically converted to LaTeX:
- `and` → $\land$
- `or` → $\lor$
- `not` → $\lnot$
- `=>` → $\Rightarrow$
- `<=>` → $\Leftrightarrow$

Example with operators:
```
<=> p or (not p and q) [and and true]
```
Renders as: $\Leftrightarrow p \lor (\lnot p \land q)$ with justification $[\land$ and true]

---

## Predicate Logic

*Lecture 2: Predicate logic*

### Quantifiers

#### Universal Quantification (∀)

```
forall x : N | x > 0
```
Generates: $\forall x : \mathbb{N} \bullet x > 0$

#### Existential Quantification (∃)

```
exists y : Z | y < 0
```
Generates: $\exists y : \mathbb{Z} \bullet y < 0$

### Multi-Variable Quantifiers

```
forall x, y : N | x = y
exists a, b, c : Z | a = b
```

Comma-separated variables share the same domain.

### Nested Quantifiers

```
forall x : N | exists y : N | x = y
```

**Important:** Nested quantifiers in `and`/`or` expressions must be parenthesized:
```
✅ Correct:   forall x : N | x > 0 and (forall y : N | y > x)
❌ Incorrect: forall x : N | x > 0 and forall y : N | y > x
```

### Declaration and Binding

The colon `:` declares the type of a variable:
```
forall x : N | predicate        [declaration]
{ x : N | predicate }          [set comprehension]
lambda x : N . expression      [lambda expression]
```

---

## Equality

*Lecture 3: Equality*

### Equality Operator

```
x = y            →  x = y
x != y           →  x ≠ y
```

### Unique Existence (∃₁)

"There is a unique value that..."

```
exists1 x : N | x = 5
```
Generates: $\exists_1 x : \mathbb{N} \bullet x = 5$

### Mu Operator (μ)

"The unique value that..."

```
mu x : N | x > 0
```
Generates: $\mu x : \mathbb{N} \bullet x > 0$

---

## Sets and Types

*Lecture 5: Sets and types*

### Set Notation

```
{1, 2, 3}                    →  {1, 2, 3}       [set literal]
{}                           →  {}              [empty set]
```

### Set Membership

```
x in A           →  x ∈ A       ['is an element of']
x notin B        →  x ∉ B       ['not an element of']
```

### Set Relations

```
A subset B       →  A ⊆ B       [subset]
A union B        →  A ∪ B       [union]
A intersect C    →  A ∩ C       [intersection]
A \ B            →  A ∖ B       [set difference]
```

### Power Set

```
P S              →  P S         [power set - set of all subsets]
P1 S             →  P₁ S        [non-empty power set]
F S              →  F S         [set of finite subsets]
```

### Cardinality

```
# S              →  # S         [cardinality of a finite set]
# {1, 2, 3}      →  # {1, 2, 3}
```

### Cartesian Product

```
A cross B        →  A × B       [Cartesian product]
(x, y)           →  (x, y)      [ordered pair]
(a, b, c)        →  (a, b, c)   [tuple]
```

### Tuple Component Selection

```
p.1              →  p.1         [first component]
p.2              →  p.2         [second component]
p.3              →  p.3         [third component]
```

### Set Comprehension

**Set by predicate:**
```
{ x : N | x > 0 }
```
Generates: $\{ x : \mathbb{N} \mid x > 0 \}$

**Set by expression:**
```
{ x : N | x > 0 . x^2 }
```
Generates: $\{ x : \mathbb{N} \mid x > 0 \bullet x^2 \}$

The bullet (`•`) separates the predicate from the expression.

**Multi-variable:**
```
{ x, y : N | x = y }
```

**Without domain:**
```
{ x | x in A }
```

**With maplets:**
```
{1 |-> a, 2 |-> b, 3 |-> c}
```
Generates: $\{1 \mapsto a, 2 \mapsto b, 3 \mapsto c\}$

### Distributed Union and Intersection

```
bigcup S         →  ⋃ S         [distributed union]
```

Note: Distributed intersection is not yet implemented.

### Standard Sets

```
Z                →  ℤ           [the set of integers]
N                →  ℕ           [natural numbers]
```

Note: Use blackboard bold for standard number sets by capitalizing: `N`, `Z`.

---

## Definitions

*Lecture 6: Definitions*

### Basic Type Definition (Given Types)

```
given Person, Company
```
Generates: `\begin{zed}[Person, Company]\end{zed}`

### Abbreviations

```
Pairs == N cross N
```

**With generic parameters:**
```
[X] Pair == X
[X, Y] Product == X cross Y
```

### Free Types

**Simple free types:**
```
Status ::= active | inactive | pending
```

**Recursive free types with constructor parameters:**
```
Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩
List ::= nil | cons⟨N × List⟩
```

Both Unicode `⟨⟩` and ASCII `<>` angle brackets are supported:
```
Tree ::= stalk | leaf<N> | branch<Tree × Tree>
```

---

## Relations

*Lecture 7: Relations*

### Maplet (↦)

```
x |-> y          →  x ↦ y       [maplet - ordered pair constructor]
```

### Relation Type

```
X <-> Y          →  X ↔ Y       [set of all relations between X and Y]
```

### Domain and Range

```
dom R            →  dom R       [domain of relation]
ran R            →  ran R       [range of relation]
```

### Domain and Range Restriction

```
S <| R           →  S ◁ R       [domain restriction]
R |> T           →  R ▷ T       [range restriction]
```

### Domain and Range Corestriction (Anti-restriction)

```
S <<| R          →  S ⩤ R       [domain corestriction]
R |>> T          →  R ⩥ T       [range corestriction]
```

### Relational Inverse

```
R~               →  R⁻¹         [relational inverse - postfix]
inv R            →  inv R       [relational inverse - prefix]
```

### Relational Image

```
R(| S |)         →  R(⦇ S ⦈)    [relational image]
```

**Examples:**
```
parentOf(| {john} |)
R(| {1, 2, 3} |)
(R o9 S)(| A |)
```

### Relational Composition

```
R ; S            →  R ; S       [relational composition]
R o9 S           →  R ∘ S       [relational composition alternative]
```

### Closures

```
R+               →  R⁺          [transitive closure]
R*               →  R*          [reflexive, transitive closure]
```

Note: Reflexive closure (`r`) and symmetric closure (`s`) are not yet implemented.

---

## Functions

*Lecture 8: Functions*

### Function Types

**Partial and Total Functions:**
```
f : X +-> Y      →  X ⇀ Y       [partial function]
f : X -> Y       →  X → Y       [total function]
```

**Injections (one-to-one):**
```
f : X >+> Y      →  X ⤔ Y       [partial injection]
f : X -|> Y      →  X ⤔ Y       [partial injection - alternative]
f : X >-> Y      →  X ↣ Y       [total injection]
```

**Surjections (onto):**
```
f : X +->> Y     →  X ⤀ Y       [partial surjection]
f : X -->> Y     →  X ↠ Y       [total surjection]
```

**Bijections (one-to-one and onto):**
```
f : X >->> Y     →  X ⤖ Y       [total bijection]
```

**Finite Functions:**
Note: Finite functions are not yet implemented.

### Function Application

**Standard application:**
```
f(x)             →  f(x)
g(x, y, z)       →  g(x, y, z)
```

**Important:** Function application requires explicit parentheses - juxtaposition is not supported:
```
✅ Correct:   f(x), dom(R)
❌ Incorrect: f x, dom R
```

**Generic instantiation:**
```
seq(N)           →  seq N
P(X)             →  P X
```

**Type application also requires parentheses:**
```
✅ Correct:   seq(Entry), P(Person)
❌ Incorrect: seq Entry, P Person
```

**Nested application:**
```
f(g(h(x)))       →  f(g(h(x)))
```

**General function application:**

Any expression can be applied as a function:
```
(f ++ g)(x)              [override then apply]
⟨a, b, c⟩(2)             [sequence indexing]
(R o9 S)(| A |)          [composition then image]
```

### Lambda Expressions (λ)

**Basic lambdas:**
```
lambda x : N . x^2
lambda f : X -> Y . f(x)
```

**Multi-variable:**
```
lambda x, y : N . x + y
lambda a, b, c : Z . a
```

**Nested lambdas:**
```
lambda x : X . lambda y : Y . (x, y)
```

### Function Override (⊕)

```
f ++ g           →  f ⊕ g       [function override]
f ++ g ++ h      →  f ⊕ g ⊕ h   [left-associative]
```

The second function takes precedence for overlapping domains.

### Range Operator ('up to')

```
1..10            →  1 ‥ 10      ['up to']
1993..current    →  1993 ‥ current
```

Represents the set `{1, 2, 3, ..., 10}`.

---

## Sequences

*Lecture 9: Sequences*

### Sequence Types

```
seq(X)           →  seq X       [set of all sequences of type X]
iseq(X)          →  iseq X      [set of all injective sequences]
```

**With generic instantiation:**
```
seq[N]
iseq[Entry]
```

### Sequence Literals

**Unicode angle brackets:**
```
⟨⟩               →  ⟨⟩          [empty sequence]
⟨a⟩              →  ⟨a⟩
⟨a, b, c⟩        →  ⟨a, b, c⟩
```

**ASCII angle brackets (alternative):**
```
<>               →  ⟨⟩          [empty sequence]
<a>              →  ⟨a⟩
<a, b, c>        →  ⟨a, b, c⟩
```

Both produce identical LaTeX output.

### Concatenation (⌢)

**Unicode:**
```
⟨a⟩ ⌢ ⟨b⟩       →  ⟨a⟩ ⌢ ⟨b⟩
s ⌢ t            →  s ⌢ t
```

**ASCII (using `^` after sequences):**
```
<a> ^ <b>        →  ⟨a⟩ ⌢ ⟨b⟩
<x> ^ s          →  ⟨x⟩ ⌢ s
```

**Note:** The `^` operator means concatenation only after a sequence closing bracket (`>` or `⟩`). Otherwise it means superscript:
```
<a> ^ <b>        →  concatenation
x^2              →  superscript
```

### Filter

```
s |> A           →  s ⊳ A       [filter]
```

Note: The filter operator syntax may vary.

### Sequence Length

```
# s              →  # s         [length - overloading of cardinality]
```

### Sequence Functions

```
head s           →  head s      [head - first element]
tail s           →  tail s      [tail - all but first]
last s           →  last s      [last element]
front s          →  front s     [all but last]
rev s            →  rev s       [reverse]
```

Note: `reverse` and `squash` functions use abbreviated forms in txt2tex.

### Pattern Matching with Sequences

Sequences enable pattern matching for recursive functions:

**Empty sequence pattern:**
```
f(<>) = 0
```

**Cons pattern (head and tail):**
```
f(<x> ^ s) = x + f(s)
```

**In axiomatic definitions:**
```
axdef
  cumulative_total : seq(N) -> N
where
  cumulative_total(<>) = 0
  forall x : N; s : seq(N) |
    cumulative_total(<x> ^ s) = x + cumulative_total(s)
end
```

### Bags

**Bag type:**
```
bag(X)           →  bag X       [set of all bags of type X]
```

**Bag literals:**
```
[[x]]            →  ⟦x⟧         [bag]
[[a, b, c]]      →  ⟦a, b, c⟧
```

---

## Schema Notation

### Axiomatic Definitions

Define global constants and their properties:

```
axdef
  population : N
where
  population > 0
end
```

**With generic parameters:**
```
axdef [T]
  identity : T
where
  identity = identity
end
```

### Schemas

Define state spaces and operations:

```
schema State
  count : N
where
  count >= 0
end
```

**With generic parameters:**
```
schema Stack[X]
  items : seq X
where
  # items <= 100
end

schema Relation[X, Y]
  domain : P X
  range : P Y
end
```

### Anonymous Schemas

Schemas without names for inline use:

```
schema
  x : N
  y : N
where
  x + y = 10
end
```

### Schema Declarations

The `where` keyword separates declarations from predicates:

```
schema Name
  declarations
where
  predicates
end
```

---

## Proof Trees

Natural deduction proofs using indentation-based syntax.

### Basic Structure

```
PROOF:
  conclusion [rule name]
    premise1
    premise2
```

### Indentation Rules

- **2 spaces per level** for proof structure
- **Siblings:** Use `::` prefix for parallel premises
- **Assumptions:** Label with `[1]`, `[2]`, etc.
- **Discharge:** Reference assumptions with `[=> intro from 1]`
- **References:** Use `[from 1]` to refer to labeled assumptions

### Justifications in Proof Trees

Justifications in proof trees are **free-form text** in square brackets. The system recognizes special patterns for structured rules:

#### Special Formatting Patterns

**Discharge notation** (for assumption elimination):
```
[=> intro from 1]
[=> intro from 2]
[or elim from 2 and 3]
```
Formats as: $\Rightarrow$-intro$^{[1]}$ with superscript reference

**Projection notation** (for left/right selection):
```
[and elim 1]
[and elim 2]
[or intro 1]
[or intro 2]
```
Formats as: $\land$-elim-1 with hyphenated subscript

**General rules:**
```
[assumption]
[premise]
[from 1]
[derived]
[excluded middle]
[contradiction]
```
Free-form text, wrapped in `\text{}` for proper spacing

#### Operator Conversion in Justifications

Logical operators are automatically converted:
- `and` → $\land$
- `or` → $\lor$
- `not` → $\lnot$
- `=>` → $\Rightarrow$
- `<=>` → $\Leftrightarrow$

Examples:
- `[=> intro from 1]` → $\Rightarrow$-intro$^{[1]}$
- `[and elim 1]` → $\land$-elim-1
- `[or elim from 2]` → $\lor$-elim (from 2)

### Supported Rules

**Conjunction:**
- `[and intro]` - introduction
- `[and elim 1]` - left elimination
- `[and elim 2]` - right elimination
- `[and intro from 1 and 3]` - introduction with references

**Disjunction:**
- `[or intro 1]` - left introduction
- `[or intro 2]` - right introduction
- `[or elim]` - elimination (case analysis)
- `[or elim from 2 and 3]` - elimination with references

**Implication:**
- `[=> intro]` - introduction (discharge assumption)
- `[=> intro from 1]` - introduction discharging assumption 1
- `[=> elim]` - modus ponens
- `[=> elim from 1 and 2]` - modus ponens with references

**Falsehood:**
- `[false intro]` - contradiction
- `[false elim]` - explosion (ex falso quodlibet)
- `[false elim from 2]` - explosion with reference

**Other:**
- `[assumption]` - marks an assumption
- `[premise]` - marks a premise
- `[from N]` - reference to line N
- `[derived]` - derived result
- `[excluded middle]` - law of excluded middle
- `[contradiction]` - proof by contradiction

### Example: Simple Proof

```
PROOF:
  p and q => p [=> intro from 1]
    [1] p and q [assumption]
    :: p [and elim 1]
      :: p and q [from 1]
```

### Example: Case Analysis

```
PROOF:
  p or q => r [=> intro from 1]
    [1] p or q [assumption]
    :: r [or elim]
      :: p or q [from 1]
      case p:
        :: r [from 2]
          [2] p [assumption]
      case q:
        :: r [from 3]
          [3] q [assumption]
```

---

## Additional Features

### Conditional Expressions

```
if x > 0 then x else -x
if s = <> then 0 else head s
```

**Nested conditionals:**
```
if x > 0 then 1 else if x < 0 then -1 else 0
```

**In function definitions:**
```
abs(x) = if x > 0 then x else -x
max(x, y) = if x > y then x else y
```

### Subscripts and Superscripts

```
x_i              →  xᵢ
x^2              →  x²
2^n              →  2ⁿ
a_{n}            →  aₙ          [braces group multi-char subscripts]
x^{2n}           →  x²ⁿ         [braces group multi-char superscripts]
```

### Multi-Word Identifiers

Underscores can be used for readable multi-word variable names:

```
cumulative_total             →  cumulative_total
not_yet_viewed               →  not_yet_viewed
employee_count               →  employee_count
```

**Smart rendering:**
- Simple subscript: `a_i` → $a_i$
- Multi-char subscript: `x_max` → $x_{max}$
- Multi-word identifier: `cumulative_total` → $\mathit{cumulative\_total}$

### Comparison Operators

```
x < y            →  x < y
x > y            →  x > y
x <= y           →  x ≤ y
x >= y           →  x ≥ y
```

### Arithmetic Operators

```
x + y            →  x + y       [addition]
x - y            →  x - y       [subtraction]
-x               →  -x          [negation]
x * y            →  x × y       [multiplication]
x mod n          →  x mod n     [modulo]
```

### Generic Type Instantiation

Apply type parameters to polymorphic types:

```
emptyset[N]                  →  ∅[N]
seq[N]                       →  seq[N]
P[X]                         →  P[X]
Type[A, B]                   →  Type[A, B]
```

**Complex parameters:**
```
emptyset[N cross N]          →  ∅[N × N]
seq[N cross N]               →  seq[N × N]
```

**Nested:**
```
Type[List[N]]                →  Type[List[N]]
Container[seq[N]]            →  Container[seq[N]]
```

---

## Quick Reference

### Whitespace Sensitivity

- **Sequence closing:** `<x>` (no space before `>`) vs `x > y` (space before `>`)
- **Generic instantiation:** `Type[X]` (no space before `[`) vs `p [just]` (space before `[`)
- **Concatenation:** `<x> ^` triggers concatenation, `x^2` is superscript

### Parentheses Requirements

- **Function application:** `f(x)` not `f x`
- **Type application:** `seq(N)` not `seq N`
- **Nested quantifiers in and/or:** `p and (forall x : N | P)`

### Common Pitfalls

1. **Forgetting parentheses** in function calls
2. **Nested quantifiers** without proper parenthesization
3. **Smart quotes** in text - use ASCII quotes or PURETEXT blocks
4. **Underscore in identifiers** not supported by fuzz typechecker (but works in txt2tex)

---

## Getting Help

For more information:
- See `README.md` for installation and setup
- See `DESIGN.md` for architecture details
- Check `examples/` directory for working examples
- Review phase-specific test files in `tests/` for syntax examples

