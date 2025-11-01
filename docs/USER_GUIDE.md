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
- Citations supported: `[cite key]` → (Author, Year) in Harvard style

**Citations in TEXT blocks:**

```
TEXT: The proof technique follows [cite simpson25a].
TEXT: This is discussed in [cite simpson25a slide 20].
TEXT: See the definition in [cite spivey92 p. 42].
TEXT: Multiple examples appear in [cite woodcock96 pp. 10-15].
```

Renders as:
- `[cite simpson25a]` → (Simpson, 2025a)
- `[cite simpson25a slide 20]` → (Simpson, 2025a, slide 20)
- `[cite spivey92 p. 42]` → (Spivey, 1992, p. 42)

**Note**: Citation keys match those defined in your bibliography (see LATEX: blocks for bibliography setup). You can add any locator text (slide, p., pp., etc.) after the citation key.

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
- Used for bibliography setup with natbib

**Bibliography Setup (Harvard Style):**

txt2tex automatically includes the `natbib` package for author-year citations. Use LATEX: blocks to define your bibliography:

```
=== Bibliography ===

LATEX: \begin{thebibliography}{Simpson, n.d.}
LATEX:
LATEX: \bibitem[Simpson, 2025a]{simpson25a} Simpson, A. (2025a). \textit{Introduction and propositions}. Lecture 01.
LATEX:
LATEX: \bibitem[Woodcock and Davies, 1996]{woodcock96} Woodcock, J. and Davies, J. (1996). \textit{Using Z}. Prentice Hall.
LATEX:
LATEX: \end{thebibliography}
```

The `\bibitem[Author, Year]{key}` format creates Harvard-style citations. Use `[cite key]` in TEXT: blocks to reference them (see TEXT: section above).

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

**Operator conversion:** Mathematical operators in justifications are automatically converted to LaTeX:

**Logical operators:**
- `and` → $\land$
- `or` → $\lor$
- `not` → $\lnot$
- `=>` → $\Rightarrow$ (or `\implies` in fuzz mode)
- `<=>` → $\Leftrightarrow$ (always, even in fuzz mode for EQUIV blocks)

**Note on fuzz mode**: When using `--fuzz`, implication renders as `\implies` everywhere. Equivalence uses `\Leftrightarrow` in EQUIV blocks (equational reasoning) but `\iff` in predicates.

**Relation operators:**
- `o9` → $\circ$ (composition)
- `|->` → $\mapsto$ (maplet)
- `<->` → $\rel$ (relation type)
- `<|` → $\dres$ (domain restriction)
- `|>` → $\rres$ (range restriction)
- `<<|` → $\ndres$ (domain corestriction)
- `|>>` → $\nrres$ (range corestriction)
- `++` → $\oplus$ (override)

**Function type operators:**
- `->` → $\fun$ (total function)
- `+->` → $\pfun$ (partial function)
- `>->` → $\inj$ (injection)
- `-->>` → $\surj$ (surjection)
- `>->>` → $\bij$ (total bijection)
- `>7->` → $\pbij$ (partial bijection)
- `7 7->` → $\ffun$ (finite partial function)

**Relation functions:**
- `dom`, `ran`, `comp`, `inv`, `id`

Example with logical operators:
```
<=> p or (not p and q) [and and true]
```
Renders as: $\Leftrightarrow p \lor (\lnot p \land q)$ with justification $[\land$ and true]

Example with relation operators:
```
<=> (exists y : Y | w |-> y in (R o9 S) and y |-> z in T) [definition of o9]
```
Renders as: $\Leftrightarrow \exists y : Y \bullet w \mapsto y \in (R \circ S) \land y \mapsto z \in T$ with justification [definition of $\circ$]

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

#### Unique Existential Quantification (∃₁)

```
exists1 x : N | x * x = 4
```
Generates: $\exists_1 x : \mathbb{N} \bullet x \times x = 4$

#### Definite Description (μ)

The mu operator (μ) denotes "the unique value satisfying a predicate":

```
mu x : N | x * x = 4 and x > 0
```

Generates (in fuzz mode): $(\mu x : \mathbb{N} \mid x \times x = 4 \land x > 0)$

**Note**: In fuzz mode, mu expressions use `|` as the separator and are wrapped in parentheses. The syntax is: `mu variable : Type | predicate`

**With expression part** (selecting from a set):
```
mu x : N | x in S . f(x)
```

Generates: `(\mu x : \mathbb{N} \mid x \in S @ f(x))`

The mu operator is typically used when you know there exists exactly one element satisfying the predicate and you want to refer to that element directly.

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
P (A cross B)    →  P (A × B)   [power set of Cartesian product - needs parentheses]
P (Z cross Z)    →  P (ℤ × ℤ)   [set of all relations on integers]
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

### Tuple Component Selection and Field Projection

**Numeric projection (tuples):**
```
p.1              →  p.1         [first component]
p.2              →  p.2         [second component]
p.3              →  p.3         [third component]
```

**Note:** Numeric projections (`.1`, `.2`, `.3`) are **not supported by fuzz** - they violate the fuzz grammar which requires identifiers after the period, not numbers. Use named schema fields instead (see below).

**Named field projection (schemas):**
```
e.name           →  e.name      [access 'name' field]
record.status    →  record.status [access 'status' field]
person.age       →  person.age  [access 'age' field]
```

Named field projections work with schema types:
```
schema Entry
  year: Year
  course: Course
  code: N
end

axdef
  e : Entry
where
  e.year = 2025 and e.code = 479
end
```

**Chained projections:**
```
record.inner.field    →  record.inner.field
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
bigcap S         →  ⋂ S         [distributed intersection]
```

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
Pairs == N cross N      →  Pairs == ℕ × ℕ
```

**With generic parameters:**
```
[X] Pair == X           →  [X] Pair == X
[X, Y] Product == X cross Y  →  [X, Y] Product == X × Y
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

### Generic Definitions

Generic definitions (gendef) define polymorphic functions and constants with type parameters:

**Basic generic definition:**
```
gendef [X, Y]
  fst : X cross Y -> X
where
  forall x : X; y : Y | fst(x, y) = x
end
```

**Note**: Use `|` (pipe) as the separator in quantifiers, not `@`. The LaTeX generator will produce fuzz-compatible output with `@` when using the `--fuzz` flag.

Generates:
```latex
\begin{gendef}[X, Y]
fst: X \cross Y \fun X
\where
\forall x : X @ \forall y : Y @ fst(x, y) = x \\
\end{gendef}
```

**Single type parameter:**
```
gendef [X]
  identity : X -> X
where
  forall x : X | identity(x) = x
end
```

**Multiple declarations (separate lines):**
```
gendef [X, Y]
  fst : X cross Y -> X
  snd : X cross Y -> Y
where
  forall x : X; y : Y | fst(x, y) = x and snd(x, y) = y
end
```

**Multiple declarations (semicolon-separated on one line):**
```
gendef [X, Y]
  fst : X cross Y -> X; snd : X cross Y -> Y
where
  forall x : X; y : Y | fst(x, y) = x and snd(x, y) = y
end
```

Generates:
```latex
\begin{gendef}[X, Y]
  fst: X \cross Y \fun X \\
  snd: X \cross Y \fun Y
\where
  \forall x : X @ \forall y : Y @ fst(x, y) = x \land snd(x, y) = y \\
\end{gendef}
```

**Note:** Both separate lines and semicolon-separated formats in the input generate the same LaTeX output - declarations appear on separate lines with `\\` line breaks. This ensures proper rendering in PDF where each declaration appears on its own line.

Generic definitions are used for:
- Polymorphic functions (like `fst`, `snd`, `head`, `tail`)
- Generic constants that work across types
- Type-parameterized operations

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
R o9 S           →  R ∘ S       [relational composition]
R comp S         →  R ∘ S       [relational composition alternative]
```

**Note:** Semicolon (`;`) is NOT supported for relational composition - it is reserved for separating declarations in `gendef`, `axdef`, and `schema` blocks. Always use `o9` or `comp` for relational composition.

**Composition vs Nested Application:**

| Syntax | Meaning | Type | Usage |
|--------|---------|------|-------|
| `g o9 f` | Function composition | `A -> C` (function) | Creates new function |
| `g(f(x))` | Nested application | `C` (value) | Computes specific result |

**Example:**
```
successor : N -> N
square : N -> N

squareSuccessor == square o9 successor    ← Defines a new function
result = square(successor(5))             ← Computes the value 36
```

Both evaluate the same when applied to arguments: `(g o9 f)(x) = g(f(x))`, but composition creates a reusable function while nested application computes a specific value.

### Closures

```
R+               →  R⁺          [transitive closure]
R*               →  R*          [reflexive, transitive closure]
```

Note: Reflexive closure (`r`) and symmetric closure (`s`) are not yet implemented.

### Compound Identifiers in Definitions

Postfix operators (`+`, `*`, `~`) can be used as part of identifier names in abbreviations and schema definitions:

```
R+ == {a, b : N | b > a}         →  R⁺ ≙ {a, b : ℕ | b > a}
R* == R+ union id[N]             →  R* ≙ R⁺ ∪ id[ℕ]
R~ == inv R                      →  R⁻¹ ≙ inv R

schema S+                        →  \begin{schema}{S⁺}
  x : N
end
```

**Context matters:** The same operator has different meanings in different contexts:

| Context | Syntax | Meaning | LaTeX |
|---------|--------|---------|-------|
| Abbreviation name | `R+ == expr` | Name is "R+" | `R⁺` |
| Expression | `S == R+` | Transitive closure operator | `R⁺` |
| Binary operator | `x + y` | Addition | `x + y` |

**Examples:**
```
# R+ is the abbreviation name (compound identifier)
R+ == {a, b : N | b > a}

# R+ in expression context (operator applied to R)
S == R+

# Works with underscores
rel_1+ == {x, y : N | x < y}     →  rel_1⁺
```

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
f : X >7-> Y     →  X ↣→ Y      [partial bijection]
```

**Finite partial functions:**
```
f : Year 7 7-> Table     →  Year ⇸ Table    [finite partial function]
```

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

### Function Definitions

Functions are typically defined using `axdef` or `gendef` (for generic functions).

**Simple total function:**
```
axdef
  square : N -> N
where
  forall n : N | square(n) = n * n
end
```

**Partial function:**
```
axdef
  predecessor : N +-> N
where
  forall n : N | n > 0 => predecessor(n) = n - 1
end
```

Note: `predecessor` is partial because 0 has no predecessor in N.

**Generic function:**
```
gendef [X]
  identity : X -> X
where
  forall x : X | identity(x) = x
end
```

**Generic function with multiple type parameters:**
```
gendef [X, Y]
  first : X cross Y -> X
where
  forall x : X; y : Y | first(x, y) = x
end
```

### Function Operators

**Domain and Range:**
```
dom f            →  dom f       [domain of function]
ran f            →  ran f       [range of function]
```

**Domain Restriction:**
```
A <| f           →  A ⩤ f       [restrict f to domain A]
```

**Range Restriction:**
```
f |> B           →  f ⩥ B       [restrict f to range B]
```

**Domain Subtraction:**
```
A <-| f          →  A ⩤ f       [remove A from domain]
```

**Range Subtraction:**
```
f |->> B         →  f ⩥ B       [remove B from range]
```

**Function Composition:**
```
f o9 g           →  f ∘ g       [forward composition: (f ; g)(x) = g(f(x))]
f o g            →  f ∘ g       [backward composition: (f ∘ g)(x) = f(g(x))]
```

**Function Inverse:**
```
f~               →  f⁻¹         [inverse function (only for injective)]
```

**Relational Image:**
```
f(| A |)         →  f⟦A⟧        [image of set A under f]
```

### Examples of Function Properties

**Injective (one-to-one):**
```
given StudentId, Student

axdef
  studentRecord : StudentId >-> Student
where
  forall id1, id2 : StudentId |
    id1 /= id2 => studentRecord(id1) /= studentRecord(id2)
end
```

**Surjective (onto):**
```
axdef
  modulo3 : N -->> {0, 1, 2}
where
  forall n : N | modulo3(n) = n mod 3 and
  forall r : {0, 1, 2} | exists n : N | modulo3(n) = r
end
```

**Recursive function on sequences:**
```
gendef [X]
  length : seq X -> N
where
  length(<>) = 0 and
  forall x : X; s : seq X | length(<x> ^ s) = 1 + length(s)
end
```

**Higher-order function:**
```
gendef [X, Y, Z]
  compose : (Y -> Z) cross (X -> Y) -> (X -> Z)
where
  forall f : Y -> Z; g : X -> Y; x : X |
    compose(f, g)(x) = f(g(x))
end
```

**See [examples/08_functions/function_definitions_simple.txt](examples/08_functions/function_definitions_simple.txt) for working function examples that pass fuzz validation.**

**Note:** Additional advanced examples are available in function_definitions.txt and function_operators.txt, but may require further refinement for full fuzz compatibility.

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

**Unicode operator (always works):**
```
⟨a⟩ ⌢ ⟨b⟩       →  ⟨a⟩ ⌢ ⟨b⟩
s ⌢ t            →  s ⌢ t
```

**ASCII alternative using `^` (whitespace-sensitive):**

The `^` operator has dual meaning based on whitespace:

| Pattern | Meaning | LaTeX | Example |
|---------|---------|-------|---------|
| `... ^ ...` (with space) | Concatenation | `\cat` | `<x> ^ <y>` |
| `...^...` (no space) | Exponentiation | `^{...}` | `x^2` |

**Concatenation examples (MUST have space before `^`):**
```
<a> ^ <b>        →  ⟨a⟩ ⌢ ⟨b⟩      [sequence literals]
s ^ t            →  s ⌢ t           [sequence variables]
f(x) ^ <y>       →  f(x) ⌢ ⟨y⟩     [function result]
<x>              →  ⟨x⟩ ⌢ ⟨y⟩      [line break counts as space]
 ^ <y>
```

**Exponentiation examples (NO space before `^`):**
```
x^2              →  x²
4^2              →  4²
n^k              →  nᵏ
(x+1)^2          →  (x+1)²
```

**Common mistake:**
```
❌ <x>^<y>       →  ERROR: "use '> ^ <' not '>^<'"
✅ <x> ^ <y>     →  ⟨x⟩ ⌢ ⟨y⟩
```

**Note:** If typing `⌢` (U+2040) is difficult, remember you can use ` ^ ` (with spaces) as ASCII alternative.

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

### Zed Blocks (Unboxed Paragraphs)

Zed blocks provide a way to write standalone Z notation content without the visual boxing of axdef/schema blocks.

**What can go in zed blocks:**
- ✅ **Predicates**: `forall x : N | x >= 0`
- ✅ **Abbreviations**: `Evens == { n : N | n mod 2 = 0 }`
- ✅ **Type declarations**: `[NAME, DATE]`
- ❌ **NOT bare expressions**: Cannot use standalone `{ x : N | x > 0 }` or `x + y`

**Simple predicate:**
```
zed
  x > 0
end
```

**Quantified predicates:**
```
zed
  forall x : N | x >= 0
end
```

```
zed
  exists n : NAME | birthday(n) in December
end
```

**Abbreviations (assignment):**
```
zed
  Evens == { n : N | n mod 2 = 0 }
end
```

**Complex predicates:**
```
zed
  forall x : S | exists y : T | x in y
end
```

Generates:
```latex
\begin{zed}
  \forall x : S \mid \exists y : T \mid x \in y
\end{zed}
```

**Key differences from axdef/schema:**
- No visual box in PDF output
- No separate declaration and where sections
- Content must be a predicate or abbreviation (not a bare expression)
- Typically used for global constraints or simple definitions

### Container Comparison: What Goes Where

| Content Type | zed | axdef | schema | Standalone |
|--------------|-----|-------|--------|------------|
| **Predicates** | ✅ `forall x : N \| x >= 0` | ✅ In `where` clause | ✅ In `where` clause | ✅ Direct |
| **Abbreviations** | ✅ `Evens == {...}` | ❌ Use top-level | ❌ Use top-level | ✅ Direct |
| **Type declarations** | ✅ `[NAME, DATE]` | ❌ Use `given` | ❌ Use `given` | ✅ `given` |
| **Variable declarations** | ❌ | ✅ Before `where` | ✅ Before `where` | ❌ |
| **Bare expressions** | ❌ | ❌ | ❌ | ✅ Direct |
| **Set comprehensions** | ❌ Alone ✅ In abbrev | ✅ In `where` clause | ✅ In `where` clause | ✅ Direct |
| **Visual box in PDF** | ❌ No box | ✅ Boxed | ✅ Boxed | ❌ No box |

**Examples:**

**Standalone (no container):**
```
{ x : N | x > 0 . x * x }          ← Bare expression, renders inline
```

**Zed block (unboxed paragraph):**
```
zed
  forall x : N | x >= 0            ← Predicate: OK
end

zed
  Evens == { n : N | n mod 2 = 0 } ← Abbreviation: OK
end

zed
  { x : N | x > 0 }                ← ERROR: Bare expression not allowed
end
```

**Axdef (boxed, with declarations):**
```
axdef
  SquaresOfEvens : P Z             ← Declaration required
where
  SquaresOfEvens = { z : Z | z mod 2 = 0 . z * z }  ← Expression in where: OK
end
```

**Schema (boxed, with declarations):**
```
schema State
  count : N                        ← Declaration required
where
  count >= 0                       ← Predicate in where: OK
end
```

**Key principle:**
- **zed blocks** are for predicates and abbreviations that don't need variable declarations
- **axdef/schema** are for definitions with typed variable declarations
- **Standalone** (no container) is for expressions you want rendered inline with math mode

### Scoping Rules: Schema vs Axdef

**CRITICAL: Understanding scope is essential for fuzz validation.**

**Named schemas** have **LOCAL scope** - components are encapsulated within the schema and cannot be referenced outside:

```
schema PodcastPlatform
  shows : F ShowId
  show_episodes : ShowId +-> F EpisodeId
where
  shows subset dom show_episodes
end

** Later in document **
Answer == {s : dom show_episodes | ...}  ❌ FUZZ ERROR: show_episodes not declared
```

The identifiers `shows` and `show_episodes` exist only within the `PodcastPlatform` schema. They are LOCAL components that define the schema's type structure.

**axdef blocks** have **GLOBAL scope** - all declared identifiers are accessible throughout the entire document:

```
axdef
  shows : F ShowId
  show_episodes : ShowId +-> F EpisodeId
where
  shows subset dom show_episodes
end

** Later in document **
Answer == {s : dom show_episodes | ...}  ✅ OK: show_episodes is globally accessible
```

All identifiers declared in `axdef` are GLOBAL and can be referenced anywhere after the declaration.

**When to use which:**

- **Use schema** to define reusable types/templates (like data structures or state spaces) that represent encapsulated components
- **Use axdef** to declare global constants, variables, or functions that need to be referenced elsewhere in your specification

**Other globally scoped declarations:**
- `given` types → `given ShowId, PeopleId`
- Abbreviations → `EpisodeId == N1`
- Generic definitions → `gendef [X, Y] fst : X cross Y -> X`
- Free types → `Color ::= red | blue | green`

**Common mistake:** Using a named schema when you need global identifiers. If other parts of your specification need to reference the declared components, use `axdef` instead.

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

**Multiple declarations (semicolon-separated):**
```
axdef
  x : N; y : N
where
  x > y
end
```

Generates:
```latex
\begin{axdef}
  x : \mathbb{N} \\
  y : \mathbb{N}
\where
  x > y \\
\end{axdef}
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

**Important:** Schema components (`count` in this example) have LOCAL scope and cannot be referenced outside the schema. If you need globally accessible identifiers, use `axdef` instead (see "Scoping Rules" above).

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

**Multiple declarations (semicolon-separated):**
```
schema Point
  x : N; y : N
where
  x > 0 and y > 0
end
```

Generates:
```latex
\begin{schema}{Point}
  x : \mathbb{N} \\
  y : \mathbb{N}
\where
  x > 0 \land y > 0
\end{schema}
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

Mathematical operators in justifications are automatically converted to LaTeX symbols:

**Logical operators:**
- `and` → $\land$
- `or` → $\lor$
- `not` → $\lnot$
- `=>` → $\Rightarrow$ (or `\implies` in fuzz mode)
- `<=>` → $\Leftrightarrow$ (or `\iff` in fuzz mode)

**Note**: In `--fuzz` mode, predicates use `\implies` and `\iff` to match fuzz package conventions.

**Relation operators:**
- `o9` → $\circ$ (composition)
- `|->` → $\mapsto$ (maplet)
- `<->` → $\rel$ (relation type)
- `<|` → $\dres$, `|>` → $\rres$, `<<|` → $\ndres$, `|>>` → $\nrres$
- `++` → $\oplus$ (override)

**Function type operators:**
- `->` → $\fun$, `+->` → $\pfun$, `>->` → $\inj$, `-->>` → $\surj$, `>->>` → $\bij$, `>7->` → $\pbij$, `7 7->` → $\ffun$

**Relation functions:**
- `dom`, `ran`, `comp`, `inv`, `id`

Examples:
- `[=> intro from 1]` → $\Rightarrow$-intro$^{[1]}$
- `[and elim 1]` → $\land$-elim-1
- `[or elim from 2]` → $\lor$-elim (from 2)
- `[definition of o9]` → [definition of $\circ$]
- `[definition of |->]` → [definition of $\mapsto$]

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

**Simple case analysis:**
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

**Case analysis with multiple sibling steps:**
```
PROOF:
  ((p => r) and (q => r)) => ((p or q) => r) [=> intro from 1]
    [1] (p => r) and (q => r) [assumption]
    :: (p or q) => r [=> intro from 2]
      [2] p or q [assumption]
      :: r [or elim from 3]
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

**Important**: When a case has multiple sibling steps (marked with `::`) leading to the conclusion:
- The LAST sibling step automatically includes earlier siblings as its premises
- Do NOT write `:: result [from above]` - this creates duplication
- The earlier derivations are automatically available to the final step

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
- **Caret operator:** `s ^ t` (space before `^`) is concatenation, `x^2` (no space) is exponentiation

### Parentheses Requirements

- **Function application:** `f(x)` not `f x`
- **Type application:** `seq(N)` not `seq N`
- **Nested quantifiers in and/or:** `p and (forall x : N | P)`

### Common Pitfalls

1. **Forgetting parentheses** in function calls
2. **Nested quantifiers** without proper parenthesization
3. **Smart quotes** in text - use ASCII quotes or PURETEXT blocks
4. **Underscore in identifiers** not supported by fuzz typechecker (but works in txt2tex)
5. **Concatenation without space** - `<x>^<y>` is an error, use `<x> ^ <y>` with spaces

---

## Getting Help

For more information:
- See `README.md` for installation and setup
- See `DESIGN.md` for architecture details
- Check `examples/` directory for working examples
- Review phase-specific test files in `tests/` for syntax examples

