# txt2tex User Guide

A comprehensive guide to writing mathematical specifications in txt2tex whiteboard notation.

## Table of Contents

1. [Installation](#installation)
2. [Document Structure](#document-structure)
3. [Text Blocks](#text-blocks)
4. [Propositional Logic](#propositional-logic)
5. [Predicate Logic](#predicate-logic)
6. [Equality](#equality)
7. [Sets and Types](#sets-and-types)
8. [Definitions](#definitions)
9. [Relations](#relations)
10. [Functions](#functions)
11. [Sequences](#sequences)
12. [Schema Notation](#schema-notation)
13. [Proof Trees](#proof-trees)

---

## Installation

### Install from PyPI

```bash
pip install txt2tex
```

### Using the CLI

After installation, the `txt2tex` command is available:

```bash
# Convert a txt file to LaTeX
txt2tex input.txt

# Specify output file
txt2tex input.txt -o output.tex

# Use zed-* packages instead of fuzz (default)
txt2tex input.txt --zed

# Include parts (a, b, c) in table of contents
txt2tex input.txt --toc-parts

# Disable overflow warnings
txt2tex input.txt --no-warn-overflow
```

### Full PDF Pipeline

To convert txt2tex files to PDF, you need:
1. A LaTeX distribution (TeX Live recommended)
2. The [fuzz](https://github.com/jmf-pobox/fuzz) package for Z notation fonts and type checking

```bash
# Generate LaTeX
txt2tex input.txt -o input.tex

# Compile to PDF (requires LaTeX and fuzz package)
# Use -interaction=nonstopmode to avoid hanging on errors
pdflatex -interaction=nonstopmode input.tex
```

**Note:** The fuzz package provides essential Z notation fonts (`oxsz*.mf`). Without it, compilation will fail with missing font errors. See the [fuzz repository](https://github.com/jmf-pobox/fuzz) for installation instructions.

For development, the repository includes `txt2pdf.sh` which handles LaTeX paths and compilation automatically.

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
- **Keywords automatically converted** to symbols:
  - `forall` → ∀ ($\forall$)
  - `exists` → ∃ ($\exists$)
  - `exists1` → ∃₁ ($\exists_1$)
  - `emptyset` → ∅ ($\emptyset$)
- Citations supported: `[cite key]` → (Author, Year) in Harvard style

**Citations in TEXT blocks:**

```
TEXT: The proof technique follows [cite spivey92].
TEXT: This is discussed in [cite spivey92 p. 42].
TEXT: See the definition in [cite woodcock96 p. 15].
TEXT: Multiple examples appear in [cite woodcock96 pp. 10-15].
```

Renders as:
- `[cite spivey92]` → (Spivey, 1992)
- `[cite spivey92 p. 42]` → (Spivey, 1992, p. 42)
- `[cite woodcock96 p. 15]` → (Woodcock and Davies, 1996, p. 15)

**Note**: Citation keys match those defined in your bibliography (see LATEX: blocks for bibliography setup). You can add any locator text (slide, p., pp., etc.) after the citation key.

### PURETEXT: - Raw Text with LaTeX Escaping

Use for bibliography entries or prose with punctuation that would confuse the lexer:

```
PURETEXT: Spivey, J.M. (1992) "The Z Notation" & references.
PURETEXT: Author's name, "quoted text", and more.
```

**Features:**
- Escapes LaTeX special characters: `&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`, `\`
- NO formula detection
- NO operator conversion
- NO keyword conversion (preserves literal `forall`, `exists`, `emptyset` for teaching)
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

txt2tex automatically includes the `natbib` package for author-year citations. You can manage bibliographies using either approach:

**Bibliography File Approach (Recommended)**

Use a separate `.bib` file with document-level directives:

```
BIBLIOGRAPHY: references.bib
BIBLIOGRAPHY_STYLE: plainnat
```

The build process will automatically run BibTeX to process citations. The bibliography file should be in the same directory as your `.txt` file.

**Available styles** (compatible with natbib):
- `plainnat` - Author-year citations (default, similar to Harvard style)
- `abbrvnat` - Abbreviated author names
- `unsrtnat` - Unsorted, order of citation
- `alpha` - Alphanumeric labels

Note: The `harvard` style is not a standard BibTeX style. Use `plainnat` for author-year citations similar to Harvard style.

**Manual Bibliography Approach**

For custom formatting or when you don't have a `.bib` file, use LATEX: blocks to define your bibliography manually:

```
LATEX: \setlength{\leftskip}{0pt}
LATEX: \begin{thebibliography}{Woodcock, n.d.}
LATEX:
LATEX: \bibitem[Spivey, 1992]{spivey92} Spivey, J.M. (1992). \textit{The Z Notation: A Reference Manual}. Prentice Hall.
LATEX:
LATEX: \bibitem[Woodcock and Davies, 1996]{woodcock96} Woodcock, J. and Davies, J. (1996). \textit{Using Z}. Prentice Hall.
LATEX:
LATEX: \end{thebibliography}
```

The `\bibitem[Author, Year]{key}` format creates Harvard-style citations. Use `[cite key]` in TEXT: blocks to reference them (see TEXT: section above).

**Note**: If `BIBLIOGRAPHY:` is specified, the bibliography file approach takes precedence. LATEX blocks will still work for other purposes.

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
lnot p           →  ¬p          (negation)
p land q         →  p ∧ q       (conjunction)
p lor q          →  p ∨ q       (disjunction)
p => q           →  p ⇒ q       (implication)
p <=> q          →  p ⇔ q       (equivalence)
```

**Important:** Use LaTeX-style keywords `land`, `lor`, `lnot` for logical operators. English-style `and`, `or`, `not` are NOT supported in Z notation expressions.

### Precedence (highest to lowest)

1. `lnot` (unary negation)
2. `land` (conjunction)
3. `lor` (disjunction)
4. `=>` (implication)
5. `<=>` (equivalence, lowest)

### Examples

```
lnot p land q      →  (¬p) ∧ q
p land q => r      →  (p ∧ q) ⇒ r
p => q => r        →  p ⇒ (q ⇒ r)    [right-associative]
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
p land q
<=> q land p [commutative]
<=> q land p [idempotent]
```

Generates `align*` environment with justifications flush-right.

#### Justifications in Equivalence Chains

Justifications are **free-form text** in square brackets after each step. You can write any reasoning you want:

```
EQUIV:
lnot (p land q)
<=> (lnot p) lor (lnot q) [De Morgan]
<=> (lnot p) lor (lnot q) [idempotence]
<=> (lnot p) lor (lnot q) lor (lnot r) [associativity]
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
- `land` → $\land$
- `lor` → $\lor$
- `lnot` → $\lnot$
- `=>` → $\Rightarrow$ (or `\implies` in fuzz mode)
- `<=>` → $\Leftrightarrow$ (always, even in fuzz mode for EQUIV blocks)

**Note on fuzz mode**: When using `--fuzz`, implication renders as `\implies` everywhere. Equivalence uses `\Leftrightarrow` in EQUIV blocks (equational reasoning) but `\iff` in predicates.

**Relation operators:**
- `o9` → $\circ$ (composition)
- `|->` → $\mapsto$ (maplet)
- `<->` → `\rel` (relation type)
- `<|` → `\dres` (domain restriction)
- `|>` → `\rres` (range restriction)
- `<<|` → `\ndres` (domain corestriction)
- `|>>` → `\nrres` (range corestriction)
- `++` → $\oplus$ (override)

**Function type operators:**
- `->` → `\fun` (total function)
- `+->` → `\pfun` (partial function)
- `>->` → `\inj` (injection)
- `-->>` → `\surj` (surjection)
- `>->>` → `\bij` (total bijection)
- `>7->` → `\pbij` (partial bijection)
- `77->` → `\ffun` (finite partial function)

**Relation functions:**
- `dom`, `ran`, `comp`, `inv`, `id`

Example with logical operators:
```
<=> p lor (lnot p land q) [land land true]
```
Renders as: $\Leftrightarrow p \lor (\lnot p \land q)$ with justification [$\land$ $\land$ true]

Example with relation operators:
```
<=> (exists y : Y | w |-> y elem (R o9 S) land y |-> z elem T) [definition of o9]
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

**With bullet separator (Phase 40):**
```
forall x : N | x > 0 . x < 10
```
Generates: $\forall x : \mathbb{N} \mid x > 0 \bullet x < 10$

The bullet separator (`.`) separates the constraint (filtering condition) from the body (conclusion). This is equivalent to:
```
forall x : N | (x > 0 => x < 10)
```

#### Existential Quantification (∃)

```
exists y : Z | y < 0
```
Generates: $\exists y : \mathbb{Z} \bullet y < 0$

**With bullet separator (Phase 40):**
```
exists y : Z | y < 0 . y > -10
```
Generates: $\exists y : \mathbb{Z} \mid y < 0 \bullet y > -10$

#### Unique Existential Quantification (∃₁)

```
exists1 x : N | x * x = 4
```
Generates: $\exists_1 x : \mathbb{N} \bullet x \times x = 4$

**With bullet separator (Phase 40):**
```
exists1 x : N | x * x = 4 . x > 0
```
Generates: $\exists_1 x : \mathbb{N} \mid x \times x = 4 \bullet x > 0$

**Note on bullet separator limitations:**

In rare cases where the bullet separator is followed by an identifier and then `=`, the parser may treat it as a field projection rather than a bullet separator. In these cases, use implication (`=>`) instead:

```
// Use implication for this pattern:
forall i, j : dom f | f i = f j => i = j

// Instead of bullet (ambiguous with projection):
forall i, j : dom f | f i = f j . i = j
```

The bullet separator works correctly when followed by set operators (`elem`, `notin`, `subset`), logical operators (`land`, `lor`, `=>`), or comparisons (`<`, `>`, `<=`, `>=`, `!=`).

#### Definite Description (μ)

The mu operator (μ) denotes "the unique value satisfying a predicate":

```
mu x : N | x * x = 4 land x > 0
```

Generates (in fuzz mode): $(\mu x : \mathbb{N} \mid x \times x = 4 \land x > 0)$

**Note**: In fuzz mode, mu expressions use `|` as the separator and are wrapped in parentheses. The syntax is: `mu variable : Type | predicate`

**With expression part** (selecting from a set):
```
mu x : N | x elem S . f(x)
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

**Important:** Nested quantifiers in `land`/`lor` expressions must be parenthesized:
```
✅ Correct:   forall x : N | x > 0 land (forall y : N | y > x)
❌ Incorrect: forall x : N | x > 0 land forall y : N | y > x
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
x elem A         →  x ∈ A       ['is an element of']
x notin B        →  x ∉ B       ['not an element of']
```

**Note:** Use `elem` for set membership. The `in` keyword was deprecated in favor of `elem` to avoid ambiguity with English prose.

### Set Relations

```
A subset B       →  A ⊆ B       [subset - includes equality]
A psubset B      →  A ⊂ B       [strict/proper subset - excludes equality]
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
  e.year = 2025 land e.code = 479
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
{ x : N | x > 0 . x * x }
```
Generates: $\{ x : \mathbb{N} \mid x > 0 \bullet x \times x \}$

The bullet (`•`) separates the predicate from the expression.

**Multi-variable:**
```
{ x, y : N | x = y }
```

**Without domain:**
```
{ x | x elem A }
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

Abbreviations define shorthand names for types or expressions. They must be wrapped in `zed...end` blocks:

**Basic abbreviations:**
```
zed
  Pairs == N cross N
end

zed
  Triples == N cross N cross N
end
```

Generates: `\begin{zed} Pairs == ℕ × ℕ \end{zed}` and `\begin{zed} Triples == ℕ × ℕ × ℕ \end{zed}`

**With generic parameters:**
```
zed
  [X] Pair == X cross X
end

zed
  [X, Y] Product == X cross Y
end
```

**Compound identifiers** (names with operator suffixes like `R+`, `R*`):
```
zed
  R+ == { a, b : N | b > a }
end

zed
  R* == { a, b : N | b >= a }
end
```

This generates:
```latex
\begin{zed}
  R^+ == \{ a, b : \mathbb{N} \mid b > a \}
\end{zed}
\begin{zed}
  R^* == \{ a, b : \mathbb{N} \mid b \geq a \}
\end{zed}
```

**Mixed content** (zed blocks can contain multiple constructs):
```
zed
  given Entry
  Status ::= active | inactive
  DefaultStatus == active
end
```

This generates a single `\begin{zed}...\end{zed}` block containing the given type, free type, and abbreviation.

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

### Syntax Environment

For complex free type definitions with multiple types, the `syntax` environment provides column-aligned layout similar to BNF grammars:

**Basic syntax block:**
```
syntax
  OP ::= plus | minus | times | divide
end
```

Generates:
```latex
\begin{syntax}
OP & ::= & plus | minus | times | divide
\end{syntax}
```

**Multiple definitions with grouping:**

Blank lines between definitions create visual groups using `\also`:

```
syntax
  Status ::= active | inactive | pending

  Response ::= ok | error<N> | timeout
end
```

Generates:
```latex
\begin{syntax}
Status & ::= & active | inactive | pending \\
\also
Response & ::= & ok | error \ldata \nat \rdata | timeout
\end{syntax}
```

**Parameterized constructors:**
```
syntax
  Tree ::= leaf<N> | branch<Tree cross Tree>

  Expr ::= const<N> | var<NAME> | binop<OP cross Expr cross Expr>
end
```

**When to use syntax vs zed blocks:**

- Use `syntax` for: Multiple related types, BNF-style grammars, complex type hierarchies
- Use `zed` for: Single simple types, types mixed with other definitions

**Examples:** See `examples/06_definitions/syntax_demo.txt`

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
  forall x : X; y : Y | fst(x, y) = x land snd(x, y) = y
end
```

**Multiple declarations (semicolon-separated on one line):**
```
gendef [X, Y]
  fst : X cross Y -> X; snd : X cross Y -> Y
where
  forall x : X; y : Y | fst(x, y) = x land snd(x, y) = y
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

### Generic Constructs - Fuzz Compatibility

**Important**: The fuzz typechecker has limitations on what can appear inside `gendef` blocks. Use these workarounds for full fuzz compatibility:

#### Workaround 1: Generic Free Types

**Problem**: Free type definitions (`::=`) are NOT supported inside `gendef` blocks.

**Incorrect** (will not compile):
```
gendef [X]
  Tree_X ::= leaf | node⟨X × Tree_X × Tree_X⟩
end
```

**Correct workaround**: Define the free type separately with `given`, then define operations in `gendef`:
```
given X

Tree_X ::= leaf_X | node_X⟨X cross Tree_X cross Tree_X⟩

gendef [X]
  makeLeaf_X : Tree_X
  makeNode_X : X cross Tree_X cross Tree_X -> Tree_X
  treeDepth_X : Tree_X -> N
where
  makeLeaf_X = leaf_X
  forall x : X; left, right : Tree_X |
    makeNode_X(x, left, right) = node_X(x, left, right)
end
```

#### Workaround 2: Generic Schemas

**Problem**: Schema definitions are NOT supported inside `gendef` blocks.

**Incorrect** (will not compile):
```
gendef [X]
  schema Container_X
    contents : seq X
    capacity : N
  where
    # contents <= capacity
  end
end
```

**Correct workaround**: Use `schema[X]` syntax (standard Z notation):
```
schema Container[X]
  contents : seq X
  capacity : N
where
  # contents <= capacity
end
```

You can then define operations on the generic schema using `gendef`:
```
gendef [X]
  emptyContainer : Container[X]
  addToContainer : Container[X] cross X -> Container[X]
where
  emptyContainer.contents = ⟨⟩ land emptyContainer.capacity = 100
end
```

#### Key Principles for Fuzz Compatibility

1. **`gendef` blocks can contain**:
   - Type declarations (`name : type`)
   - Schema references (to previously defined schemas)
   - Predicates in `where` clause

2. **`gendef` blocks CANNOT contain**:
   - Free type definitions (`::=`)
   - Schema definitions (`schema Name ... end`)

3. **Generic schemas**: Use `schema Name[X, Y]` syntax (not `gendef`)

4. **Generic free types**: Define separately with `given`, then operations with `gendef`

See `examples/06_definitions/gendef_advanced.txt` for complete working examples.

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
R*               →  R*          [reflexive-transitive closure]
```

**Closure operators** (postfix):
- `+` (transitive): follow relation one or more times
- `*` (reflexive-transitive): follow relation zero or more times

Note: Reflexive closure (`rcl`) and symmetric closure (`s`) are not yet implemented.

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
f : Year 77-> Table     →  Year ⇸ Table    [finite partial function]
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
lambda x : N . x * x
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
  forall n : N | modulo3(n) = n mod 3 land
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
| `...^...` (no space) | Relation iteration | `\bsup...\esup` | `R^2` |

**Concatenation examples (MUST have space before `^` and be on same line):**
```
<a> ^ <b>        →  ⟨a⟩ ⌢ ⟨b⟩      [sequence literals]
s ^ t            →  s ⌢ t           [sequence variables]
f(x) ^ <y>       →  f(x) ⌢ ⟨y⟩     [function result]
```

**Note**: Multi-line concatenation (splitting across lines) is not currently supported.

**Relation iteration examples (NO space before `^`):**
```
R^2              →  R²          [relation composed with itself]
R^n              →  Rⁿ          [n-fold relation composition]
```

**Important limitation:** The `^` operator (without space) generates `\bsup...\esup` which fuzz interprets as the `iter` operator. This **only works for relations**, not arithmetic:

✅ **Works:** `R^n` where R is a relation (type: `X <-> Y`)
❌ **Does NOT work:** `x^2`, `2^n` where x or 2 are numbers (fuzz type error)

**For arithmetic exponentiation, use:**
- Manual multiplication: `x * x` for x², `x * x * x` for x³
- Define a pow function (see examples/06_definitions/pow_function.txt)

**Common mistake:**
```
❌ <x>^<y>       →  ERROR: "use '> ^ <' not '>^<'"
✅ <x> ^ <y>     →  ⟨x⟩ ⌢ ⟨y⟩
```

**Note:** If typing `⌢` (U+2040) is difficult, remember you can use ` ^ ` (with spaces) as ASCII alternative.

### Filter

```
s ↾ A            →  s ↾ A       [sequence filter - restricts sequence s to elements in set A]
s filter A       →  s ↾ A       [ASCII alternative using 'filter' keyword]
```

The filter operator restricts a sequence to only include elements from a given set.

**ASCII Notation:** Use the `filter` keyword (e.g., `s filter A`)
**Unicode Alternative:** Use `↾` (U+21BE) if preferred

**Example:**
```
records filter {x : Entry | x.viewed = yes}    [filter sequence to viewed entries]
```

**Note:** The filter operator is distinct from `|>` (range restriction for relations).

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

Note: `reverse` is abbreviated as `rev` in txt2tex.

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
b1 == [[x]]            →  b₁ = ⟦x⟧         [bag in abbreviation]
b2 == [[a, b, c]]      →  b₂ = ⟦a, b, c⟧
```

**Note**: Bag literals must appear in an abbreviation or expression context, not as standalone statements.

**Bag union:**
```
b1 ⊎ b2          →  b1 ⊎ b2     [bag union - combines two bags]
b1 bag_union b2  →  b1 ⊎ b2     [ASCII alternative using 'bag_union' keyword]
```

The bag union operator combines two bags, preserving multiplicities (unlike set union which removes duplicates).

**ASCII Notation:** Use the `bag_union` keyword (e.g., `b1 bag_union b2`)
**Unicode Alternative:** Use `⊎` (U+228E) if preferred

---

## Schema Notation

### Zed Blocks (Unboxed Paragraphs)

Zed blocks provide a way to write Z notation content without the visual boxing of axdef/schema blocks. They correspond directly to fuzz's `\begin{zed}...\end{zed}` environment.

**What can go in zed blocks:**
- ✅ **Predicates**: `forall x : N | x >= 0`
- ✅ **Given types**: `given A, B, C`
- ✅ **Free types**: `Status ::= active | inactive`
- ✅ **Abbreviations**: `MaxSize == 100` or `[X] Pair == X cross X`
- ✅ **Mixed content**: Multiple constructs in one block
- ❌ **NOT bare expressions**: Cannot use standalone `{ x : N | x > 0 }` or `x + y` alone

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
  exists n : NAME | birthday(n) elem December
end
```

**Given types:**
```
zed
  given Person, Company
end
```

**Free types:**
```
zed
  Status ::= active | inactive | pending
end
```

**Abbreviations:**
```
zed
  Evens == { n : N | n mod 2 = 0 }
end
```

**Abbreviations with generic parameters:**
```
zed
  [X] Pair == X cross X
end
```

**Compound identifier abbreviations:**
```
zed
  R+ == { a, b : N | b > a }
end
```

**Mixed content (multiple constructs in one block):**
```
zed
  given Entry
  Status ::= active | inactive
  DefaultStatus == active
end
```

**Complex predicates:**
```
zed
  forall x : S | exists y : T | x elem y
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
- Can contain given types, free types, abbreviations, and predicates
- Supports mixed content (multiple construct types in one block)
- Typically used for global type definitions, abbreviations, and constraints

### Container Comparison: What Goes Where

| Content Type | zed | axdef | schema | Standalone |
|--------------|-----|-------|--------|------------|
| **Predicates** | ✅ `forall x : N \| x >= 0` | ✅ In `where` clause | ✅ In `where` clause | ✅ Direct |
| **Abbreviations** | ✅ `MaxSize == 100` | ❌ Use zed | ❌ Use zed | ❌ Use zed |
| **Given types** | ✅ `given A, B` | ❌ Use zed | ❌ Use zed | ✅ `given` (legacy) |
| **Free types** | ✅ `Status ::= active` | ❌ Use zed | ❌ Use zed | ✅ Direct (legacy) |
| **Type declarations** | ✅ Via `given` | ❌ Use zed | ❌ Use zed | ✅ `given` |
| **Variable declarations** | ❌ | ✅ Before `where` | ✅ Before `where` | ❌ |
| **Bare expressions** | ❌ | ❌ | ❌ | ✅ Direct |
| **Set comprehensions** | ✅ In abbrev | ✅ In `where` clause | ✅ In `where` clause | ✅ Direct |
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
  x > 0 land y > 0
end
```

Generates:
```latex
\begin{schema}{Point}
  x : \mathbb{N} \\
  y : \mathbb{N}
\where
  x > 0 land y > 0
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
- `land` → $\land$
- `lor` → $\lor$
- `lnot` → $\lnot$
- `=>` → $\Rightarrow$ (or `\implies` in fuzz mode)
- `<=>` → $\Leftrightarrow$ (or `\iff` in fuzz mode)

**Note**: In `--fuzz` mode, predicates use `\implies` and `\iff` to match fuzz package conventions.

**Relation operators:**
- `o9` → $\circ$ (composition)
- `|->` → $\mapsto$ (maplet)
- `<->` → `\rel` (relation type)
- `<|` → `\dres`, `|>` → `\rres`, `<<|` → `\ndres`, `|>>` → `\nrres`
- `++` → $\oplus$ (override)

**Function type operators:**
- `->` → `\fun`, `+->` → `\pfun`, `>->` → `\inj`, `-->>` → `\surj`, `>->>` → `\bij`, `>7->` → `\pbij`, `77->` → `\ffun`

**Relation functions:**
- `dom`, `ran`, `comp`, `inv`, `id`

Examples:
- `[=> intro from 1]` → $\Rightarrow$-intro$^{[1]}$
- `[land elim 1]` → $\land$-elim-1
- `[lor elim from 2]` → $\lor$-elim (from 2)
- `[definition of o9]` → [definition of $\circ$]
- `[definition of |->]` → [definition of $\mapsto$]

### Supported Rules

**Conjunction:**
- `[land intro]` - introduction
- `[land elim 1]` - left elimination
- `[land elim 2]` - right elimination
- `[land intro from 1 land 3]` - introduction with references

**Disjunction:**
- `[lor intro 1]` - left introduction
- `[lor intro 2]` - right introduction
- `[lor elim]` - elimination (case analysis)
- `[lor elim from 2 land 3]` - elimination with references

**Implication:**
- `[=> intro]` - introduction (discharge assumption)
- `[=> intro from 1]` - introduction discharging assumption 1
- `[=> elim]` - modus ponens
- `[=> elim from 1 land 2]` - modus ponens with references

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
p land q => p [=> intro from 1]
  [1] p land q [assumption]
      p [land elim 1]
```

### Example: Case Analysis

**Simple case analysis:**
```
PROOF:
p lor q => r [=> intro from 1]
  [1] p lor q [assumption]
      r [lor elim]
        case p:
          r [from assumption p]
        case q:
          r [from assumption q]
```

**Case analysis with sibling premises:**
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

**Important**: When working with case analysis:
- Use `[from above]` to reference facts established before the case split
- The `::` sibling markers indicate multiple facts that together support the next step
- Each case should derive the same conclusion through different reasoning paths
- Facts proven before case analysis remain available within all cases

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

**Subscripts:**
```
x_i              →  xᵢ          [subscript]
a_{n}            →  aₙ          [braces group multi-char subscripts]
```

**Superscripts (relation iteration only):**
```
R^n              →  Rⁿ          [n-fold relation composition]
R^{n+1}          →  Rⁿ⁺¹        [braces group multi-char superscripts]
```

**CRITICAL LIMITATION**: The `^` operator generates `\bsup ... \esup` LaTeX commands which fuzz interprets as the `iter` operator (relation iteration). This **ONLY works for relations**, not arithmetic:

✅ **Supported:** `R^n` where R has type `X <-> Y` (relation)
❌ **NOT supported:** `x^2`, `2^n`, `n^k` where the base is a number (causes fuzz type error)

**For arithmetic exponentiation:**
- Use manual multiplication: `x * x` for x², `x * x * x` for x³
- Define a `pow` function (see examples/06_definitions/pow_function.txt)

**Why this limitation exists:** Fuzz's `\bsup...\esup` command is specifically for the `iter` operator, which applies a relation to itself n times. It expects a relation type, not a number type. See the Z Reference Manual section on `iter` for details.

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

## Overflow Warnings

txt2tex automatically detects lines in Z notation blocks (axdef, schema, zed, gendef) that may overflow the page margin. These blocks use fuzz's internal `\halign` formatting which cannot be automatically scaled with `adjustbox`.

### Warning Output

When a line exceeds the threshold, you'll see a warning on stderr:

```
Warning: Line 270 may overflow page margin (~145 chars)
  In: axdef where clause
  Content: forall i : songs | loveHateScore(i) = if ...
  Suggestion: Break long expressions using indentation continuation
```

### CLI Options

- `--no-warn-overflow` - Disable overflow warnings
- `--overflow-threshold N` - Set custom threshold (default: 140 LaTeX chars)

### Line Break Syntax

Use `\` (backslash) to explicitly break long lines. Line breaks are supported:

**After logical operators:**
```
p land q => \
  r lor s
```

**After `then` and before `else` in conditionals:**
```
if condition \
  then result1 \
  else result2
```

**After `=` in equations:**
```
longFunctionName(x, y, z) = \
  complexExpression + moreTerms
```

### Fixing Overflow

To fix overflowing lines, use `\` to break at logical points:

**Before (overflows):**
```
axdef
  f : SongId +-> N
where
  forall i : songs | f(i) = if (# {u : UserId | i elem loved(u)}) >= (# {u : UserId | i elem hated(u)}) then (# {u : UserId | i elem loved(u)}) - (# {u : UserId | i elem hated(u)}) else 0
end
```

**After (fits page):**
```
axdef
  f : SongId +-> N
where
  forall i : songs |
    f(i) = if (# {u : UserId | i elem loved(u)}) >= (# {u : UserId | i elem hated(u)}) \
      then (# {u : UserId | i elem loved(u)}) - (# {u : UserId | i elem hated(u)}) \
      else 0
end
```

### Blocks That Support Auto-Scaling

The following block types use `adjustbox` and automatically scale to fit the page:
- `TRUTH TABLE:` blocks
- `ARGUE:` and `EQUIV:` blocks
- `PROOF:` blocks (proof trees)

These do not need manual line breaking.

---

## Quick Reference

### Whitespace Sensitivity

- **Sequence closing:** `<x>` (no space before `>`) vs `x > y` (space before `>`)
- **Generic instantiation:** `Type[X]` (no space before `[`) vs `p [just]` (space before `[`)
- **Caret operator:** `s ^ t` (space before `^`) is concatenation, `R^n` (no space) is relation iteration

### Parentheses Requirements

- **Function application:** `f(x)` not `f x`
- **Type application:** `seq(N)` not `seq N`
- **Nested quantifiers in land/lor:** `p land (forall x : N | P)`

### Common Pitfalls

1. **Forgetting parentheses** in function calls
2. **Nested quantifiers** without proper parenthesization
3. **Smart quotes** in text - use ASCII quotes or PURETEXT blocks
4. **Underscore in identifiers** not supported by fuzz typechecker (but works in txt2tex)
5. **Concatenation without space** - `<x>^<y>` is an error, use `<x> ^ <y>` with spaces

---

## Getting Help

For more information:
- See [../../README.md](../../README.md) for installation and setup
- See [../DESIGN.md](../DESIGN.md) for architecture details
- Check `examples/` directory for working examples (48 examples organized by topic)
- Review phase-specific test files in `tests/` for syntax examples

---

## See Also

### Learning Resources
- **[Tutorial Index](../tutorials/README.md)** - Step-by-step learning path
- **[Getting Started](../tutorials/00_getting_started.md)** - Your first txt2tex document
- **[Propositional Logic Tutorial](../tutorials/01_propositional_logic.md)** - Truth tables and proofs
- **[Predicate Logic Tutorial](../tutorials/02_predicate_logic.md)** - Quantifiers and domains
- **[Sets and Types Tutorial](../tutorials/03_sets_and_types.md)** - Set operations and Z types
- **[Proof Trees Tutorial](../tutorials/04_proof_trees.md)** - Natural deduction proofs
- **[Z Definitions Tutorial](../tutorials/05_z_definitions.md)** - Schemas and axdefs
- **[Relations Tutorial](../tutorials/06_relations.md)** - Maplets and relational operators
- **[Functions Tutorial](../tutorials/07_functions.md)** - Lambda expressions and function types
- **[Sequences Tutorial](../tutorials/08_sequences.md)** - Sequence notation and operations
- **[Schemas Tutorial](../tutorials/09_schemas.md)** - Schema notation and operations
- **[Advanced Topics](../tutorials/10_advanced.md)** - Generic definitions and more

### Reference Documentation
- **[Proof Syntax Guide](PROOF_SYNTAX.md)** - Detailed proof tree formatting rules
- **[Fuzz vs Standard LaTeX](FUZZ_VS_STD_LATEX.md)** - Understanding fuzz typechecker quirks
- **[Feature Gaps](FUZZ_FEATURE_GAPS.md)** - Known limitations and workarounds

### Development Resources
- **[Missing Features](MISSING_FEATURES.md)** - Features not yet implemented
- **[IDE Setup](../development/IDE_SETUP.md)** - VSCode/Cursor configuration

