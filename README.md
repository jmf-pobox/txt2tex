# txt2tex

Convert whiteboard-style mathematical notation to high-quality LaTeX for formal methods and Z notation.

## Current Status: Phase 17 ✅

**Production Ready: Solutions 1-36, 44-47 (77%)** - Fully inline parsing support for propositional logic, truth tables, equivalence chains, quantifiers, equality, proof trees, set comprehension, generic parameters, relation operators, function types, lambda expressions, tuples, set literals, relational image, generic type instantiation, **sequences, bags, tuple projection**, anonymous schemas, range operator, override operator, general function application, **ASCII sequence brackets**, **multi-word identifiers with underscore**, **conditional expressions (if/then/else)**, and **recursive free types with constructor parameters**.

### Coverage Breakdown

- 🎯 **24 phases complete** (Phase 0-9, 10a-b, 11a-d, 11.5-11.9, 12, 13.1-13.4, 14, 15, 16, 17)
- ✅ **773 tests passing** (100% pass rate)
- 📚 **19+ example files** demonstrating all features
- 🔧 **Makefile automation** for building PDFs

**Solution Coverage (Verified)**:
- ✅ **Solutions 1-36**: 69% - Fully working with inline parsing
- ⚠️ **Solutions 37-39**: 6% - Partial (some parts require additional sequence operators)
- ⚠️ **Solutions 40-43**: 8% - Partial (require state machines and schema operations)
- ✅ **Solutions 44-47**: 8% - Fully working (recursive free types with constructor parameters)
- ❌ **Solutions 48-52**: 10% - Partial/blocked (require pattern matching and advanced features)

**Overall: ~77% solution coverage** (40/52 solutions, including partial Solutions 44-47)

## Quick Start

### 🚨 Proper Conversion Workflow

**Always use the shell script or hatch command - never manually invoke pdflatex!**

```bash
# Method 1: Shell script (recommended)
./txt2pdf.sh examples/phase9.txt

# Method 2: Hatch command
hatch run convert examples/phase9.txt
```

The `txt2pdf.sh` script automatically:
- Sets PYTHONPATH for the CLI
- Generates LaTeX from txt
- Sets TEXINPUTS and MFINPUTS for packages
- Compiles to PDF
- Cleans up auxiliary files

### Using the Shell Script (Options)

```bash
# Convert txt to PDF in one command
./txt2pdf.sh examples/phase9.txt

# Use fuzz package instead of zed-*
./txt2pdf.sh myfile.txt --fuzz
```

### Using Hatch CLI

```bash
# Convert and compile to PDF
hatch run cli input.txt

# Generate LaTeX only
hatch run cli input.txt --latex-only
```

### Using Make

```bash
# In examples/ directory - build all phase examples
cd examples && make

# Build specific phase
make phase8

# Parallel build
make -j4

# In hw/ directory - build solutions
cd hw && make
```

## Syntax Requirements & Limitations

### Function and Type Application

**Function application requires explicit parentheses** - juxtaposition (whitespace) is not supported:

```
✅ Correct:   f(x), cumulative_total(s), dom(R)
❌ Incorrect: f x, cumulative_total s, dom R
```

**Type application also requires parentheses**:

```
✅ Correct:   seq(Entry), P(Person)
❌ Incorrect: seq Entry, P Person
```

### Nested Quantifiers

**Nested quantifiers in `and`/`or` expressions must be parenthesized**:

```
✅ Correct:   forall x : N | x > 0 and (forall y : N | y > x)
❌ Incorrect: forall x : N | x > 0 and forall y : N | y > x
```

**Current limitation**: Deeply nested quantifiers with multiple bindings may not parse correctly:

```
❌ Not yet supported: forall i : T | forall x, y : U(i) | P
✅ Workaround: Use TEXT blocks for complex nested quantifiers
```

### Fuzz Typechecker Compatibility

When using `--fuzz` flag for typechecking:

**Identifiers with underscores are NOT supported by fuzz**:
- `cumulative_total` will cause fuzz validation errors
- The fuzz typechecker does not recognize underscores in identifiers

**Recommended conventions for fuzz-compatible code**:

Following the conventions used in the fuzz package test suite:

1. **camelCase with initial capital** (for schemas and types):
   ```
   ✅ BirthdayBook, AddBirthday, CheckSys
   ```

2. **camelCase with initial lowercase** (for multi-word functions/variables):
   ```
   ✅ cumulativeTotal instead of cumulative_total
   ✅ maxHeight instead of max_height
   ✅ childOf instead of child_of
   ```

3. **Single-word identifiers** (preferred when possible):
   ```
   ✅ total, height, known, birthday, working
   ```

4. **Subscripts** (for indexed variables and variants):
   ```
   ✅ x_i, x_max, a_1
   ✅ BirthdayBook1, CheckSys1 (variant/refinement schemas)
   ```

**Note**: Free types can use escaped underscores in constructor names (e.g., `REPORT ::= ok | already\_known`) as this is LaTeX syntax, not an identifier.

**If you don't need fuzz validation**:
- Use underscores freely: `cumulative_total`, `child_of`, etc.
- Generate PDF without `--fuzz` flag
- LaTeX rendering works perfectly with underscores

**LaTeX generation works correctly** with underscores for both modes:
- Without `--fuzz`: Generates `\mathit{cumulative\_total}` for pdflatex
- With `--fuzz`: Generates `cumulative_total` for fuzz package (but fuzz will reject it)

**Note**: This is a fuzz limitation, not a txt2tex limitation. The tool fully supports underscores in identifiers.

### Known Limitations (Implementation Needed)

The following features are not yet implemented and require TEXT blocks as workarounds:

**1. Pattern Matching in Function Definitions** (affects Solutions 44-47):
```
✅ Implemented: Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩  (recursive free types)
❌ Not implemented: Pattern matching equations for recursive functions
✅ Workaround: Use conditional expressions (if/then/else) or TEXT blocks
```

**2. Advanced State Machine Operations** (affects Solutions 40-43):
```
❌ Not implemented: Schema operations (Delta, Xi), state transitions
✅ Workaround: Use TEXT blocks
```

See [ROADMAP.md](ROADMAP.md) for implementation plans and [BUGS.md](BUGS.md) for complete list of known issues.

## User Guide: Text Format

### Document Structure

#### Sections
```
=== Section Title ===
```
Generates: `\section*{Section Title}`

#### Solutions
```
** Solution 1 **

Content here...
```
Generates: `\bigskip\noindent\textbf{Solution 1}\medskip`

#### Part Labels
```
(a) First part
(b) Second part
(c) Third part
```
Generates: `(a)\par\vspace{11pt}` with proper spacing

#### Text Paragraphs
```
TEXT: This is a plain text paragraph with => and <=> symbols.
```
Operators in TEXT are converted: `=>` → `$\Rightarrow$`, `<=>` → `$\Leftrightarrow$`

**Inline Math in TEXT** (Phase 8+): Math expressions are automatically detected and converted:
```
TEXT: The set { x : N | x > 0 } contains positive integers.
TEXT: We know that forall x : N | x >= 0 is true.
```
Generates: `$\{ x \colon N \mid x > 0 \}$` and `$\forall x \colon N \bullet x \geq 0$`

---

### Propositional Logic (Phase 0)

#### Operators
```
p and q          →  p ∧ q
p or q           →  p ∨ q
not p            →  ¬p
p => q           →  p ⇒ q
p <=> q          →  p ⇔ q
```

#### Precedence (highest to lowest)
1. `not` (unary)
2. `and`
3. `or`
4. `=>`
5. `<=>` (lowest)

#### Examples
```
not p and q      →  (¬p) ∧ q
p and q => r     →  (p ∧ q) ⇒ r
p => q => r      →  p ⇒ (q ⇒ r)  [right-associative]
```

---

### Truth Tables (Phase 1)

```
TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T
```

Generates a centered LaTeX tabular environment with proper formatting.

---

### Equivalence Chains (Phase 2)

```
EQUIV:
p and q
<=> q and p [commutative]
<=> q and p [idempotent]
```

Generates `align*` environment with justifications:
```latex
\begin{align*}
p \land q \\
&\Leftrightarrow q \land p && \text{[commutative]} \\
&\Leftrightarrow q \land p && \text{[idempotent]}
\end{align*}
```

Operators in justifications (`and`, `or`, `not`, `=>`, `<=>`) are automatically converted to LaTeX symbols.

---

### Quantifiers (Phase 3, 6, 7)

#### Basic Quantifiers
```
forall x : N | x > 0           →  ∀ x : ℕ • x > 0
exists y : Z | y < 0           →  ∃ y : ℤ • y < 0
exists1 x : N | x = 5          →  ∃₁ x : ℕ • x = 5
mu x : N | x > 0               →  μ x : ℕ • x > 0
```

#### Multi-Variable Quantifiers (Phase 6)
```
forall x, y : N | x = y        →  ∀ x, y : ℕ • x = y
exists a, b, c : Z | a = b     →  ∃ a, b, c : ℤ • a = b
```

#### Nested Quantifiers
```
forall x : N | exists y : N | x = y
```

---

### Mathematical Notation (Phase 3, 7)

#### Subscripts and Superscripts
```
x_i              →  xᵢ
x^2              →  x²
2^n              →  2ⁿ
a_{n}            →  aₙ  (braces group multi-char subscripts)
x^{2n}           →  x²ⁿ (braces group multi-char superscripts)
```

#### Comparison Operators
```
x < y            →  x < y
x > y            →  x > y
x <= y           →  x ≤ y
x >= y           →  x ≥ y
x = y            →  x = y
x != y           →  x ≠ y
```

#### Set Operators (Phase 3, 7)
```
x in A           →  x ∈ A
x notin B        →  x ∉ B
A subset B       →  A ⊆ B
A union B        →  A ∪ B
A intersect C    →  A ∩ C
```

---

### Set Comprehension (Phase 8)

#### Set by Predicate
```
{ x : N | x > 0 }              →  { x : ℕ | x > 0 }
```

#### Set by Expression
```
{ x : N | x > 0 . x^2 }        →  { x : ℕ | x > 0 • x² }
```

The bullet (`•`) separates the predicate from the expression.

#### Multi-Variable Sets
```
{ x, y : N | x = y }           →  { x, y : ℕ | x = y }
```

#### Set Without Domain
```
{ x | x in A }                 →  { x | x ∈ A }
```

#### Complex Examples
```
forall x : N | x in { y : N | y > 0 }
{ x : N | x > 0 and x <= 10 }
```

---

### Relation Operators (Phase 10a-b)

#### Basic Relations (Phase 10a)

**Relation Type:**
```
R <-> S                      →  R ↔ S  (relation from X to Y)
```

**Maplet Constructor:**
```
x |-> y                      →  x ↦ y  (ordered pair)
```

**Domain and Range Restriction:**
```
S <| R                       →  S ◁ R  (domain restriction)
R |> T                       →  R ▷ T  (range restriction)
```

**Composition:**
```
R ; S                        →  R ; S  (relational composition)
R comp S                     →  R ∘ S  (alternative composition)
```

**Domain and Range Functions:**
```
dom R                        →  dom R  (domain of relation)
ran R                        →  ran R  (range of relation)
```

#### Extended Relations (Phase 10b)

**Domain and Range Subtraction:**
```
S <<| R                      →  S ⩤ R  (domain subtraction)
R |>> T                      →  R ⩥ T  (range subtraction)
```

**Composition Operators:**
```
R o9 S                       →  R ∘ S  (forward/backward composition)
```

**Inverse and Identity:**
```
inv R                        →  inv R  (inverse function)
id X                         →  id X   (identity relation)
```

**Postfix Operators:**
```
R~                           →  R⁻¹    (relational inverse)
R+                           →  R⁺     (transitive closure)
R*                           →  R*     (reflexive-transitive closure)
```

#### Examples

**Basic relation expressions:**
```
x |-> y in R                 →  (x ↦ y) ∈ R
dom (S <| R)                 →  dom (S ◁ R)
R ; S ; T                    →  R ; S ; T  (left-associative)
```

**Extended operations:**
```
(R~)+                        →  (R⁻¹)⁺  (transitive closure of inverse)
inv (S <<| R)                →  inv (S ⩤ R)
(R o9 S)*                    →  (R ∘ S)*  (reflexive-transitive closure)
```

**Complex expressions:**
```
dom ((S <| R) |> T)          →  dom (S ◁ R ▷ T)
(id X) ; R                   →  (id X) ; R
R~ = inv R                   →  R⁻¹ = inv R
```

---

### Function Type Operators (Phase 11a)

Function types in Z notation describe different classes of functions between sets.

#### Total and Partial Functions

**Total Functions** (every element in domain has a mapping):
```
f : X -> Y                   →  f : X ⇸ Y
```

**Partial Functions** (some elements may not have a mapping):
```
f : X +-> Y                  →  f : X ⇀ Y
```

#### Injections (one-to-one)

**Total Injections** (injective total functions):
```
f : X >-> Y                  →  f : X ↣ Y
```

**Partial Injections** (injective partial functions):
```
f : X >+> Y                  →  f : X ⤔ Y
f : X -|> Y                  →  f : X ⤔ Y  (alternative notation)
```

#### Surjections (onto)

**Total Surjections** (surjective total functions):
```
f : X -->> Y                 →  f : X ↠ Y
```

**Partial Surjections** (surjective partial functions):
```
f : X +->> Y                 →  f : X ⤀ Y
```

#### Bijections (one-to-one and onto)

**Bijections** (total injective and surjective):
```
f : X >->> Y                 →  f : X ⤖ Y
```

#### Complex Function Types

**Nested function types:**
```
f : (X -> Y) -> Z            →  f : (X ⇸ Y) ⇸ Z
g : X -> (Y +-> Z)           →  g : X ⇸ (Y ⇀ Z)
h : (N -> N) -> (N -> N)     →  h : (ℕ ⇸ ℕ) ⇸ (ℕ ⇸ ℕ)
```

**Mixed function types:**
```
X -> Y +-> Z >-> W           →  X ⇸ Y ⇀ Z ↣ W  (left-associative)
```

#### Properties

- **Precedence**: Function types have the same precedence as relations (level 6)
- **Associativity**: Left-associative (e.g., `X -> Y -> Z` parses as `(X -> Y) -> Z`)
- **Compatibility**: Work seamlessly with other relation operators

---

### Function Application (Phase 11b)

Function application uses standard mathematical notation:

```
f(x)                         →  f(x)
g(x, y, z)                   →  g(x, y, z)
```

**Special Z notation functions** (generic instantiation):
```
seq(N)                       →  seq N  (sequence type)
P(X)                         →  P X    (power set type)
```

**Nested application:**
```
f(g(h(x)))                   →  f(g(h(x)))
```

---

### Lambda Expressions (Phase 11d)

Lambda expressions define anonymous functions:

#### Basic Lambdas
```
lambda x : N . x^2           →  λ x : ℕ • x²
lambda f : X -> Y . f(x)     →  λ f : X ⇸ Y • f(x)
```

#### Multi-Variable Lambdas
```
lambda x, y : N . x + y      →  λ x, y : ℕ • x + y
lambda a, b, c : Z . a       →  λ a, b, c : ℤ • a
```

#### Nested Lambdas
```
lambda x : X . lambda y : Y . (x, y)
→  λ x : X • λ y : Y • (x, y)
```

#### Complex Domain Types
```
lambda f : X -> Y . lambda x : X . f(x)
→  λ f : X ⇸ Y • λ x : X • f(x)
```

---

### Additional Operators (Phase 11.5)

#### Arithmetic Operators
```
x + y                        →  x + y   (addition)
x * y                        →  x × y   (multiplication)
x mod n                      →  x mod n (modulo)
```

#### Power Set Operators
```
P S                          →  P S    (power set)
P1 S                         →  P₁ S   (non-empty power set)
```

#### Cartesian Product
```
A cross B                    →  A × B
X cross Y cross Z            →  X × Y × Z
```

#### Set Difference
```
A \ B                        →  A ∖ B
```

#### Cardinality
```
# S                          →  # S
# { x : N | x > 0 }          →  # { x : ℕ | x > 0 }
```

---

### Tuple Expressions (Phase 11.6)

Tuples are ordered collections of elements:

```
(a, b)                       →  (a, b)
(x, y, z)                    →  (x, y, z)
(1, 2, 3, 4)                 →  (1, 2, 3, 4)
```

**Tuples in expressions:**
```
(a, b+1, f(c))               →  (a, b+1, f(c))
```

**Tuples in set comprehensions:**
```
{ x : N | x > 0 . (x, x^2) }
→  { x : ℕ | x > 0 • (x, x²) }
```

**Note**: Single-element parentheses `(x)` are parenthesized expressions, not tuples. Tuples require at least 2 elements.

---

### Set Literals (Phase 11.7)

Explicit set notation with elements:

#### Simple Set Literals
```
{1, 2, 3}                    →  {1, 2, 3}
{a, b, c}                    →  {a, b, c}
{}                           →  {}  (empty set)
```

#### Set Literals with Maplets
```
{1 |-> a, 2 |-> b, 3 |-> c}
→  {1 ↦ a, 2 ↦ b, 3 ↦ c}
```

**Mixed content:**
```
{1, 2 |-> 3, 4}              →  {1, 2 ↦ 3, 4}
```

**Nested sets:**
```
{{1, 2}, {3, 4}}             →  {{1, 2}, {3, 4}}
```

---

### Relational Image (Phase 11.8)

The relational image gives the image of a set under a relation:

#### Basic Relational Image
```
R(| S |)                     →  R(⦇ S ⦈)
parentOf(| {john} |)         →  parentOf(⦇ {john} ⦈)
```

**Syntax**: `R(| S |)` where R is a relation and S is a set.

**LaTeX**: Uses `\limg` and `\rimg` delimiters.

#### With Set Literals
```
R(| {1, 2, 3} |)             →  R(⦇ {1, 2, 3} ⦈)
```

#### With Composed Relations
```
(R o9 S)(| A |)              →  (R ∘ S)(⦇ A ⦈)
R~(| S |)                    →  R⁻¹(⦇ S ⦈)
```

#### In Set Comprehensions
```
{ p : Person | p in dom parentOf . (p, parentOf(| {p} |)) }
→  { p : Person | p ∈ dom parentOf • (p, parentOf(⦇ {p} ⦈)) }
```

#### Chained Application
```
R(| S |)(| T |)              →  R(⦇ S ⦈)(⦇ T ⦈)
```

**Use cases:**
- Function definitions: `{ p : Person . p |-> parentOf(| {p} |) }`
- Image queries: `married(| {Alice, Bob} |)`
- Relational composition: `(ancestor o9 parent)(| {john} |)`

---

### Generic Type Instantiation (Phase 11.9)

Generic type parameters allow polymorphic specifications:

#### Basic Generic Instantiation
```
emptyset[N]                  →  ∅[N]
seq[N]                       →  seq[N]
P[X]                         →  P[X]
```

#### Multiple Type Parameters
```
Type[A, B]                   →  Type[A, B]
Container[X, Y, Z]           →  Container[X, Y, Z]
```

#### Complex Type Parameters
```
emptyset[N cross N]          →  ∅[N × N]
P[P X]                       →  P[P X]
seq[N cross N]               →  seq[N × N]
```

#### Nested Generic Instantiation
```
Type[List[N]]                →  Type[List[N]]
Container[seq[N]]            →  Container[seq[N]]
```

#### Chained Generic Instantiation
```
Type[N][M]                   →  Type[N][M]
```
**Note**: Parses left-to-right as `(Type[N])[M]`

#### In Expressions
```
x in Type[N]                 →  x ∈ Type[N]
A subset P[X]                →  A ⊆ P[X]
emptyset[N] union {x}        →  ∅[N] ∪ {x}
```

#### In Set Comprehensions and Quantifiers
```
{ s : P[N] | s = emptyset[N] }
→  { s : P[N] | s = ∅[N] }

forall x : seq[N] | # x > 0
→  ∀ x : seq[N] • # x > 0
```

**Whitespace Detection**: The parser distinguishes between:
- `Type[X]` (no space) → generic instantiation
- `p [justification]` (space before `[`) → justification bracket

**Use cases:**
- Polymorphic definitions: `[X] notin == { x : X ; s : P[X] | not (x in s) }`
- Generic set types: `emptyset[N]`, `seq[Person]`, `P[Event]`
- Type instantiation: `Type[A, B]` for multi-parameter types

---

### Sequences and Bags (Phase 12)

Phase 12 adds support for sequences (ordered lists) and bags (multisets).

#### Sequence Literals

**Unicode Angle Brackets** (⟨⟩):
```
⟨⟩                           →  \langle \rangle  (empty sequence)
⟨a⟩                          →  \langle a \rangle
⟨a, b, c⟩                    →  \langle a, b, c \rangle
```

**ASCII Angle Brackets** (Phase 14):
```
<>                           →  \langle \rangle  (empty sequence)
<a>                          →  \langle a \rangle
<a, b, c>                    →  \langle a, b, c \rangle
```

Both Unicode and ASCII brackets work identically and produce the same LaTeX output.

#### Sequence Operators

**Concatenation** (Unicode):
```
⟨a⟩ ⌢ ⟨b⟩                   →  \langle a \rangle \cat \langle b \rangle
s ⌢ t                        →  s \cat t
```

**Concatenation** (ASCII - Phase 14):
```
<a> ^ <b>                    →  \langle a \rangle \cat \langle b \rangle
s ^ t                        →  s \cat t (when s ends with sequence)
```

**Note**: The `^` operator means concatenation only after a sequence closing bracket (`>` or `⟩`). Otherwise it means superscript.

**Sequence Functions**:
```
head s                       →  head s  (first element)
tail s                       →  tail s  (all but first)
last s                       →  last s  (last element)
front s                      →  front s (all but last)
rev s                        →  rev s   (reverse)
```

#### Sequence Types

```
seq(N)                       →  \seq N     (sequences of N)
iseq(N)                      →  \iseq N    (injective sequences)
seq[N]                       →  seq[N]     (generic instantiation)
```

#### Tuple Projection

Access tuple elements by position (1-indexed):
```
p.1                          →  p.1   (first element)
p.2                          →  p.2   (second element)
p.3                          →  p.3   (third element)
```

**In expressions:**
```
(trains(x)).2                →  (trains(x)).2
x.2 + y.3                    →  x.2 + y.3
```

**Chained with function application:**
```
f(x).1                       →  f(x).1
(g(a, b)).2                  →  (g(a, b)).2
```

#### Bag Literals

Bags are multisets (unordered collections allowing duplicates):

```
[[x]]                        →  \lbag x \rbag
[[a, b, c]]                  →  \lbag a, b, c \rbag
```

**Bag types:**
```
bag(X)                       →  \bag X
```

---

### Advanced Features (Phase 13)

Phase 13 adds powerful features for complex specifications.

#### Anonymous Schemas (Phase 13.1)

Schemas without names for inline use:

```
schema
  x : N
  y : N
where
  x + y = 10
end
```

Generates anonymous `\begin{schema}` environment without a name parameter.

#### Range Operator (Phase 13.2)

Integer ranges for set notation:

```
1..10                        →  1 \upto 10
1993..current                →  1993 \upto current
x.2..x.3                     →  x.2 \upto x.3
```

**Semantics**: `m..n` represents `{m, m+1, m+2, ..., n}`

**In expressions:**
```
x in 1..100                  →  x \in 1 \upto 100
forall i : 1..n | P          →  \forall i : 1 \upto n \bullet P
```

#### Override Operator (Phase 13.3)

Function/sequence override combines two functions, with the second taking precedence:

```
f ++ g                       →  f \oplus g
f ++ g ++ h                  →  f \oplus g \oplus h  (left-associative)
```

**Use cases:**
```
dom (f ++ g) = dom f union dom g
(f ++ g)(x)                  →  (f \oplus g)(x)
```

**Precedence**: Same as union (higher than intersection)

#### General Function Application (Phase 13.4)

Any expression can be applied as a function, not just identifiers:

**Sequence indexing:**
```
s(i)                         →  s(i)
⟨a, b, c⟩(2)                 →  \langle a, b, c \rangle(2)
```

**Override with application:**
```
(f ++ g)(x)                  →  (f \oplus g)(x)
```

**Composition:**
```
(R o9 S)(| A |)              →  (R \circ S)(\limg A \rimg)
```

**Chained projections:**
```
f(x).1                       →  f(x).1
```

---

### Pattern Matching Support (Phase 14)

Phase 14 enables pattern matching syntax for recursive function definitions using ASCII sequence brackets.

#### ASCII Sequence Brackets

Alternative to Unicode for easier typing:

**Empty sequence:**
```
<>                           →  \langle \rangle
f(<>)                        →  f(\langle \rangle)
```

**Sequence with elements:**
```
<x>                          →  \langle x \rangle
<a, b, c>                    →  \langle a, b, c \rangle
```

**Nested sequences:**
```
<<a>, <b>>                   →  \langle \langle a \rangle, \langle b \rangle \rangle
```

#### ASCII Concatenation

The `^` operator means concatenation when it follows a sequence closing bracket:

**After sequences:**
```
<x> ^ s                      →  \langle x \rangle \cat s
<a> ^ <b> ^ <c>              →  \langle a \rangle \cat \langle b \rangle \cat \langle c \rangle
```

**Regular superscript elsewhere:**
```
x^2                          →  x^2  (superscript, not concatenation)
2^n                          →  2^n
```

**Disambiguation**: Whitespace before `>` distinguishes sequence closing from comparison:
- `<x>` → sequence (no space before `>`)
- `x > y` → comparison (space before `>`)

#### Pattern Matching Examples

**Empty sequence pattern:**
```
total(<>) = 0                →  total(\langle \rangle) = 0
```

**Cons pattern (head and tail):**
```
total(<x> ^ s) = x + total(s)
→  total(\langle x \rangle \cat s) = x + total(s)
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

**Pattern matching use cases:**
- Recursive function definitions on sequences
- Base case with empty sequence: `f(<>) = value`
- Recursive case with cons: `f(<x> ^ s) = expr(x, f(s))`
- Natural recursive structure matching mathematical definitions

---

### Multi-Word Identifiers (Phase 15)

Phase 15 enables identifiers with underscores for natural multi-word variable names.

#### Underscore in Identifiers

**Multi-word identifiers:**
```
cumulative_total             →  \mathit{cumulative\_total}
not_yet_viewed               →  \mathit{not\_yet\_viewed}
employee_count               →  \mathit{employee\_count}
```

**Subscript notation (backward compatible):**
```
a_i                          →  a_i  (simple subscript)
a_1                          →  a_1
x_max                        →  x_{max}  (multi-char subscript)
```

#### Smart LaTeX Rendering

The system automatically determines the appropriate LaTeX rendering:

1. **No underscore**: `x` → `x`
2. **Simple subscript** (single char after `_`): `a_i` → `a_i`
3. **Multi-char subscript** (2-3 chars after `_`): `x_max` → `x_{max}`
4. **Multi-word identifier**: `cumulative_total` → `\mathit{cumulative\_total}`

**Heuristic**: If any part is > 3 characters OR multiple underscores, treat as multi-word identifier.

#### In Definitions

**Function definitions:**
```
axdef
  cumulative_total : seq(N) -> N
where
  cumulative_total(<>) = 0
  forall x : N; s : seq(N) |
    cumulative_total(<x> ^ s) = x + cumulative_total(s)
end
```

**Schema variables:**
```
schema System
  employee_count : N
  not_yet_viewed : P Document
where
  employee_count >= 0
end
```

**Use cases:**
- Natural multi-word variable names from specifications
- Backward compatible with existing subscript notation
- Automatic LaTeX formatting without manual markup

---

### Conditional Expressions (Phase 16)

Phase 16 adds conditional expressions (if/then/else) for mathematical specifications.

#### Basic Conditionals

```
if x > 0 then x else -x      →  (\text{if } x > 0 \text{ then } x \text{ else } -x)
if s = <> then 0 else head s →  (\text{if } s = \langle \rangle \text{ then } 0 \text{ else } \head s)
```

#### Nested Conditionals

Conditionals can be nested in then/else branches:

```
if x > 0 then 1 else if x < 0 then -1 else 0
→  (\text{if } x > 0 \text{ then } 1 \text{ else }
    (\text{if } x < 0 \text{ then } -1 \text{ else } 0))
```

#### In Function Definitions

**Absolute value:**
```
abs(x) = if x > 0 then x else -x
→  abs(x) = (\text{if } x > 0 \text{ then } x \text{ else } -x)
```

**Maximum:**
```
max(x, y) = if x > y then x else y
→  max(x, y) = (\text{if } x > y \text{ then } x \text{ else } y)
```

**Sign function:**
```
sign(x) = if x > 0 then 1 else if x < 0 then -1 else 0
→  sign(x) = (\text{if } x > 0 \text{ then } 1 \text{ else }
             (\text{if } x < 0 \text{ then } -1 \text{ else } 0))
```

#### Conditional as Operand

Conditionals can appear as operands in arithmetic expressions:

```
y + if x > 0 then 1 else 0
→  y + (\text{if } x > 0 \text{ then } 1 \text{ else } 0)
```

#### Recursive Functions

Conditionals enable natural recursive definitions:

```
f(s) = if s = <> then 0 else head s + f(tail s)
→  f(s) = (\text{if } s = \langle \rangle \text{ then } 0
          \text{ else } \head s + f(\tail s))
```

#### Arithmetic Subtraction

Phase 16 also adds the MINUS operator for arithmetic:

```
x - y                        →  x - y  (subtraction)
-x                           →  -x  (negation)
```

**Use cases:**
- Conditional logic in mathematical specifications
- Recursive function definitions with base/recursive cases
- Pattern matching alternative to separate equations
- Natural expression of piecewise functions

---

### Z Notation (Phase 4, 17)

#### Given Types
```
given Person, Company
```
Generates: `\begin{zed}[Person, Company]\end{zed}`

#### Free Types (Simple - Phase 4)
```
Status ::= active | inactive | pending
```
Generates: `\begin{zed}Status ::= active | inactive | pending\end{zed}`

#### Recursive Free Types with Constructor Parameters (Phase 17)

**Parameterized constructors** allow recursive type definitions:

**Single parameter:**
```
given N

Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩
```

**LaTeX Output:**
```latex
\begin{zed}[N]\end{zed}

\begin{zed}Tree ::= stalk | leaf \ldata N \rdata | branch \ldata Tree \cross Tree \rdata\end{zed}
```

**Multiple parameters:**
```
List ::= nil | cons⟨N × List⟩
```

**ASCII angle brackets** (alternative):
```
Tree ::= stalk | leaf<N> | branch<Tree × Tree>
```
Both Unicode `⟨⟩` and ASCII `<>` produce identical LaTeX output.

**Complex parameter types:**
```
Container ::= empty | filled⟨seq(N) × P(Entry)⟩
```

**Use cases:**
- Recursive data structures (trees, lists, graphs)
- Algebraic data types
- Structural induction proofs
- Pattern matching (with conditional expressions)

#### Abbreviations
```
Pairs == N x N
```

#### Axiomatic Definitions
```
axdef
  population : N
where
  population > 0
end
```

#### Schemas
```
schema State
  count : N
where
  count >= 0
end
```

#### Generic Parameters (Phase 9)

Add type parameters to abbreviations, axdefs, and schemas for polymorphism:

**Generic Abbreviations:**
```
[X] Pair == X
[X, Y] Product == X x Y
```

**Generic Axiomatic Definitions:**
```
axdef [T]
  identity : T
where
  identity = identity
end
```

**Generic Schemas:**
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

Generic parameters are enclosed in square brackets `[X, Y]` and can be:
- Before abbreviation names: `[X] Name == expr`
- After `axdef` keyword: `axdef [T] ... end`
- After schema names: `schema Name[X] ... end`

---

### Proof Trees (Phase 5)

Natural deduction proofs using indentation-based syntax:

```
PROOF:
  p and q => p [=> intro from 1]
    [1] p and q [assumption]
    :: p [and elim 1]
      :: p and q [from 1]
```

#### Proof Syntax
- **Indentation**: 2 spaces per level
- **Assumptions**: `[1]`, `[2]`, etc. for labeled assumptions
- **Justifications**: `[rule name]` after expression
- **Discharge**: `[=> intro from 1]` references assumption `[1]`
- **Siblings**: `::` prefix for parallel premises
- **References**: `[from 1]` refers to assumption `[1]`

#### Supported Rules
- `and intro`, `and elim 1`, `and elim 2`
- `or intro 1`, `or intro 2`, `or elim`
- `=> intro`, `=> elim`
- `false intro`, `false elim`
- Case analysis: `case p:` and `case q:`

#### Example: Complex Proof
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

## Features by Phase

### ✅ Phase 0: Propositional Logic
- Basic operators: `and`, `or`, `not`, `=>`, `<=>`
- Correct precedence and associativity
- Parentheses for grouping

### ✅ Phase 1: Document Structure
- Section headers: `=== Title ===`
- Solution blocks: `** Solution N **`
- Part labels: `(a)`, `(b)`, `(c)`
- Truth tables: `TRUTH TABLE:`
- Proper spacing with `\bigskip`, `\medskip`

### ✅ Phase 2: Equivalence Chains
- `EQUIV:` environment
- Justifications in brackets: `[rule name]`
- Automatic alignment with `align*`
- Operator conversion in justifications

### ✅ Phase 3: Mathematical Notation
- Quantifiers: `forall`, `exists`
- Subscripts: `x_i`, `a_{n}`
- Superscripts: `x^2`, `2^{10}`
- Set operators: `in`, `notin`, `subset`, `union`, `intersect`
- Comparison: `<`, `>`, `<=`, `>=`, `=`, `!=`

### ✅ Phase 4: Z Notation Basics
- Given types: `given A, B`
- Free types: `Type ::= branch1 | branch2`
- Abbreviations: `Name == Expression`
- Axiomatic definitions: `axdef ... where ... end`
- Schemas: `schema Name ... where ... end`

### ✅ Phase 5: Proof Trees
- Natural deduction proofs
- Indentation-based structure
- Assumption discharge with labels
- Multiple inference rules
- Case analysis with `or-elim`
- LaTeX `\infer` macro generation

### ✅ Phase 6: Multi-Variable Quantifiers
- Comma-separated variables: `forall x, y : N`
- Shared domain across variables
- Works with all quantifiers

### ✅ Phase 7: Equality & Special Operators
- Equality: `=`, `!=` in all contexts
- Unique existence: `exists1`
- Mu operator: `mu x : N | pred`
- Full equality reasoning support

### ✅ Phase 8: Set Comprehension
- Set by predicate: `{ x : N | pred }`
- Set by expression: `{ x : N | pred . expr }`
- Multi-variable: `{ x, y : N | pred }`
- Optional domain: `{ x | pred }`
- Nested set comprehensions
- Inline math in TEXT paragraphs

### ✅ Phase 9: Generic Parameters
- Generic abbreviations: `[X] Name == expr`
- Generic axiomatic definitions: `axdef [T] ... end`
- Generic schemas: `schema Name[X, Y] ... end`
- Multiple type parameters: `[X, Y, Z]`
- Backwards compatible with non-generic definitions

### ✅ Phase 10a: Basic Relation Operators
- Relation type: `<->` (X ↔ Y)
- Maplet constructor: `|->` (x ↦ y)
- Domain restriction: `<|` (S ◁ R)
- Range restriction: `|>` (R ▷ T)
- Composition: `;` and `comp` (R ; S, R ∘ S)
- Domain and range functions: `dom`, `ran`

### ✅ Phase 10b: Extended Relation Operators
- Domain subtraction: `<<|` (S ⩤ R)
- Range subtraction: `|>>` (R ⩥ T)
- Composition: `o9` (R ∘ S)
- Inverse function: `inv` (inv R)
- Identity relation: `id` (id X)
- Postfix inverse: `~` (R⁻¹)
- Transitive closure: `+` (R⁺)
- Reflexive-transitive closure: `*` (R*)

### ✅ Phase 11a: Function Type Operators (enhanced Phase 18)
- Total functions: `->` (X ⇸ Y)
- Partial functions: `+->` (X ⇀ Y)
- Total injections: `>->` (X ↣ Y)
- Partial injections: `>+>` or `-|>` (X ⤔ Y)
- Total surjections: `-->>` (X ↠ Y)
- Partial surjections: `+->>` (X ⤀ Y)
- Bijections: `>->>` (X ⤖ Y)
- Nested and complex function types

### ✅ Phase 11b: Function Application
- Standard application: `f(x)`, `g(x, y, z)`
- Nested application: `f(g(h(x)))`
- Generic instantiation: `seq(N)`, `P(X)`

### ✅ Phase 11c: Function Type Parsing
- Right-associative function types
- Complex nested types
- Integration with relation operators

### ✅ Phase 11d: Lambda Expressions
- Basic lambdas: `lambda x : N . x^2`
- Multi-variable: `lambda x, y : N . x + y`
- Nested lambdas
- Complex domain types

### ✅ Phase 11.5: Additional Operators
- Arithmetic: `+`, `*`, `mod`
- Power sets: `P`, `P1`
- Cartesian product: `cross` (×)
- Set difference: `\` (∖)
- Cardinality: `#`

### ✅ Phase 11.6: Tuple Expressions
- Multi-element tuples: `(a, b, c)`
- Tuples in expressions and comprehensions
- Nested tuples

### ✅ Phase 11.7: Set Literals
- Simple literals: `{1, 2, 3}`, `{a, b, c}`
- Empty set: `{}`
- Maplets: `{1 |-> a, 2 |-> b}`
- Nested sets

### ✅ Phase 11.8: Relational Image
- Basic: `R(| S |)`
- With compositions: `(R o9 S)(| A |)`
- In comprehensions: `parentOf(| {p} |)`
- Chained application

### ✅ Phase 11.9: Generic Type Instantiation
- Basic: `emptyset[N]`, `seq[N]`, `P[X]`
- Multiple parameters: `Type[A, B, C]`
- Complex parameters: `emptyset[N cross N]`
- Nested: `Type[List[N]]`
- Chained: `Type[N][M]`
- In domains: `forall x : P[N] | ...`
- Whitespace-sensitive parsing

### ✅ Phase 12: Sequences and Bags
- Sequence literals: `⟨⟩`, `⟨a, b, c⟩` (Unicode) or `<>`, `<a, b, c>` (ASCII)
- Concatenation: `⌢` (Unicode) or `^` after sequences (ASCII)
- Sequence operators: `head`, `tail`, `last`, `front`, `rev`
- Sequence types: `seq(N)`, `iseq(N)`
- Tuple projection: `.1`, `.2`, `.3`
- Bag literals: `[[a, b, c]]`
- Bag types: `bag(X)`

### ✅ Phase 13.1: Anonymous Schemas
- Schemas without names: `schema ... where ... end`
- Inline schema expressions
- Compatible with all schema features

### ✅ Phase 13.2: Range Operator
- Integer ranges: `m..n` → `m \upto n`
- In expressions: `1..10`, `1993..current`, `x.2..x.3`
- Set semantics: `{m, m+1, ..., n}`

### ✅ Phase 13.3: Override Operator
- Function/sequence override: `f ++ g` → `f \oplus g`
- Left-associative: `f ++ g ++ h`
- Same precedence as union
- Use in expressions: `dom (f ++ g)`, `(f ++ g)(x)`

### ✅ Phase 13.4: General Function Application
- Any expression can be applied: `(f ++ g)(x)`, `⟨a, b, c⟩(2)`
- Sequence indexing: `s(i)`
- Chained with projection: `f(x).1`
- Enables complex functional expressions

### ✅ Phase 14: ASCII Sequence Brackets & Pattern Matching
- ASCII alternative to Unicode: `<>` ≡ `⟨⟩`, `<a, b>` ≡ `⟨a, b⟩`
- ASCII concatenation: `<x> ^ s` ≡ `⟨x⟩ ⌢ s`
- Smart disambiguation: `<x>` vs `x > y` based on whitespace
- Pattern matching support: `f(<>) = 0`, `f(<x> ^ s) = expr`
- Enables recursive function definitions on sequences

### ✅ Phase 15: Underscore in Identifiers
- Multi-word identifiers: `cumulative_total`, `not_yet_viewed`
- Smart LaTeX rendering based on word length
- Simple subscripts: `a_i` → `a_i`
- Multi-char subscripts: `x_max` → `x_{max}`
- Multi-word identifiers: `cumulative_total` → `\mathit{cumulative\_total}`
- Backward compatible with existing subscript notation

### ✅ Phase 16: Conditional Expressions
- Basic conditionals: `if condition then expr1 else expr2`
- Nested conditionals in then/else branches
- Conditionals as operands in expressions
- Function definitions with conditionals: `abs(x) = if x > 0 then x else -x`
- Recursive functions: `f(s) = if s = <> then 0 else head s + f(tail s)`

### ✅ Phase 17: Recursive Free Types with Constructor Parameters
- FreeBranch AST node with name and optional parameters
- Constructor parameters: `Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩`
- LaTeX generation with `\ldata` and `\rdata` for parameterized constructors
- Support for both Unicode `⟨⟩` and ASCII `<>` angle brackets
- Complex parameter types (cross products, function applications)
- Backward compatible with simple free types (Phase 4)

### ✅ Phase 18 (Future): Semicolon-Separated Bindings
- Multiple binding groups: `forall x : N; y : N | P`
- Mixed comma and semicolon: `forall x, y : N; z : N | P`
- Nested scope for bindings
- Right-to-left nested quantifiers in LaTeX

### ✅ Phase 18: Partial Function Operators
- Alternative partial injection notation: `-|>` (equivalent to `>+>`)
- Used in database and state machine specifications
- Full function type operator support: `->`, `+->`, `>->`, `>+>`, `-|>`, `-->>`, `+->>`, `>->>`

### ✅ Phase 19: Finite Set Types
- Finite set type constructors: `F` and `F1`
- LaTeX rendering: `F X` → `\finset~X`, `F1 X` → `\finset_1~X`
- Generic instantiation: `F(SongId)` → `\finset~SongId`
- Truth table compatibility: F/P tokens handled in truth table rows
- Used in database schema specifications

### ✅ Phase 20: Distributed Union (bigcup)
- Distributed union operator: `bigcup`
- Prefix operator: `bigcup(S)` → `\bigcup S`
- Combines with other operators: `bigcup(ran(f))` → `\bigcup \ran f`
- Used for flattening sets of sets into single sets

---

## Command-Line Reference

### txt2pdf.sh Script

```bash
# Basic usage
./txt2pdf.sh input.txt                    # Creates input.pdf

# Use fuzz package
./txt2pdf.sh input.txt --fuzz

# Specify output
./txt2pdf.sh input.txt -o output.pdf
```

### Hatch CLI

```bash
# Convert to PDF (default)
hatch run cli input.txt

# LaTeX only
hatch run cli input.txt --latex-only

# Use fuzz package
hatch run cli input.txt --fuzz

# Expression mode
hatch run cli -e "p and q => r"

# Output to file
hatch run cli -e "p or q" -o output.tex
```

### Options

```
usage: txt2tex [-h] [-o OUTPUT] [--fuzz] [--latex-only] [-e] input

positional arguments:
  input                 Input text (expression or file path)

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file path
  --fuzz                Use fuzz package instead of zed-* packages
  --latex-only          Generate LaTeX only (skip PDF compilation)
  -e, --expr            Treat input as expression (not file)
```

---

## Examples

See the `examples/` directory for complete working examples:

- **phase0.txt** - Propositional logic basics
- **phase1.txt** - Document structure and truth tables
- **phase2.txt** - Equivalence chains with justifications
- **phase3.txt** - Quantifiers and mathematical notation
- **phase4.txt** - Z notation definitions
- **phase5.txt** - Natural deduction proof trees
- **phase6.txt** - Multi-variable quantifiers
- **phase7.txt** - Equality and special operators
- **phase8.txt** - Set comprehension
- **phase9.txt** - Generic parameters
- **phase10a_relations.txt** - Basic relation operators
- **phase11a.txt** - Function type operators
- **phase11b.txt** - Function application
- **phase11c.txt** - Function type parsing
- **phase11d.txt** - Lambda expressions
- **phase11_8_relational_image.txt** - Relational image
- **test_tuples.txt** - Tuple expressions (Phase 11.6)
- **test_set_literals.txt** - Set literals with maplets (Phase 11.7)
- **phase11_9.txt** - Generic type instantiation (Phase 11.9)

Build all examples:
```bash
cd examples
make                    # Build all
make phase11a           # Build specific phase
./txt2pdf.sh phase11_8_relational_image.txt  # Individual file
```

---

## Development

### Requirements
- Python 3.10+
- hatch (for development)
- LaTeX distribution (TeX Live recommended)
- zed-* packages (included in `latex/` directory)

### Setup

```bash
# Install hatch
pip install hatch

# Create development environment
hatch env create

# Run tests
hatch run test

# Run all quality gates
hatch run type       # MyPy type checking
hatch run lint       # Ruff linting
hatch run format     # Ruff formatting
```

### Quality Standards

All code must pass:
- ✅ MyPy strict mode (zero errors)
- ✅ Ruff linting (zero violations)
- ✅ Ruff formatting
- ✅ All tests passing (469 tests)
- ✅ Test coverage maintained (~79%)

### Running Tests

```bash
# All tests
hatch run test

# Specific phase
hatch run test tests/test_phase9.py

# With coverage
hatch run test-cov

# Verbose
hatch run test -v
```

### Project Structure

```
sem/
├── src/txt2tex/              # Source code
│   ├── tokens.py             # Token definitions
│   ├── lexer.py              # Lexical analyzer
│   ├── ast_nodes.py          # AST node types
│   ├── parser.py             # Recursive descent parser
│   ├── latex_gen.py          # LaTeX generator
│   └── cli.py                # Command-line interface
├── tests/                    # Test suite
│   ├── test_phase0.py        # Phase 0 tests
│   ├── test_phase1.py        # Phase 1 tests
│   ├── ...
│   ├── test_phase8.py        # Phase 8 tests
│   ├── test_phase9.py        # Phase 9 tests
│   ├── test_phase10a.py      # Phase 10a tests
│   ├── test_phase10b.py      # Phase 10b tests
│   ├── test_phase11a.py      # Phase 11a tests
│   ├── test_function_app.py  # Phase 11b tests
│   ├── test_lambda.py        # Phase 11d tests
│   ├── test_tuples.py        # Phase 11.6 tests
│   ├── test_set_literals.py  # Phase 11.5/11.7 tests
│   ├── test_relational_image.py # Phase 11.8 tests
│   ├── test_inline_math.py   # Inline math tests
│   └── ...                   # (453 tests total)
├── examples/                 # Example files
│   ├── Makefile              # Build automation
│   ├── phase0.txt            # Through phase9.txt
│   ├── exercises.pdf         # Reference materials
│   ├── glossary.pdf
│   └── solutions.pdf
├── hw/                       # Homework solutions
│   ├── Makefile              # Build automation
│   └── solutions.txt
├── latex/                    # LaTeX packages
│   ├── zed-cm.sty           # Z notation packages
│   ├── zed-maths.sty
│   └── zed-proof.sty
├── txt2pdf.sh               # Convenience script
├── pyproject.toml           # Python project config
├── DESIGN.md                # Architecture documentation
├── CLAUDE.md                # Development context
└── README.md                # This file
```

---

## Design Philosophy

**Phased approach**: Each phase delivers a complete, working end-to-end system that is immediately useful for a subset of problems. This allows incremental development with regular user testing and feedback.

**Parser-based**: Unlike regex-based approaches, txt2tex uses a proper compiler pipeline:
```
Text → Lexer → Tokens → Parser → AST → Generator → LaTeX → PDF
```

This provides:
- **Correctness**: Semantic understanding of structure
- **Maintainability**: Clean architecture, easy to extend
- **Error messages**: Precise line/column error reporting
- **Testability**: Each component tested in isolation

**Quality first**: All code passes strict type checking (mypy), linting (ruff), formatting, and comprehensive tests before commit.

See `DESIGN.md` for complete architectural details and implementation notes.

---

## LaTeX Packages

### Default: zed-* packages (Jim Davies)
```latex
\usepackage{zed-cm}       % Computer Modern fonts
\usepackage{zed-maths}    % Mathematical operators
\usepackage{zed-proof}    % Proof tree macros (\infer)
```

Advantages:
- No custom fonts required
- Works on any LaTeX installation
- Excellent proof tree support
- Modular design

### Optional: fuzz (Mike Spivey)
```bash
./txt2pdf.sh input.txt --fuzz
```

```latex
\usepackage{fuzz}         % Z notation package
```

Advantages:
- Historical standard for Z notation
- Single package simplicity
- Custom fonts for Z notation

Both packages are compatible - generated LaTeX works with either.

---

## Troubleshooting

### LaTeX Compilation Errors

**Missing packages:**
```
! LaTeX Error: File `zed-cm.sty' not found.
```
Solution: The zed-* packages are included in `latex/`. Ensure `TEXINPUTS` is set correctly:
```bash
export TEXINPUTS=./latex//:
pdflatex file.tex
```

The `txt2pdf.sh` script handles this automatically.

**Missing fonts (fuzz package):**
```
! Font not found: oxsz10
```
Solution: Ensure `MFINPUTS` is set:
```bash
export MFINPUTS=./latex//:
```

### Parse Errors

**Unexpected character:**
```
Error: Line 5, column 10: Unexpected character: '@'
```
Solution: Check for unsupported characters. See User Guide for supported syntax.

**Expected token:**
```
Error: Line 3, column 15: Expected '|' after quantifier binding
```
Solution: Check quantifier syntax: `forall x : N | predicate`

### Running Examples

If examples don't compile, ensure you're in the correct directory:
```bash
cd examples
make phase8           # Builds phase8.pdf
```

Or use the shell script from any location:
```bash
./txt2pdf.sh examples/phase8.txt
```

---

## Contributing

Contributions are welcome! Please:

1. Read `DESIGN.md` and `CLAUDE.md` for architectural context
2. Follow the phased development approach
3. Maintain all quality gates (type, lint, format, tests)
4. Add tests for new features
5. Update documentation

### Adding a New Feature

1. **Design**: Document in `DESIGN.md`
2. **Lexer**: Add tokens to `tokens.py` and `lexer.py`
3. **AST**: Add nodes to `ast_nodes.py`
4. **Parser**: Add parsing rules to `parser.py`
5. **Generator**: Add LaTeX generation to `latex_gen.py`
6. **Tests**: Add comprehensive tests to `tests/test_phaseN.py`
7. **Example**: Add example to `examples/phaseN.txt`
8. **Docs**: Update this README

---

## Roadmap

### Completed (Phase 0-17) - 77% Solution Coverage ✅

✅ **Phase 0**: Propositional logic
✅ **Phase 1**: Document structure, truth tables
✅ **Phase 2**: Equivalence chains
✅ **Phase 3**: Quantifiers, mathematical notation
✅ **Phase 4**: Z notation basics (given, free types, abbreviations, schemas)
✅ **Phase 5**: Natural deduction proof trees
✅ **Phase 6**: Multi-variable quantifiers
✅ **Phase 7**: Equality and special operators (exists1, mu)
✅ **Phase 8**: Set comprehension, inline math
✅ **Phase 9**: Generic parameters (polymorphic Z notation)
✅ **Phase 10a**: Basic relation operators (`<->`, `|->`, `<|`, `|>`, `dom`, `ran`, `;`, `comp`)
✅ **Phase 10b**: Extended relations (`<<|`, `|>>`, `o9`, `inv`, `id`, `~`, `+`, `*`)
✅ **Phase 11a**: Function type operators (`->`, `+->`, `>->`, `>+>`, `-->>`, `+->>`, `>->>`)
✅ **Phase 11b**: Function application (`f(x)`, `g(x,y,z)`)
✅ **Phase 11c**: Function type parsing (right-associative)
✅ **Phase 11d**: Lambda expressions (`lambda x : N . x^2`)
✅ **Phase 11.5**: Additional operators (arithmetic, power set, cartesian product, set difference, cardinality)
✅ **Phase 11.6**: Tuple expressions (`(a, b, c)`)
✅ **Phase 11.7**: Set literals with maplets (`{1 |-> a, 2 |-> b}`)
✅ **Phase 11.8**: Relational image (`R(| S |)`)
✅ **Phase 11.9**: Generic type instantiation (`emptyset[N]`, `Type[X]`, `P[N]`)
✅ **Phase 12**: Sequences and bags (`⟨a, b, c⟩`, `[[a, b]]`, `head`, `tail`, `.1`, `.2`)
✅ **Phase 13.1**: Anonymous schemas (`schema ... end`)
✅ **Phase 13.2**: Range operator (`m..n`)
✅ **Phase 13.3**: Override operator (`f ++ g`)
✅ **Phase 13.4**: General function application (`(f ++ g)(x)`, `s(i)`)
✅ **Phase 14**: ASCII sequence brackets and pattern matching (`<x> ^ s`)
✅ **Phase 15**: Underscore in identifiers (`cumulative_total`, smart subscript rendering)
✅ **Phase 16**: Conditional expressions (`if x > 0 then x else -x`, nested conditionals, MINUS operator)
✅ **Phase 17**: Recursive free types with constructor parameters (`Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩`)

### Remaining Features (12 solutions to full coverage)

**Current Status:** 40/52 solutions fully working (Solutions 1-36, 44-47)

**Next Priority: Pattern Matching** (Solutions 44-47 enhancement)
- Pattern matching equations for recursive functions
- Separate equations for each constructor case
- Base case and inductive case handling

**Phase 18: Pattern Matching** (Solutions 44-47 complete)
- Pattern matching syntax: `f(<>) = 0` and `f(<x> ^ s) = x + f(s)`
- Multiple equations per function
- Constructor patterns in function definitions
- Structural recursion patterns

**Phase 19: Full Sequence Operators** (Solutions 37-39)
- Additional sequence operators: `filter`, `squash`, `extract`
- Distributed concatenation: `cat/s`
- Sequence comprehensions

**Phase 20: Schema Operations** (Solutions 40-43)
- Schema decoration: `State'`, `Input?`, `Output!`
- Delta and Xi notation: `Delta State`, `Xi State`
- Schema composition and operations
- State machine specifications

**Supplementary** (Solutions 48-52)
- Advanced Z notation features (varies by solution)

**Estimated effort:**
- Phase 18 (Pattern matching): 6-8 hours → 80% coverage
- Phase 19 (Sequence operators): 4-6 hours → 85% coverage
- Phase 20 (Schema operations): 10-15 hours → 95% coverage
- Supplementary: 5-10 hours → 100% coverage

### Future Enhancements
- Better error recovery and messages
- IDE integration (LSP server)
- Syntax highlighting configurations
- Interactive REPL mode
- LaTeX preview mode

---

## License

MIT

## Credits

- **Mike Spivey**: fuzz package for Z notation
- **Jim Davies**: zed-* packages for Z notation
- **Anthropic Claude**: Development assistant

## Contact

For bugs, feature requests, or questions, please open an issue on GitHub.

---

**Last Updated**: Phase 17 Complete (Recursive Free Types with Constructor Parameters)
**Version**: 0.17.0
**Status**: Production Ready for Solutions 1-36, 44-47 - 77% Coverage (40/52 solutions)
**Test Suite**: 773 tests passing
**Remaining**: Solutions 37-43, 48-52 (pattern matching, schema operations, advanced features)
