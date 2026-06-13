# txt2tex User Guide

A comprehensive guide to writing mathematical specifications in txt2tex whiteboard notation.

txt2tex emits standard LaTeX, so you can take any `.tex` file to Overleaf or your usual editor at any point. Use it for one question per assignment if that's all you need — no commitment to the whole document. If you want to check how an expression renders without creating a file, `txt2tex -i` opens an interactive REPL.

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

See [README.md](../../README.md) for installation instructions, including:

- Installing via `pip install txt2tex`
- Setting up LaTeX packages for PDF generation
- Optional fuzz typechecker binary

---

## Document Structure

### Sections

```text
=== Introduction and Propositions ===
```

Generates: `\section*{Introduction and Propositions}`

Section titles may contain hyphens, colons, parentheses, and other
punctuation — the title text is captured verbatim and LaTeX-escaped
(DAT #15). Example:

```text
=== Foreign-key constraints ===
```

Generates: `\section*{Foreign-key constraints}` (the hyphen is preserved
as a literal hyphen, not widened to math-mode spacing).

### Solutions

```text
** Solution 1 **

Content here...
```

Generates: `\subsection*{Solution 1}`

**Note:** In previous versions, `** **` rendered `\section*` (same level as `=== ===`). It now renders `\subsection*`, one level smaller, so solutions nest under sections in the table of contents.

### Part Labels

```text
(a) First part
(b) Second part
(c) Third part
```

Each part gets proper spacing and formatting with `(a)\par\vspace{11pt}`.

**Note:** In previous versions, `(a)` rendered `\subsection*`. It now renders `\subsubsection*`, one level smaller.

### Table of Contents

Use `CONTENTS:` anywhere in the document to insert a table of contents at that point.

#### Heading hierarchy

The three structural markers map to three LaTeX heading levels:

| Input marker | LaTeX heading | TOC level |
|---|---|---|
| `=== Title ===` | `\section*{Title}` | section |
| `** Solution N **` | `\subsection*{Solution N}` | subsection |
| `(a)` (part label) | `\subsubsection*{(a)}` | subsubsection |

#### Depth control

`CONTENTS:` accepts an optional depth argument that controls which headings appear in the contents list. Depth is enforced by selectively emitting `\addcontentsline` calls — **not** via LaTeX's `tocdepth` counter, which has no effect on starred headings.

| Keyword | Depth | What appears |
|---|---|---|
| `CONTENTS:` (bare) | 2 | Sections and solutions |
| `CONTENTS: 1` | 1 | Sections only |
| `CONTENTS: 2` | 2 | Sections and solutions |
| `CONTENTS: 3` | 3 | Sections, solutions, and parts |
| `CONTENTS: full` | 3 | Sections, solutions, and parts |
| `CONTENTS: all` | 3 | Sections, solutions, and parts |

Bare `CONTENTS:` defaults to depth 2 — the right default for a typical question/solution document where you want the solutions listed but not every sub-part.

#### --toc-parts flag

The `--toc-parts` CLI flag forces parts `(a)`, `(b)`, etc. into the TOC regardless of the `CONTENTS:` depth keyword. Use it when you want full depth without adding `CONTENTS: full` to the source file.

#### Worked example

```text
CONTENTS: full

=== Question 1 ===

** Solution 1 **

TEXT: The proof proceeds by induction.

(a) Base case.

TEXT: We show the base case holds.

(b) Inductive step.

TEXT: Assume the hypothesis for n; prove it for n + 1.

=== Question 2 ===

** Solution 2 **
```

This produces a nested contents list:

```text
Contents
  Question 1
    Solution 1
      (a)
      (b)
  Question 2
    Solution 2
```

With bare `CONTENTS:` (depth 2), only "Question 1", "Solution 1", "Question 2", and "Solution 2" would appear — the `(a)` and `(b)` entries are suppressed.

**Part-label scope rule (DAT #18 / DAT #1):** A `(label)` token is recognised
as a structural part label only when it appears at the start of a paragraph
AND uses a short, recognised form: a single letter `(a)-(z)`, a single digit
`(1)-(9)`, or a short Roman numeral `(i)-(x)`.  Parenthesised words like
`(underlined)` or `(continued)` that appear mid-sentence or that are too long
are treated as literal prose, not part labels.

Example of `(word)` inside TEXT prose passing through as literal text:

```text
TEXT: Each primary key is highlighted (underlined) in the schema box.
```

Generates: `Each primary key is highlighted (underlined) in the schema box.`
— no spurious `\subsection*{(underlined)}` is inserted.

---

## Text Blocks

txt2tex provides four types of text blocks for different purposes:

### TEXT: - Smart Text with Formula Detection

Each `TEXT:` directive covers **one line**.  There is no multi-line `TEXT:`
block — `TEXT:` is not terminated by `END`.  For a multi-line paragraph,
write consecutive `TEXT:` lines (they coalesce — see "Paragraph coalescing"
below).  For multi-line raw LaTeX, use the multi-line [`LATEX:` block
form](#latex---raw-latex-passthrough).

Use `TEXT:` for normal prose where you want mathematical expressions
automatically detected and converted:

```text
TEXT: This is a plain text paragraph with => and <=> symbols.
TEXT: The set { x : N | x > 0 } contains positive integers.
TEXT: We write $\forall x : N | x \geq 0$ to mean all natural numbers.
```

**Features:**

- Operators converted: `=>` → $\Rightarrow$, `<=>` → $\Leftrightarrow$
- Formulas automatically detected: `{ x : N | x > 0 }` → $\{ x : \mathbb{N} \mid x > 0 \}$
- Sequence literals converted: `<a, b, c>` → $\langle a, b, c \rangle$
- **Math-keyword rewrite is opt-in via `$...$`** (#136 / DAT #11): bare
  English words like `exists`, `forall`, `group`, `union` are NOT
  automatically converted to math glyphs. Write `$\exists$`, `$\forall$`,
  etc. when you want the symbol.

  Compare:

  ```text
  TEXT: There exists a witness in the constraint set.
  ```

  Generates: `There exists a witness in the constraint set.` (bare
  `exists` stays as English prose.)

  ```text
  TEXT: We write $\exists x : N$ to mean "some natural number".
  ```

  Generates the `∃` glyph inside the inline `$...$`, English prose
  outside.

- Citations supported: `[cite key]` → (Author, Year) in Harvard style

**Paragraph coalescing (DAT #16):** Consecutive `TEXT:` directives on
adjacent lines (with no blank line between them) are joined into a single
paragraph.  A blank line between two `TEXT:` directives produces two
separate paragraphs.

```text
TEXT: First sentence of the paragraph.
TEXT: Second sentence continues here.
TEXT: Third sentence wraps up the thought.
```

The three lines above produce one paragraph. A blank line between any two of
them would start a new paragraph.

**Citations in TEXT blocks:**

```text
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

Like `TEXT:`, each `PURETEXT:` covers **one line** and is not terminated by
`END`.  Use multiple lines for multiple sentences.

Use `PURETEXT:` for bibliography entries or prose with punctuation that
would confuse the lexer:

```text
PURETEXT: Spivey, J.M. (1992) "The Z Notation" & references.
PURETEXT: Author's name, "quoted text", and more.
```

**Features:**

- Escapes LaTeX special characters: `&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`, `\`
- NO formula detection
- NO operator conversion
- NO keyword conversion (preserves literal `forall`, `exists`, `emptyset` for teaching)
- Preserves punctuation like quotes, commas, parentheses

### B: - B-Machine Verbatim Block

Use `B:` to embed an Atelier-B / B-Method machine listing verbatim. The body
is passed directly to a LaTeX `verbatim` environment — no Z-parser heuristics,
no keyword conversion, no escaping. Indentation and blank lines are preserved
exactly as written.

**Syntax:**

```text
B:
MACHINE MachineName
SETS
   MySet
VARIABLES
   v
INVARIANT
   v : MySet
INITIALISATION
   v := default
END
```

**Rules:**

- The `B:` line opens the block. Any text on the same line after `:` is ignored.
- Every line after `B:` is captured verbatim until a line that is exactly `END`
  at column 0 (no leading whitespace, no trailing content beyond a newline).
- The `END` line is part of the emitted block — it is the standard B-Method
  machine terminator (Abrial, *The B-Book*, 1996).
- Multiple `B:` blocks in one file are independent; each produces its own
  `\begin{verbatim}…\end{verbatim}` region.
- A `B:` block opened without a matching `END` is a lexer error; the error
  message cites the source line of the `B:` opener.

**Why not use `LATEX:` for B machines?**

`B:` wraps its body in `\begin{verbatim}…\end{verbatim}`, which gives you
fixed-width font and literal-character rendering — backslashes, braces, and
percent signs appear exactly as typed. The multi-line `LATEX:` block form
(see below) also captures the full body as one unit, but it emits the lines
as live LaTeX, not verbatim text. Use `B:` for listings you want rendered
as-written; use multi-line `LATEX:` for raw LaTeX you want interpreted.

**Example — full machine with prose before and after:**

```text
TEXT: Below is the B machine for the Trains case study.

B:
MACHINE Trains
SETS
   PLACE
VARIABLES
   trains
INVARIANT
   trains : iseq(PLACE * PLACE)
INITIALISATION
   trains := []
END

TEXT: The invariant ensures trains is a sequence of directed edges.
```

### LATEX: - Raw LaTeX Passthrough

Unlike `TEXT:` and `PURETEXT:` (one line each, no terminator), `LATEX:`
has **two forms**: a single-line directive `LATEX: <content>` and a
multi-line block `LATEX:` ... `END` (see [§Multi-line block
form](#multi-line-block-form) below).

Use `LATEX:` for custom LaTeX commands, environments, or formatting not
supported by txt2tex:

```text
LATEX: \begin{center}\textit{Custom formatting}\end{center}
LATEX: \vspace{1cm}
LATEX: \mycustomcommand{arg1}{arg2}
```

**Features:**

- NO escaping - raw LaTeX passed directly through
- Perfect for tikz diagrams, custom environments, special commands
- Used for bibliography setup with natbib

#### Multi-line block form

When you need to pass several lines of LaTeX through as a single unit — with
indentation preserved and no paragraph breaks inserted between lines — use the
block form instead of repeating `LATEX:` on every line.

**Syntax:** write `LATEX:` alone on a line (nothing after the colon except
optional trailing whitespace), then the body, then `END` at column 0.

```text
LATEX:
\begin{tikzpicture}
  \draw (0,0) -- (1,1);
  \node at (0.5,0.5) {midpoint};
\end{tikzpicture}
END
```

The body is emitted as live LaTeX — backslashes are interpreted, environments
are processed. The `END` terminator (column 0, no trailing text) closes the
block; `\end{...}` lines inside the body are not confused with `END`.

**When to use the block form vs. single-line `LATEX:`:**

| Situation | Use |
|-----------|-----|
| One short command | `LATEX: \vspace{1cm}` |
| Multi-line environment or diagram | Block form |
| Indentation must be preserved | Block form |
| Content should appear as literal text (verbatim) | `B:` instead |

A `LATEX:` block opened without a matching `END` is a lexer error; the error
message cites the source line of the opener.

For B-machine listings specifically, use `B:` — it wraps the body in
`\begin{verbatim}` so backslashes and braces appear as typed.

**Bibliography Setup (Harvard Style):**

txt2tex automatically includes the `natbib` package for author-year citations. You can manage bibliographies using either approach:

<!-- markdownlint-disable-next-line MD036 -->
**Bibliography File Approach (Recommended)**

Use a separate `.bib` file with document-level directives:

```text
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

<!-- markdownlint-disable-next-line MD036 -->
**Manual Bibliography Approach**

For custom formatting or when you don't have a `.bib` file, use LATEX: blocks to define your bibliography manually:

```text
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

The multi-line block form can also be used for the bibliography, which keeps
the entire environment as one block rather than one `LATEX:` directive per
line:

```text
LATEX:
\setlength{\leftskip}{0pt}
\begin{thebibliography}{Woodcock, n.d.}

\bibitem[Spivey, 1992]{spivey92} Spivey, J.M. (1992). \textit{The Z Notation: A Reference Manual}. Prentice Hall.

\bibitem[Woodcock and Davies, 1996]{woodcock96} Woodcock, J. and Davies, J. (1996). \textit{Using Z}. Prentice Hall.

\end{thebibliography}
END
```

**Note**: If `BIBLIOGRAPHY:` is specified, the bibliography file approach takes precedence. LATEX blocks will still work for other purposes.

### PAGEBREAK: - Insert Page Break

```text
PAGEBREAK:
```

Generates: `\newpage` to start a new page in the PDF.

---

## Propositional Logic

<!-- markdownlint-disable-next-line MD036 -->
*Lecture 1: Introduction and propositions*

### Basic Operators

```text
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

```text
lnot p land q      →  (¬p) ∧ q
p land q => r      →  (p ∧ q) ⇒ r
p => q => r        →  p ⇒ (q ⇒ r)    [right-associative]
```

### Truth Tables

```text
TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T
```

Generates a centered LaTeX tabular environment with proper formatting.

### Equivalence Chains

```text
EQUIV:
p land q
<=> q land p [commutative]
<=> q land p [idempotent]
```

Generates an array environment with justifications flush-right. Each step is
joined by $\Leftrightarrow$ (logical equivalence).

`ARGUE:` is an alias for `EQUIV:` and produces identical output.

### Equality Chains

Use `EQUAL:` when the steps are expressions of the same Z type — arithmetic,
sequence length, function values — and the correct connective is `=`, not
$\Leftrightarrow$.

```text
EQUAL:
length s
length (tail s) + 1 [by definition of length]
```

Each step is joined by `=` in the rendered output. Justifications work
identically to EQUIV: chains.

When to choose `EQUAL:` over `EQUIV:`:

- Steps are natural-number valued (lengths, counts, cardinalities)
- Steps are set-valued or function-valued expressions
- You want to write an equational calculation, not a propositional equivalence

#### Justifications in Equivalence and Equality Chains

Justifications are **free-form text** in square brackets after each step. You can write any reasoning you want:

```text
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

- `o9` → $\semi$ (forward composition)
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

```text
<=> p lor (lnot p land q) [land land true]
```

Renders as: $\Leftrightarrow p \lor (\lnot p \land q)$ with justification [$\land$ $\land$ true]

Example with relation operators:

```text
<=> (exists y : Y | w |-> y elem (R o9 S) land y |-> z elem T) [definition of o9]
```

Renders as: $\Leftrightarrow \exists y : Y \bullet w \mapsto y \in (R \semi S) \land y \mapsto z \in T$ with justification [definition of $\semi$]

---

## Predicate Logic

<!-- markdownlint-disable-next-line MD036 -->
*Lecture 2: Predicate logic*

### Quantifiers

#### Universal Quantification (∀)

```text
forall x : N | x > 0
```

Generates: $\forall x : \mathbb{N} \bullet x > 0$

**With bullet separator (Phase 40):**

```text
forall x : N | x > 0 . x < 10
```

Generates: $\forall x : \mathbb{N} \mid x > 0 \bullet x < 10$

The bullet separator (`.`) separates the constraint (filtering condition) from the body (conclusion). This is equivalent to:

```text
forall x : N | (x > 0 => x < 10)
```

#### Existential Quantification (∃)

```text
exists y : Z | y < 0
```

Generates: $\exists y : \mathbb{Z} \bullet y < 0$

**With bullet separator (Phase 40):**

```text
exists y : Z | y < 0 . y > -10
```

Generates: $\exists y : \mathbb{Z} \mid y < 0 \bullet y > -10$

#### Unique Existential Quantification (∃₁)

```text
exists1 x : N | x * x = 4
```

Generates: $\exists_1 x : \mathbb{N} \bullet x \times x = 4$

**With bullet separator (Phase 40):**

```text
exists1 x : N | x * x = 4 . x > 0
```

Generates: $\exists_1 x : \mathbb{N} \mid x \times x = 4 \bullet x > 0$

**Note on bullet separator limitations:**

In rare cases where the bullet separator is followed by an identifier and then `=`, the parser may treat it as a field projection rather than a bullet separator. In these cases, use implication (`=>`) instead:

```text
// Use implication for this pattern:
forall i, j : dom f | f i = f j => i = j

// Instead of bullet (ambiguous with projection):
forall i, j : dom f | f i = f j . i = j
```

The bullet separator works correctly when followed by set operators (`elem`, `notin`, `subset`), logical operators (`land`, `lor`, `=>`), or comparisons (`<`, `>`, `<=`, `>=`, `!=`).

#### Definite Description (μ)

The mu operator (μ) denotes "the unique value satisfying a predicate":

```text
mu x : N | x * x = 4 land x > 0
```

Generates (in fuzz mode): $(\mu x : \mathbb{N} \mid x \times x = 4 \land x > 0)$

**Note**: In fuzz mode, mu expressions use `|` as the separator and are wrapped in parentheses. The syntax is: `mu variable : Type | predicate`

**With expression part** (selecting from a set):

```text
mu x : N | x elem S . f(x)
```

Generates: `(\mu x : \mathbb{N} \mid x \in S @ f(x))`

The mu operator is typically used when you know there exists exactly one element satisfying the predicate and you want to refer to that element directly.

### Multi-Variable Quantifiers

```text
forall x, y : N | x = y
exists a, b, c : Z | a = b
```

Comma-separated variables share the same domain.

### Nested Quantifiers

```text
forall x : N | exists y : N | x = y
```

**Important:** Nested quantifiers in `land`/`lor` expressions must be parenthesized:

```text
✅ Correct:   forall x : N | x > 0 land (forall y : N | y > x)
❌ Incorrect: forall x : N | x > 0 land forall y : N | y > x
```

### Schema-text Quantification

Z RM §3.10 permits schemas to appear directly as quantifier bindings, without
spelling out all the variables and domain types manually.  txt2tex supports all
four forms for `forall`, `exists`, and `exists1`.

#### State-change binding (ΔS)

```text
exists Delta S | P
```

Generates (fuzz mode): `\exists \Delta S @ P`

Asserts there is some state change of schema `S` satisfying predicate `P`.
fuzz expands `\Delta S` into the full before-and-after variable list; the
engine emits the binding literally.

Example — miniature promotion predicate (mirrors SBM Ex 21):

```text
exists Delta BoxOffice | Promote
```

#### Read-only binding (ΞS)

```text
exists Xi S | P
```

Generates: `\exists \Xi S @ P`

Like `Delta` but additionally constrains that all outputs equal their
inputs (the state is not changed).

#### Schema-as-declaration (S)

```text
exists S | P
```

Generates: `\exists S @ P`

Existentially quantifies over all components of schema `S`.  `S` must
start with an uppercase letter (Z naming convention) to distinguish it
from a value variable.

#### Primed schema (S')

```text
exists S' | P
```

Generates: `\exists S^{\prime} @ P`

Like the bare form but uses the after-state components of schema `S`.

#### forall and exists1

All three quantifiers (`forall`, `exists`, `exists1`) support every
schema binding form:

```text
forall Delta S | P         →  \forall \Delta S @ P
exists1 Delta S | P        →  \exists_1 \Delta S @ P
exists Xi S | P            →  \exists \Xi S @ P
```

#### Disambiguation

The parser uses the first character of the identifier to distinguish a
schema name from a variable name:

- Uppercase initial letter → schema binding (e.g., `BoxOffice`, `S`, `State`)
- Lowercase initial letter → value binding (e.g., `x`, `state`, `n`)

This follows Z's own naming convention.  To force a value binding for an
identifier starting with uppercase, add a `:` domain declaration:

```text
exists S : SchemaType | P      [value binding — S is a variable of SchemaType]
exists S | P                   [schema binding — S is the schema name]
```

See the [Schemas section](#schemas) for how `Delta` and `Xi` are defined.

### Declaration and Binding

The colon `:` declares the type of a variable:

```text
forall x : N | predicate        [declaration]
{ x : N | predicate }          [set comprehension]
lambda x : N . expression      [lambda expression]
```

---

## Equality

<!-- markdownlint-disable-next-line MD036 -->
*Lecture 3: Equality*

### Equality Operator

```text
x = y            →  x = y
x != y           →  x ≠ y
```

### Unique Existence (∃₁)

"There is a unique value that..."

```text
exists1 x : N | x = 5
```

Generates: $\exists_1 x : \mathbb{N} \bullet x = 5$

### Mu Operator (μ)

"The unique value that..."

```text
mu x : N | x > 0
```

Generates: $(\mu x : \mathbb{N} \mid x > 0)$  (fuzz mode wraps the
binder in parens and uses `\mid`, not `\bullet`; see Predicate Logic
section)

---

## Sets and Types

<!-- markdownlint-disable-next-line MD036 -->
*Lecture 5: Sets and types*

### Set Notation

```text
{1, 2, 3}                    →  {1, 2, 3}       [set literal]
{}                           →  {}              [empty set]
```

### Set Membership

```text
x elem A         →  x ∈ A       ['is an element of']
x notin B        →  x ∉ B       ['not an element of']
```

**Note:** Use `elem` for set membership. The `in` keyword was deprecated in favor of `elem` to avoid ambiguity with English prose.

### Set Relations

```text
A subset B       →  A ⊆ B       [subset - includes equality]
A psubset B      →  A ⊂ B       [strict/proper subset - excludes equality]
A union B        →  A ∪ B       [union]
A intersect C    →  A ∩ C       [intersection]
A \ B            →  A ∖ B       [set difference]
```

### Power Set

```text
P S              →  P S         [power set - set of all subsets]
P1 S             →  P₁ S        [non-empty power set]
F S              →  F S         [set of finite subsets]
P (A cross B)    →  P (A × B)   [power set of Cartesian product - needs parentheses]
P (Z cross Z)    →  P (ℤ × ℤ)   [set of all relations on integers]
```

### Cardinality

```text
# S              →  # S         [cardinality of a finite set]
# {1, 2, 3}      →  # {1, 2, 3}
```

### Cartesian Product

```text
A cross B        →  A × B       [Cartesian product]
(x, y)           →  (x, y)      [ordered pair]
(a, b, c)        →  (a, b, c)   [tuple]
```

### Tuple Component Selection and Field Projection

**Numeric projection (tuples):**

```text
p.1              →  p.1         [first component]
p.2              →  p.2         [second component]
p.3              →  p.3         [third component]
```

**Note:** Numeric projections (`.1`, `.2`, `.3`) are **not supported by fuzz** - they violate the fuzz grammar which requires identifiers after the period, not numbers. Use named schema fields instead (see below).

**Named field projection (schemas):**

```text
e.name           →  e.name      [access 'name' field]
record.status    →  record.status [access 'status' field]
person.age       →  person.age  [access 'age' field]
```

Named field projections work with schema types:

```text
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

```text
record.inner.field    →  record.inner.field
```

### Set Comprehension

**Set by predicate:**

```text
{ x : N | x > 0 }
```

Generates: $\{ x : \mathbb{N} \mid x > 0 \}$

**Set by expression:**

```text
{ x : N | x > 0 . x * x }
```

Generates: $\{ x : \mathbb{N} \mid x > 0 \bullet x \times x \}$

The bullet (`•`) separates the predicate from the expression.

**Multi-variable:**

```text
{ x, y : N | x = y }
```

**Without domain:**

```text
{ x | x elem A }
```

**With maplets:**

```text
{1 |-> a, 2 |-> b, 3 |-> c}
```

Generates: $\{1 \mapsto a, 2 \mapsto b, 3 \mapsto c\}$

### Distributed Union and Intersection

```text
bigcup S         →  ⋃ S         [distributed union]
bigcap S         →  ⋂ S         [distributed intersection]
```

**Automatic parenthesisation of nested prefix operators (fuzz mode):**

Z RM §3.7 requires prefix-generic operators (`seq`, `P`, `dom`, `ran`,
`bigcup`, `bigcap`, etc.) to take an *atomic* operand. A nested prefix
application is not atomic, so the engine wraps it in parens automatically.
You do not need to add explicit parens in your source:

```text
seq (P X)              →  \seq~(\power X)     ← parens added by engine
ran (bigcup (ran s))   →  \ran~(\bigcup~(\ran s))
```

### Standard Sets

```text
Z                →  ℤ           [the set of integers]
N                →  ℕ           [natural numbers]
```

Note: Use blackboard bold for standard number sets by capitalizing: `N`, `Z`.

---

## Definitions

<!-- markdownlint-disable-next-line MD036 -->
*Lecture 6: Definitions*

### Basic Type Definition (Given Types)

```text
given Person, Company
```

Generates: `\begin{zed}[Person, Company]\end{zed}`

### Abbreviations

Abbreviations define shorthand names for types or expressions.  They can appear standalone at the top level (the engine wraps them in `zed` automatically) or inside an explicit `zed...end` block when you want to group several with other paragraph kinds:

**Basic abbreviations:**

```text
zed
  Pairs == N cross N
end

zed
  Triples == N cross N cross N
end
```

Generates: `\begin{zed} Pairs == ℕ × ℕ \end{zed}` and `\begin{zed} Triples == ℕ × ℕ × ℕ \end{zed}`

**With generic parameters:**

```text
zed
  [X] Pair == X cross X
end

zed
  [X, Y] Product == X cross Y
end
```

**Compound identifiers** (names with operator suffixes like `R+`, `R*`):

```text
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

```text
zed
  given Entry
  Status ::= active | inactive
  DefaultStatus == active
end
```

This generates a single `\begin{zed}...\end{zed}` block containing the given type, free type, and abbreviation.

### Free Types

**Simple free types:**

```text
Status ::= active | inactive | pending
```

**Recursive free types with constructor parameters:**

```text
Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩
List ::= nil | cons⟨N × List⟩
```

Both Unicode `⟨⟩` and ASCII `<>` angle brackets are supported:

```text
Tree ::= stalk | leaf<N> | branch<Tree × Tree>
```

### Syntax Environment

For complex free type definitions with multiple types, the `syntax` environment provides column-aligned layout similar to BNF grammars:

**Basic syntax block:**

```text
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

```text
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

```text
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

```text
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

```text
gendef [X]
  identity : X -> X
where
  forall x : X | identity(x) = x
end
```

**Multiple declarations (separate lines):**

```text
gendef [X, Y]
  fst : X cross Y -> X
  snd : X cross Y -> Y
where
  forall x : X; y : Y | fst(x, y) = x land snd(x, y) = y
end
```

**Multiple declarations (semicolon-separated on one line):**

```text
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

```text
gendef [X]
  Tree_X ::= leaf | node⟨X × Tree_X × Tree_X⟩
end
```

**Correct workaround**: Define the free type separately with `given`, then define operations in `gendef`:

```text
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

```text
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

```text
schema Container[X]
  contents : seq X
  capacity : N
where
  # contents <= capacity
end
```

You can then define operations on the generic schema using `gendef`:

```text
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

<!-- markdownlint-disable-next-line MD036 -->
*Lecture 7: Relations*

### Maplet (↦)

```text
x |-> y          →  x ↦ y       [maplet - ordered pair constructor]
```

### Relation Type

```text
X <-> Y          →  X ↔ Y       [set of all relations between X and Y]
```

### Domain and Range

```text
dom R            →  dom R       [domain of relation]
ran R            →  ran R       [range of relation]
```

### Domain and Range Restriction

```text
S <| R           →  S ◁ R       [domain restriction]
R |> T           →  R ▷ T       [range restriction]
```

### Domain and Range Corestriction (Anti-restriction)

```text
S <<| R          →  S ⩤ R       [domain corestriction]
R |>> T          →  R ⩥ T       [range corestriction]
```

### Relational Inverse

```text
R~               →  R⁻¹         [relational inverse - postfix]
inv R            →  inv R       [relational inverse - prefix]
```

### Relational Image

```text
R(| S |)         →  R(⦇ S ⦈)    [relational image]
```

**Examples:**

```text
parentOf(| {john} |)
R(| {1, 2, 3} |)
(R o9 S)(| A |)
```

### Relational Composition

```text
R o9 S           →  \semi       [forward relational composition (fuzz \semi)]
R comp S         →  \comp       [backward relational composition (fuzz \comp)]
```

**Note:** Semicolon (`;`) in expression context emits `\semi` (forward composition). In declaration context (inside `gendef`, `axdef`, `schema` blocks) it separates declarations. For clarity, prefer `o9` for forward composition in expressions.

**Composition vs Nested Application:**

| Syntax | Meaning | Type | Usage |
|--------|---------|------|-------|
| `g o9 f` | Function composition | `A -> C` (function) | Creates new function |
| `g(f(x))` | Nested application | `C` (value) | Computes specific result |

**Example:**

```text
successor : N -> N
square : N -> N

squareSuccessor == square o9 successor    ← Defines a new function
result = square(successor(5))             ← Computes the value 36
```

Both evaluate the same when applied to arguments: `(g o9 f)(x) = g(f(x))`, but composition creates a reusable function while nested application computes a specific value.

### Closures

```text
R+               →  R⁺          [transitive closure]
R*               →  R*          [reflexive-transitive closure]
```

**Closure operators** (postfix):

- `+` (transitive): follow relation one or more times
- `*` (reflexive-transitive): follow relation zero or more times

Note: Reflexive closure (`rcl`) and symmetric closure (`s`) are not yet implemented.

### Compound Identifiers in Definitions

Postfix operators (`+`, `*`, `~`) can be used as part of identifier names in abbreviations and schema definitions:

```text
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

```text
# R+ is the abbreviation name (compound identifier)
R+ == {a, b : N | b > a}

# R+ in expression context (operator applied to R)
S == R+

# Works with underscores
rel_1+ == {x, y : N | x < y}     →  rel_1⁺
```

---

## Functions

<!-- markdownlint-disable-next-line MD036 -->
*Lecture 8: Functions*

### Function Types

**Partial and Total Functions:**

```text
f : X +-> Y      →  X ⇀ Y       [partial function]
f : X -> Y       →  X → Y       [total function]
```

**Injections (one-to-one):**

```text
f : X >+> Y      →  X ⤔ Y       [partial injection]
f : X -|> Y      →  X ⤔ Y       [partial injection - alternative]
f : X >-> Y      →  X ↣ Y       [total injection]
```

**Surjections (onto):**

```text
f : X +->> Y     →  X ⤀ Y       [partial surjection]
f : X -->> Y     →  X ↠ Y       [total surjection]
```

**Bijections (one-to-one and onto):**

```text
f : X >->> Y     →  X ⤖ Y       [total bijection]
f : X >7-> Y     →  X ↣→ Y      [partial bijection]
```

**Finite partial functions:**

```text
f : Year 77-> Table     →  Year ⇸ Table    [finite partial function]
```

### Function Application

**Standard application:**

```text
f(x)             →  f(x)
g(x, y, z)       →  g(x, y, z)
```

**Important:** Function application requires explicit parentheses - juxtaposition is not supported:

```text
✅ Correct:   f(x), dom(R)
❌ Incorrect: f x, dom R
```

**Generic instantiation:**

```text
seq(N)           →  seq N
P(X)             →  P X
```

**Type application also requires parentheses:**

```text
✅ Correct:   seq(Entry), P(Person)
❌ Incorrect: seq Entry, P Person
```

**Nested application:**

```text
f(g(h(x)))       →  f(g(h(x)))
```

**General function application:**

Any expression can be applied as a function:

```text
(f ++ g)(x)              [override then apply]
⟨a, b, c⟩(2)             [sequence indexing]
(R o9 S)(| A |)          [composition then image]
```

### Lambda Expressions (λ)

**Basic lambdas:**

```text
lambda x : N . x * x
lambda f : X -> Y . f(x)
```

**Multi-variable:**

```text
lambda x, y : N . x + y
lambda a, b, c : Z . a
```

**Nested lambdas:**

```text
lambda x : X . lambda y : Y . (x, y)
```

### Function Override (⊕)

```text
f ++ g           →  f ⊕ g       [function override]
f ++ g ++ h      →  f ⊕ g ⊕ h   [left-associative]
```

The second function takes precedence for overlapping domains.

### Range Operator ('up to')

```text
1..10            →  1 ‥ 10      ['up to']
1993..current    →  1993 ‥ current
```

Represents the set `{1, 2, 3, ..., 10}`.

### Function Definitions

Functions are typically defined using `axdef` or `gendef` (for generic functions).

**Simple total function:**

```text
axdef
  square : N -> N
where
  forall n : N | square(n) = n * n
end
```

**Partial function:**

```text
axdef
  predecessor : N +-> N
where
  forall n : N | n > 0 => predecessor(n) = n - 1
end
```

Note: `predecessor` is partial because 0 has no predecessor in N.

**Generic function:**

```text
gendef [X]
  identity : X -> X
where
  forall x : X | identity(x) = x
end
```

**Generic function with multiple type parameters:**

```text
gendef [X, Y]
  first : X cross Y -> X
where
  forall x : X; y : Y | first(x, y) = x
end
```

### Function Operators

**Domain and Range:**

```text
dom f            →  dom f       [domain of function]
ran f            →  ran f       [range of function]
```

**Domain Restriction:**

```text
A <| f           →  A ◁ f       [restrict f to domain A]
```

**Range Restriction:**

```text
f |> B           →  f ▷ B       [restrict f to range B]
```

**Domain Subtraction:**

```text
A <<| f          →  A ⩤ f       [remove A from domain]
```

**Range Subtraction:**

```text
f |>> B          →  f ⩥ B       [remove B from range]
```

**Function Composition:**

```text
f o9 g           →  \semi       [forward composition (fuzz \semi): (f ; g)(x) = g(f(x))]
f comp g         →  \comp       [backward composition (fuzz \comp): (f ∘ g)(x) = f(g(x))]
```

**Function Inverse:**

```text
f~               →  f⁻¹         [inverse function (only for injective)]
```

**Relational Image:**

```text
f(| A |)         →  f⟦A⟧        [image of set A under f]
```

### Examples of Function Properties

**Injective (one-to-one):**

```text
given StudentId, Student

axdef
  studentRecord : StudentId >-> Student
where
  forall id1, id2 : StudentId |
    id1 /= id2 => studentRecord(id1) /= studentRecord(id2)
end
```

**Surjective (onto):**

```text
axdef
  modulo3 : N -->> {0, 1, 2}
where
  forall n : N | modulo3(n) = n mod 3 land
  forall r : {0, 1, 2} | exists n : N | modulo3(n) = r
end
```

**Recursive function on sequences:**

```text
gendef [X]
  length : seq X -> N
where
  length(<>) = 0 land
  forall x : X; s : seq X | length(<x> ^ s) = 1 + length(s)
end
```

**Higher-order function:**

```text
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

<!-- markdownlint-disable-next-line MD036 -->
*Lecture 9: Sequences*

### Sequence Types

```text
seq(X)           →  seq X       [set of all sequences of type X]
iseq(X)          →  iseq X      [set of all injective sequences]
```

**With generic instantiation:**

```text
seq[N]
iseq[Entry]
```

### Sequence Literals

**Unicode angle brackets:**

```text
⟨⟩               →  ⟨⟩          [empty sequence]
⟨a⟩              →  ⟨a⟩
⟨a, b, c⟩        →  ⟨a, b, c⟩
```

**ASCII angle brackets (alternative):**

```text
<>               →  ⟨⟩          [empty sequence]
<a>              →  ⟨a⟩
<a, b, c>        →  ⟨a, b, c⟩
```

Both produce identical LaTeX output.

### Concatenation (⌢)

**Unicode operator (always works):**

```text
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

```text
<a> ^ <b>        →  ⟨a⟩ ⌢ ⟨b⟩      [sequence literals]
s ^ t            →  s ⌢ t           [sequence variables]
f(x) ^ <y>       →  f(x) ⌢ ⟨y⟩     [function result]
```

**Note**: Multi-line concatenation (splitting across lines) is not currently supported.

**Relation iteration examples (NO space before `^`):**

```text
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

```text
❌ <x>^<y>       →  ERROR: "use '> ^ <' not '>^<'"
✅ <x> ^ <y>     →  ⟨x⟩ ⌢ ⟨y⟩
```

**Note:** If typing `⌢` (U+2040) is difficult, remember you can use ` ^ ` (with spaces) as ASCII alternative.

### Filter

```text
s ↾ A            →  s ↾ A       [sequence filter - restricts sequence s to elements in set A]
s filter A       →  s ↾ A       [ASCII alternative using 'filter' keyword]
```

The filter operator restricts a sequence to only include elements from a given set.

**ASCII Notation:** Use the `filter` keyword (e.g., `s filter A`)
**Unicode Alternative:** Use `↾` (U+21BE) if preferred

**Example:**

```text
records filter {x : Entry | x.viewed = yes}    [filter sequence to viewed entries]
```

**Note:** The filter operator is distinct from `|>` (range restriction for relations).

### Sequence Length

```text
# s              →  # s         [length - overloading of cardinality]
```

### Sequence Functions

```text
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

```text
f(<>) = 0
```

**Cons pattern (head and tail):**

```text
f(<x> ^ s) = x + f(s)
```

**In axiomatic definitions:**

```text
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

```text
bag(X)           →  bag X       [set of all bags of type X]
```

**Bag literals:**

```text
b1 == [[x]]            →  b₁ = ⟦x⟧         [bag in abbreviation]
b2 == [[a, b, c]]      →  b₂ = ⟦a, b, c⟧
```

**Note**: Bag literals must appear in an abbreviation or expression context, not as standalone statements.

**Bag union:**

```text
b1 ⊎ b2          →  b1 ⊎ b2     [bag union - combines two bags]
b1 bag_union b2  →  b1 ⊎ b2     [ASCII alternative using 'bag_union' keyword]
```

The bag union operator combines two bags, preserving multiplicities (unlike set union which removes duplicates).

**ASCII Notation:** Use the `bag_union` keyword (e.g., `b1 bag_union b2`)
**Unicode Alternative:** Use `⊎` (U+228E) if preferred

**Bag difference (Z RM §4.6.2):**

```text
b1 bag_diff b2        →  b1 \uminus b2   [bag difference]
coins bag_diff [[c?]] →  coins \uminus [\![ c? ]\!]
```

The bag difference operator `bag_diff` emits `\uminus`. For bags `b1` and `b2` and any element `x`, `(b1 bag_diff b2)(x) = max(0, b1(x) - b2(x))` — multiplicity clamped at zero. This is the natural notation for operations such as removing a coin from a multiset:

```text
coins' = coins bag_diff [[c?]]
```

**ASCII Notation:** Use the `bag_diff` keyword — there is no single-character Unicode alternative for `\uminus` in txt2tex source.

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

```text
zed
  x > 0
end
```

**Quantified predicates:**

```text
zed
  forall x : N | x >= 0
end
```

```text
zed
  exists n : NAME | birthday(n) elem December
end
```

**Given types:**

```text
zed
  given Person, Company
end
```

**Free types:**

```text
zed
  Status ::= active | inactive | pending
end
```

**Abbreviations:**

```text
zed
  Evens == { n : N | n mod 2 = 0 }
end
```

**Abbreviations with generic parameters:**

```text
zed
  [X] Pair == X cross X
end
```

**Compound identifier abbreviations:**

```text
zed
  R+ == { a, b : N | b > a }
end
```

**Mixed content (multiple constructs in one block):**

```text
zed
  given Entry
  Status ::= active | inactive
  DefaultStatus == active
end
```

**Complex predicates:**

```text
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

```text
{ x : N | x > 0 . x * x }          ← Bare expression, renders inline
```

**Zed block (unboxed paragraph):**

```text
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

```text
axdef
  Doubled : P Z             ← Declaration required
where
  Doubled = { z : Z | z mod 2 = 0 . z * 2 }  ← Expression in where: OK
end
```

**Schema (boxed, with declarations):**

```text
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

```text
schema Library
  books : F BookId
  book_chapters : BookId +-> F ChapterId
where
  books subset dom book_chapters
end

** Later in document **
Answer == {b : dom book_chapters | ...}  ❌ FUZZ ERROR: book_chapters not declared
```

The identifiers `books` and `book_chapters` exist only within the `Library` schema. They are LOCAL components that define the schema's type structure.

**axdef blocks** have **GLOBAL scope** - all declared identifiers are accessible throughout the entire document:

```text
axdef
  books : F BookId
  book_chapters : BookId +-> F ChapterId
where
  books subset dom book_chapters
end

** Later in document **
Answer == {b : dom book_chapters | ...}  ✅ OK: book_chapters is globally accessible
```

All identifiers declared in `axdef` are GLOBAL and can be referenced anywhere after the declaration.

**When to use which:**

- **Use schema** to define reusable types/templates (like data structures or state spaces) that represent encapsulated components
- **Use axdef** to declare global constants, variables, or functions that need to be referenced elsewhere in your specification

**Other globally scoped declarations:**

- `given` types → `given BookId, AuthorId`
- Abbreviations → `ChapterId == N1`
- Generic definitions → `gendef [X, Y] fst : X cross Y -> X`
- Free types → `Color ::= red | blue | green`

**Common mistake:** Using a named schema when you need global identifiers. If other parts of your specification need to reference the declared components, use `axdef` instead.

### Axiomatic Definitions

Define global constants and their properties:

```text
axdef
  population : N
where
  population > 0
end
```

**With generic parameters:**

```text
axdef [T]
  identity : T
where
  identity = identity
end
```

**Multiple declarations (semicolon-separated):**

```text
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

### Paragraph Ordering Convention for Dependent Definitions

The Z Reference Manual (§3.5) allows all names declared in a single `axdef` or `gendef`
paragraph to enter scope simultaneously. Fuzz accepts cross-references between declarations
in the same block — this is valid Z.

The Z community convention (Spivey, *Understanding Z*) favours splitting dependent definitions
into separate paragraphs in dependency order. Each paragraph then stands as a self-contained
mathematical object whose reliance on earlier paragraphs is structurally visible to the reader.

**Combined form** (valid Z, accepted by fuzz):

```text
axdef
  maxSeq : seq(N) -> N
  minSeq : seq(N) -> N
  maxDiff : seq(N) -> N
where
  forall s : seq(N) | maxSeq(s) = ...
  forall s : seq(N) | minSeq(s) = ...
  forall s : seq(N) | maxDiff(s) = maxSeq(s) - minSeq(s)
end
```

**Sequential form** (recommended):

```text
axdef
  maxSeq : seq(N) -> N
where
  forall s : seq(N) | maxSeq(s) = ...
end

axdef
  minSeq : seq(N) -> N
where
  forall s : seq(N) | minSeq(s) = ...
end

axdef
  maxDiff : seq(N) -> N
where
  forall s : seq(N) | maxDiff(s) = maxSeq(s) - minSeq(s)
end
```

A Z examiner prefers the sequential form because each paragraph can be read and understood
independently; the dependency of `maxDiff` on `maxSeq` and `minSeq` is evident from
document order rather than inferred from the predicate. This is a presentation convention,
not a type-checking requirement. txt2tex faithfully renders either form — the choice is
the author's.

### Schemas

Define state spaces and operations:

```text
schema State
  count : N
where
  count >= 0
end
```

**Important:** Schema components (`count` in this example) have LOCAL scope and cannot be referenced outside the schema. If you need globally accessible identifiers, use `axdef` instead (see "Scoping Rules" above).

**With generic parameters:**

```text
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

```text
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
  x > 0 \land y > 0
\end{schema}
```

### Anonymous Schemas

Schemas without names for inline use:

```text
schema
  x : N
  y : N
where
  x + y = 10
end
```

### Schema Declarations

The `where` keyword separates declarations from predicates:

```text
schema Name
  declarations
where
  predicates
end
```

### Schema Inclusion (Bare, Δ, Ξ)

A declaration line with no colon is a **schema inclusion** — it brings the
components and predicates of the named schema into the enclosing block.

#### Bare inclusion

```text
schema LoggedInUser
  User
  sessionToken : N
where
  sessionToken > 0
end
```

`User` on its own line (no colon) brings all User components into LoggedInUser.
The generated LaTeX is:

```latex
\begin{schema}{LoggedInUser}
User \\
sessionToken : \nat
\where
sessionToken > 0
\end{schema}
```

#### Delta inclusion (Δ) — state-and-operation

`Delta S` is the Z RM §3.7 convention for including a schema in an operation
that modifies state.  It signals that both the before-state `S` and after-state
`S'` are present.

```text
schema IncrCounter
  Delta Counter
  increment? : N
where
  count' = count + increment?
end
```

Generates: `\Delta Counter \\`

#### Xi inclusion (Ξ) — read-only operation

`Xi S` is the Z RM §5.2 convention for a schema that does not modify state.

```text
schema ReadCount
  Xi Counter
  result! : N
where
  result! = count
end
```

Generates: `\Xi Counter \\`

#### Generic instantiation in inclusions

Inclusions can carry type parameters:

```text
schema PushNat
  Delta Stack[N]
  value? : N
end
```

Generates: `\Delta Stack[\nat] \\`

#### Disambiguation rule

The parser uses one-pass scan-ahead to tell inclusions from typed declarations:

- **Colon before newline** → typed declaration: `count, limit : N`
- **No colon before newline** → schema inclusion: `Counter`

This means `count, limit : N` (two variables sharing a type) is never confused
with a bare inclusion, even when the names would otherwise match a schema name.

#### Schema-as-predicate in where clause

Once a schema is included in the declaration list, its name can appear in the
`where` clause as a predicate.  Conjunction `S1 land S2` applies both:

```text
schema AB
  A
  B
  z : N
where
  A land B
  z = x + y
end
```

**See:** `examples/10_schemas/delta_xi_inclusion.txt`,
`examples/10_schemas/schema_as_predicate.txt`

#### θ-Expression (`theta`)

`theta S` constructs the binding whose components are the in-scope variables
matching schema S's signature (Z RM §3.10).

```text
theta Booking'        → \theta Booking'   (after-state binding)
theta AirlineState    → \theta AirlineState
theta S = theta S'    → \theta S = \theta S'  (frame condition)
```

The typical use is packaging a state snapshot inside a maplet:

```text
schema AddBooking
  Delta AirlineState
  bookingId? : BookingId
  Booking
where
  bookings' = bookings oplus { bookingId? |-> theta Booking' }
end
```

**Syntax rules:**

| Rule | Detail |
|------|--------|
| Keyword | `theta` (lowercase; `\theta` is the Greek letter) |
| Schema reference | Any valid identifier, including Phase-0 decorated forms (`S'`, `S?`) |
| Decoration of keyword | Forbidden — `theta'` raises a LexerError |
| Precedence | Primary expression, same level as `Identifier` |

**Generated LaTeX:** `theta S` → `\theta S`  Works under both `fuzz.sty`
(default) and `--zed` mode; `\theta` is a standard LaTeX Greek letter macro.

**See:** `examples/10_schemas/theta_binding.txt`

#### Horizontal Schema Definitions (`defs`)

`Name [generics]? defs RHS` writes a Z RM §3.8 *horizontal definition* —
assigns a new name to a schema expression without a boxed schema environment.

```text
OpAlias defs Delta Counter
NatPair defs [ x, y : N | x < y ]
StackAlias[X] defs GenStack[X]
```

| Aspect | Detail |
|--------|--------|
| Keyword | `defs` (lowercase, reserved) |
| Output environment | `\begin{zed} Name \defs RHS \end{zed}` |
| `\defs` macro | Defined in `fuzz.sty` line 280 as `\widehat=` |
| RHS: schema reference | Plain or decorated (`Delta`/`Xi`) identifier |
| RHS: inline schema text | `[ decl-list \| pred-list ]` |
| Generic LHS | `Name[X, Y] defs RHS` |
| Decoration of keyword | Forbidden — `defs'` raises LexerError |
| Schema calculus RHS | `;`, `>>`, `hide`, `project` — see below |

**Inline schema text:** declarations are separated by `;`; predicates are
separated by `;` in the source and joined with `\land` in the output.

```text
BoundedNat defs [n : N | n > 0; n < 100]
// → BoundedNat \defs [ n : \nat | n > 0 \land n < 100 ]
```

**Generated LaTeX:** `OpAlias defs Delta Counter` → `OpAlias \defs \Delta Counter`
inside `\begin{zed}...\end{zed}`.

**See:** `examples/10_schemas/horizontal_defs.txt`

#### Schema Renaming (`S[old/new, ...]`)

Schema renaming produces a schema identical to an existing one except that
named components are given new names (Z RM §3.11).  Renaming is written on
the RHS of a `defs` paragraph:

```text
CounterN defs Counter[count/n]
Op2 defs Counter[count'/count]
SwappedPoint defs Point[x/y, y/x]
```

| Property | Value |
|---|---|
| Syntax | `SchemaName[oldName/newName, ...]` |
| Minimum pairs | 1 |
| Decoration on schema | `S'[a/b]` renames the primed schema `S'` |
| Decoration in pairs | `S[a'/b]` or `S[a/b']` supported |
| Disambiguation | Scan for `/` at depth 0 inside `[...]` |

**Disambiguation from generic instantiation** (`S[X]`, Phase 1.1): if any
`/` appears at bracket depth 0, the parser treats the bracket as rename
pairs; otherwise it treats the bracket as type parameters.

**Generated LaTeX:** `Counter[count/n]` renders as `Counter[count/n]` —
the brackets and slashes are literal math-mode text with no special macro.

**See:** `examples/10_schemas/schema_rename.txt`

#### Schema Calculus Operators (Z RM §3.11)

Schema-calculus operators combine, filter, and pipeline schemas.  They appear
only on the RHS of a `defs` paragraph.  The macros (`\semi`, `\pipe`, `\hide`,
`\project`) are defined in `fuzz.sty` and `zed-cm.sty`; no preamble change is
needed.

| Source notation      | LaTeX emitted         | Meaning                          |
|----------------------|-----------------------|----------------------------------|
| `S ; T`              | `S \semi T`           | Sequential composition           |
| `S >> T`             | `S \pipe T`           | Output-to-input piping           |
| `S hide (x, y)`      | `S \hide (x, y)`      | Existentially quantify components |
| `S project T`        | `S \project T`        | Project S onto T's signature     |

**Precedence (tightest to loosest):**

1. `hide` and `project`
2. `;` (composition)
3. `>>` (piping)

So `S hide (x) ; T >> U` parses as `((S hide (x)) ; T) >> U`.

```text
OpAB defs OpA ; OpB
// → \begin{zed} OpAB \defs OpA \semi OpB \end{zed}

Pipeline defs Send >> Receive
// → \begin{zed} Pipeline \defs Send \pipe Receive \end{zed}

Visible defs State hide (temp)
// → \begin{zed} Visible \defs State \hide (temp) \end{zed}

Projected defs State project View
// → \begin{zed} Projected \defs State \project View \end{zed}

Combined defs (OpA ; OpB) hide (x)
// → \begin{zed} Combined \defs OpA \semi OpB \hide (x) \end{zed}
```

**Context sensitivity:** `;` is a schema-composition operator only on the RHS
of a `defs` paragraph.  Inside `axdef`, `schema`, and `gendef` bodies, `;`
remains a declaration separator — this is unchanged.

**See:** `examples/15_schema_calculus/`

---

## Proof Trees

Natural deduction proofs using indentation-based syntax. For a
worked walkthrough, read
**[Tutorial 4: Proof Trees](../tutorials/04_proof_trees.md)** first.
The full specification is in
[PROOF_SYNTAX.md](PROOF_SYNTAX.md).

There are two related keywords:

- **`PROOF:`** — *applies* rules to build a derivation tree.  Use this
  when you want to show that a conclusion follows from premises by a
  sequence of natural-deduction steps.
- **`INFRULE:`** — *displays* a single inference rule schema as a
  horizontal premise/conclusion pair.  Use this when you want to
  exhibit the rule itself, not derive a result with it.

### `INFRULE:` — rule schema display

```text
INFRULE:
P
P => Q
---
Q [modus ponens]
```

Lines above the `---` separator are premises; the line below is the
conclusion; the bracketed text is an optional label.  The output is a
horizontal `\derive` rule.  See `examples/04_proof_trees/infrule_*.txt`
for working examples.

### Basic Structure

```text
PROOF:
conclusion [rule name]
  :: premise_1
  :: premise_2
```

The conclusion is written first; its premises are **indented children**.
Multi-premise rules (`land intro`, `=> elim`, `false-intro`, `<=> intro`,
`lor elim`) require `::` on each premise — without it, consecutive
indented lines collapse to a *linear chain* and the extra premises are
silently dropped from the rendered tree.

Unary rules (`land elim 1`, `lor intro 1`, `false elim`, single-premise
applications) take a single indented child with no `::` needed.

### Indentation Rules

- **2 spaces per level** for proof structure
- **Multi-premise rules:** every premise carries a `::` prefix
- **Unary rules:** single indented child, no `::`
- **Assumptions:** mark with `[N] X [assumption]` directly under the
  discharging rule
- **Discharge:** reference at any leaf with `Y [from N]`
- **Case analysis:** `case X:` blocks inside `lor elim from N`; the
  case formula is available as `X [from N]` within the block

### Justifications in Proof Trees

Justifications in proof trees are **free-form text** in square brackets. The system recognizes special patterns for structured rules:

#### Special Formatting Patterns

**Discharge notation** (for assumption elimination):

```text
[=> intro from 1]
[=> intro from 2]
[or elim from 2 and 3]
```

Formats as: $\Rightarrow$-intro$^{[1]}$ with superscript reference

**Projection notation** (for left/right selection):

```text
[and elim 1]
[and elim 2]
[or intro 1]
[or intro 2]
```

Formats as: $\land$-elim-1 with hyphenated subscript

**General rules:**

```text
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

- `o9` → $\semi$ (forward composition)
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
- `[definition of o9]` → [definition of $\semi$]
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

```text
PROOF:
p land q => p [=> intro from 1]
  [1] p land q [assumption]
  :: p [land elim 1]
    p land q [from 1]
```

### Example: Case Analysis

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

The `lor elim from 2` rule has three premises: the disjunction
(`p lor q [from 2]`) plus two `case` blocks. Inside each case, the
case formula is referenced with the discharge label of the enclosing
rule (`p [from 2]`, `q [from 2]`). The two `:: r [=> elim]` nodes are
binary, so each has `::` on its premises (the case formula plus the
relevant implication extracted from assumption [1]).

**Working notes on case analysis:**

- Inside a `case X:` block, the case formula `X` is available via
  `X [from N]` where `N` is the label discharged by the enclosing
  `lor elim from N` rule.
- Facts proven outside the case analysis remain available via their
  own `[from M]` references at any leaf where they're used.
- Each case derives the same conclusion through different reasoning
  paths.

---

## Relational Databases

Notation for relational database specifications.

For a worked normalisation walkthrough (functional dependencies, 1NF → 3NF
decomposition), see
`examples/14_relational_databases/normalisation.txt`.

### pk Declaration

Mark an attribute as a primary key with the `pk` prefix inside a **named**
schema body.  txt2tex renders `pk` fields with `\underline{field}` inside
the schema box:

```text
schema Book
  pk bookId : BookId
  isbn : ISBN
  pages : N
end
```

Generated LaTeX (abridged):

```latex
\begin{schemapk}{Book}
\underline{bookId} : BookId \\
isbn : ISBN \\
pages : \nat
\end{schemapk}
```

Fuzz type-checks the schema via a hidden plain copy (using
`\setbox0=\vbox{...}`).  The rendered copy uses the `schemapk`
environment, which fuzz ignores.

**Composite primary key** — two or more `pk` lines:

```text
schema CentreStaff
  pk centreId : CentreID
  pk staffId : PersonID
end
```

Each PK field is underlined independently:
`\underline{centreId}` and `\underline{staffId}`.

**Comma-separated pk names** (when names share a type):

```text
schema S
  pk a, b : T
end
```

**Scope**: `pk` is only valid in named schema bodies.  It raises
ParserError in axdef, gendef, anonymous schemas, and inline schema text.

**Error cases:**

```text
pk                   // no attribute name — parser error
pk noType            // missing colon — parser error
pk Delta S           // Delta is a schema inclusion, not an attribute — parser error
pk in axdef          // only schema bodies — parser error
```

### Relational Algebra (Phase 2.2)

The five Codd/Date operators.  All use kernel LaTeX (`\mathrm`,
`\div`) — no extra package needed.  The emission uses keyword style:
`Restrict`, `Project`, `Join`; renaming emits as literal `R[NEW/OLD]`
pass-through (Z RM §3.11).

**Fuzz compatibility.** Algebra expressions emit *outside* any Z
environment (as `\noindent$...$` LaTeX math). fuzz silently skips
them; schemas, axdefs, and other Z-side content in the same document
still type-check cleanly. Write algebra as a top-level expression in
your `.txt` source — never inside a `zed`/`axdef`/`schema`/`gendef`
block. Wrapping algebra inside a Z block causes fuzz to reject the
algebra keyword forms.

#### Restriction

```text
sigma[pages >= 200](Book)
```

Renders: $\mathrm{Restrict}_{pages \geq 200}(Book)$

The predicate inside `[...]` is a full expression (comparisons, logical
operators, etc.).

#### Projection

```text
pi[bookId, isbn](Book)
```

Renders: $\mathrm{Project}_{bookId, isbn}(Book)$

The attribute list is comma-separated identifiers.

#### Renaming

Z RM §3.11 postfix form: `R[NEW/OLD]`.  NEW is written first, OLD second.

```text
Book[id/bookId]
R[B/A, D/C]
```

Renders: $Book[id/bookId]$

The base may be any relation expression.  Compound bases are automatically
parenthesised:

```text
pi[tournament](sigma[venue = 'Wimbledon'](Match))[id/tournament]
```

Renders: $(\mathrm{Project}_{tournament}(\mathrm{Restrict}_{venue = `Wimbledon'}(Match)))[id/tournament]$

Multiple pairs are comma-separated; each pair writes NEW first then `/` then OLD:

```text
R[B/A, D/C]
```

**Context requirement.** The postfix `[NEW/OLD]` form is recognised only
inside a relational context — that is, as the argument to `sigma`, `pi`, or
the right operand of `join`/`div`.  At the top level of an abbreviation RHS,
wrap the rename inside a projection to force relational context:

```text
// Force relational context with pi (project all attributes):
B == pi[ship, class, launched](Ship[ship/name])
```

**Fuzz note.** `R[NEW/OLD]` on a relation is not valid inside Z paragraphs
(`zed`, `axdef`, `schema`).  The engine routes relational expressions through
inline math (`\noindent$...$`) automatically, so fuzz never sees the `/`.

The old `rho[A as B](R)` prefix keyword is retired.  `rho` now lexes as a
plain identifier.

#### Natural Join

```text
Track join Album
```

Renders: $\mathrm{Join}(Track, Album)$

The source keyword is `join`; the LaTeX emission is `\mathrm{Join}(R, S)`,
matching the instructor's canonical vocabulary (per slides/topic02.pdf §45).

**Theta-join** with explicit predicate:

```text
Track join [Track.albumId = Album.albumId] Album
```

Renders: $\mathrm{Join}_{Track.albumId = Album.albumId}(Track, Album)$

#### Division

```text
R div S
```

Renders: $R \div S$

#### Naming a query

Use `==` (Z abbreviation) to bind a name to an algebra expression.
txt2tex inspects the RHS: when it contains a relational construct (algebra,
binding, GROUP/UNGROUP), the abbreviation emits outside any Z block:

```text
LongBooks == pi[bookId, isbn](sigma[pages >= 200](Book))
```

Emits as `\noindent$LongBooks \defs \mathrm{Project}_{bookId, isbn}(\mathrm{Restrict}_{pages \geq 200}(Book))$`.

#### Combining Operators

```text
// long books projected to key and isbn
pi[bookId, isbn](sigma[pages >= 200](Book))

// rename then join (rename inside pi forces relational context)
pi[id, isbn, pages, year](Book[id/bookId]) join Loan

// name a query using ==
LongBooks == pi[bookId, isbn](sigma[pages >= 200](Book))
```

**Precedence summary** (tightest to loosest):

| Operator | Form | Level |
|----------|------|-------|
| `sigma`, `pi` | prefix-with-args | atom (tightest) |
| `R[NEW/OLD]` | postfix (inside relational context) | atom |
| `f(x)` | function application | atom |
| `intersect`, `setminus` (`\`) | infix | tighter than cross |
| `cross`, `join`, `div`, `group`, `ungroup` | infix | middle |
| `union`, `++` (override) | infix | loosest (of this group) |

### GROUP and UNGROUP (Phase 4.1)

Date's nested-relation operators.  Bundle attributes into a
relation-valued attribute (`group`) or flatten them back (`ungroup`).

**Fuzz compatibility.** GROUP/UNGROUP emit *outside* any Z
environment, so fuzz silently skips them. Use them as top-level
expressions in your source — not inside `zed`/`axdef`/`schema`
blocks. The `\mathop{\mathrm{GROUP}}` wrapping and Date-style braces
sit outside Z grammar; fuzz rejects them in Z-block contents.

#### GROUP — regroup form

```text
R group ({A, B, ...} as alias)
```

Renders: $R \mathop{\mathrm{GROUP}} (\{A, B\} \mathop{\mathrm{AS}} alias)$

The attribute list inside `{...}` is comma-separated.  The alias after
`as` names the resulting nested-relation column.

Example:

```text
GroupMembers group ({username} as members)
```

Renders: $GroupMembers \mathop{\mathrm{GROUP}} (\{username\} \mathop{\mathrm{AS}} members)$

#### GROUP — aggregate form

Computes scalar aggregates per partition.  The aggregator keywords are
`Count`, `Sum`, `Avg`, `Min`, `Max`, and `Median` — each takes a
single attribute name and an alias:

```text
R group (Count(attr) as alias)
R group (Sum(attr) as alias)
R group (Avg(attr) as alias)
R group (Min(attr) as alias)
R group (Max(attr) as alias)
R group (Median(attr) as alias)
```

Each renders as:

$$R~\mathrm{Group}(\mathrm{Aggregator}(attr)~\mathrm{as}~alias)$$

Concrete examples for each aggregator:

```text
Sales group (Count(orderId) as orderCount)
Sales group (Sum(amount) as totalRevenue)
Sales group (Avg(amount) as meanRevenue)
Sales group (Min(amount) as cheapest)
Sales group (Max(amount) as priciest)
Sales group (Median(amount) as midRevenue)
```

Multiple aggregators are comma-separated:

```text
R group (Count(x) as total, Sum(y) as grand)
```

Renders: $R~\mathrm{Group}(\mathrm{Count}(x)~\mathrm{as}~total,~\mathrm{Sum}(y)~\mathrm{as}~grand)$

**Constraints.**

- The aggregate form and the regroup form (`{...} as alias`) are
  mutually exclusive within a single `group` expression.  Mixing them
  is a parse error.
- Each aggregator accepts exactly one attribute identifier — no nested
  aggregators, no compound expressions.

#### UNGROUP

```text
R ungroup alias
```

Renders: $R \mathop{\mathrm{UNGROUP}} alias$

Inverse of GROUP — removes the nested-relation attribute and restores
the original flat columns.

#### Chaining

GROUP and UNGROUP are left-associative at the same precedence as
`join` and `div`:

```text
R group ({A} as sub) ungroup sub
```

### Z Binding Calculus (Phase 2.3)

Binding brackets construct labelled tuples per Z RM §3.7.  Used in
relational-calculus queries.

**Fuzz compatibility.** Bindings emit *outside* any Z environment, so
fuzz silently skips them. Write binding-bearing comprehensions as
top-level expressions — not inside `zed`/`axdef`/`schema` blocks.
fuzz parses Z-block contents strictly and rejects `==` inside
`\lblot ... \rblot` even though both the brackets and the operator
are defined in `fuzz.sty`.

**Syntax:**

```text
{| label == expression, ... |}
```

Components are **comma-separated** (not semicolons).

**Examples:**

```text
{| trackId == t.trackId |}

{| trackId == t.trackId, year == a.year, tracks == a.tracks |}

{| |}                         // empty binding (Z RM permits it)
```

**In set comprehensions:**

```text
{ t : Track | t.duration < 180 . {| trackId == t.trackId |} }

{ t : Track; a : Album | t.albumId = a.albumId .
  {| trackId == t.trackId, year == a.year |}
}
```

The `;` in `s : Ship; c : Class` separates variable-type pairs with
different domains (multi-typed comprehension).

**LaTeX output:**

- `{| a == 1 |}` → `\lblot a == 1 \rblot`
- `{| a == 1, b == 2 |}` → `\lblot a == 1, b == 2 \rblot`
- `{| |}` → `\lblot \rblot`

The macros `\lblot` and `\rblot` are defined in both `fuzz.sty` and the
`zed-*` family.  No preamble change is needed.

**Token disambiguation:**

- `{|` — Binding bracket left (LBIND)
- `|}` — Binding bracket right (RBIND)
- `{` — Set brace (LBRACE)
- `|` — Quantifier/comprehension pipe (PIPE)
- `(|` — Relational image left (LIMG)
- `|)` — Relational image right (RIMG)

## Additional Features

### Conditional Expressions

```text
if x > 0 then x else -x
if s = <> then 0 else head s
```

**Nested conditionals:**

```text
if x > 0 then 1 else if x < 0 then -1 else 0
```

**In function definitions:**

```text
abs(x) = if x > 0 then x else -x
max(x, y) = if x > y then x else y
```

### Subscripts and Superscripts

**Subscripts:**

```text
x_i              →  xᵢ          [subscript]
a_{n}            →  aₙ          [braces group multi-char subscripts]
```

**Superscripts (relation iteration only):**

```text
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

### Identifier Decoration

Z notation uses trailing decoration characters as part of the identifier lexeme.
This is the Z RM §3.3 convention for naming before-state, after-state, input,
and output variables.

| Decoration | Meaning | Example |
|---|---|---|
| `'` (prime) | After-state | `count'`, `s''` |
| `?` | Input variable | `in?`, `x?` |
| `!` | Output variable | `out!`, `y!` |

Decorations may appear in any order and can be combined:

```text
schema StateOp
  count, count' : N
  in? : N
  out! : N
where
  count' = count + in?
  out! = count
end
```

Multiple primes (`s''`) and mixed combinations (`x?'`) are all valid.
The decoration characters are part of the identifier name; there is no
space between the base name and its decoration.

**Contrast with contractions:** apostrophes in English prose (inside TEXT
blocks) are not treated as decoration. `don't` and `won't` pass through
unchanged.

### Multi-Word Identifiers

Underscores can be used for readable multi-word variable names:

```text
cumulative_total             →  cumulative_total
not_yet_viewed               →  not_yet_viewed
employee_count               →  employee_count
```

**Smart rendering:**

- Simple subscript: `a_i` → $a_i$
- Multi-char subscript: `x_max` → $x_{max}$
- Multi-word identifier: `cumulative_total` → $\mathit{cumulative\_total}$

### Comparison Operators

```text
x < y            →  x < y
x > y            →  x > y
x <= y           →  x ≤ y
x >= y           →  x ≥ y
```

### Arithmetic Operators

```text
x + y            →  x + y       [addition]
x - y            →  x - y       [subtraction]
-x               →  -x          [negation]
x * y            →  x × y       [multiplication]
x div n          →  x ÷ n       [integer division — same `div` keyword as relational div]
x mod n          →  x mod n     [modulo]
```

### Generic Type Instantiation

Apply type parameters to polymorphic types:

```text
emptyset[N]                  →  ∅[N]
seq[N]                       →  seq[N]
P[X]                         →  P[X]
Type[A, B]                   →  Type[A, B]
```

**Complex parameters:**

```text
emptyset[N cross N]          →  ∅[N × N]
seq[N cross N]               →  seq[N × N]
```

**Nested:**

```text
Type[List[N]]                →  Type[List[N]]
Container[seq[N]]            →  Container[seq[N]]
```

---

## Overflow Warnings

txt2tex automatically detects lines in Z notation blocks (axdef, schema, zed, gendef) that may overflow the page margin. These blocks use fuzz's internal `\halign` formatting which cannot be automatically scaled with `adjustbox`.

### Warning Output

When a line exceeds the threshold, you'll see a warning on stderr:

```text
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

```text
p land q => \
  r lor s
```

**After `then` and before `else` in conditionals:**

```text
if condition \
  then result1 \
  else result2
```

**After `=` in equations:**

```text
longFunctionName(x, y, z) = \
  complexExpression + moreTerms
```

**After `|` in quantifier bindings (single-decl and semicolon-chained):**

A natural newline or explicit `\` after the `|` separator in a quantifier
binding causes the body to be placed on the next line, indented with `\t1`
(the Spivey-canonical fuzz tab-stop).

Single-binding form:

```text
forall i : songs |
  loveHateScore(i) = someExpression
```

Semicolon-chained form — all four quantifier types (`forall`, `exists`,
`exists1`, `mu`) honour the break equally:

```text
forall s : Ship; o : Outcome; b : Battle |
  (o.ship = s.name land o.battle = b.name) =>
  (s.launched <= b.date)
```

Both forms emit `@ \\` followed by a newline and `\t1` indentation:

```latex
\forall s : Ship; o : Outcome; b : Battle @ \\
\t1 (o.ship = s.name \land o.battle = b.name) \implies ...
```

The bullet (`.`) separator in constraint-plus-body quantifiers also supports
the same break:

```text
forall x : N; y : N | x > 0 .
  x < y
```

#### Algebra and Set Operators

The following operators also support WYSIWYG line breaks — both a natural
newline after the operator and an explicit `\` continuation:

| Keyword | LaTeX | Notes |
|---------|-------|-------|
| `join` | `\mathrm{Join}(R, S)` | natural join / theta-join |
| `cross` | `\times` | Cartesian product |
| `div` | `\div` | relational division |
| `intersect` | `\cap` | set intersection |
| `union` | `\cup` | set union |
| `setminus` | `\setminus` | set difference — see caveat |
| `++` | `\oplus` | override |
| `group` | `\mathop{\mathrm{GROUP}}` | Date nested-relation operator |
| `ungroup` | `\mathop{\mathrm{UNGROUP}}` | Date nested-relation operator |
| `Count`, `Sum`, `Avg`, `Min`, `Max`, `Median` | `\mathrm{Count}(attr)~\mathrm{as}~alias` | Aggregators inside `group` RHS |

**Display position** (free-standing expression): the broken chain wraps in
`\begin{array}{l}...\end{array}` with `\\` between continuations.

**Inside a `where` predicate** (`schema`, `axdef`, `zed`): `\\` is emitted
inline with no array wrapper — the same form fuzz type-checks for `land`
and `lor`.

Example — long algebra expression broken at operator boundaries:

```text
pi[winner, venue, tier](Tournament join
  Match join
  (pi[tournament](sigma[venue = 'Centre Court'](Match)))[id/tournament])
```

Example — inside a schema `where` clause:

```text
schema S
  x, y, z : P A
where
  x = y union
    z intersect A
end
```

**`setminus` caveat.** The `setminus` token is the character `\`. The lexer
reads `\` at end of line as a continuation marker, and `\` followed by any
non-newline character as `setminus`. You cannot place a continuation
immediately after `setminus`. Break *before* `setminus` instead:

```text
-- OK: break before setminus
A setminus B setminus \
  C
-- NOT OK: continuation immediately after setminus is a lex error
A \        -- this is "A setminus (next line)" -- wrong
  B
```

### Fixing Overflow

To fix overflowing lines, use `\` to break at logical points:

**Before (overflows):**

```text
axdef
  f : SongId +-> N
where
  forall i : songs | f(i) = if (# {u : UserId | i elem loved(u)}) >= (# {u : UserId | i elem hated(u)}) then (# {u : UserId | i elem loved(u)}) - (# {u : UserId | i elem hated(u)}) else 0
end
```

**After (fits page):**

```text
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
- `ARGUE:`, `EQUIV:`, and `EQUAL:` blocks
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
- **[Feature Gaps](MISSING_FEATURES.md)** - Known limitations and workarounds

### Development Resources

- **[Missing Features](MISSING_FEATURES.md)** - Features not yet implemented
- **[IDE Setup](../development/IDE_SETUP.md)** - VSCode/Cursor configuration
