# Tutorial 11: Relational Databases

**Level 2** — Requires familiarity with Z schemas (Tutorial 9).

## Relation Variables and Attribute Typography

The Oxford DAT (Database Design) course uses a two-tier naming convention for
relation schemas:

- **Relation names** (Class, Ship, Battle, Outcome) are written in upright
  roman type: $\mathrm{Class}$, $\mathrm{Ship}$
- **Attribute names** (class, name, bore, country) stay in default italic type:
  $class$, $name$

This matches the `\relvar` / `\attr` macros from the course LaTeX template:

```latex
\newcommand{\relvar}[1]{\mathrm{#1}}
\newcommand{\attr}[1]{\mathit{#1}}
```

txt2tex implements this via the `relvars` declaration paragraph.

## The relvars Paragraph

Declare relation variables with `relvars` followed by a comma-separated list
of names:

```text
relvars Class, Ship, Battle, Outcome
```

The declaration is **document-global**: once declared, every occurrence of
`Class`, `Ship`, `Battle`, or `Outcome` as an identifier in a math context
renders as `\mathrm{Class}`, `\mathrm{Ship}`, etc.

Attributes (`class`, `name`, `bore`) do not need any special marker — they
stay italic by default.

## Example: Warships Database

```text
relvars Class, Ship, Battle, Outcome

schema Class
  class : N
  country : N
  bore : N
  displacement : N
  launched : N
end

schema Ship
  name : N
  class : N
  launched : N
end
```

In the compiled PDF:

- The schema header `Class` is upright: `\begin{schema}{\mathrm{Class}}`
- The declaration `class : N` uses italic `class` (attribute name)
- The declaration `class : Class` (Ship schema) has italic `class` on the left
  and upright `\mathrm{Class}` on the right

## Decoration and Subscripts

Decoration characters (`'`, `?`, `!`) and subscripts interact cleanly with
relvars. The decoration appears **outside** `\mathrm{}`:

| txt2tex source | LaTeX output        |
|----------------|---------------------|
| `Class`        | `\mathrm{Class}`    |
| `Class'`       | `\mathrm{Class}'`   |
| `Class?`       | `\mathrm{Class}?`   |
| `Class_1`      | `\mathrm{Class}_1`  |
| `Class_12`     | `\mathrm{Class}_{12}` |

## Multiple relvars Paragraphs

You can split declarations across multiple paragraphs — they combine into
one relvar set:

```text
relvars Class, Ship
relvars Battle, Outcome
```

## Syntax Rules

- Names must be plain identifiers (no decoration, no generic parameters)
- At least one name is required
- Commas are mandatory between names; trailing commas are not allowed
- `relvars` is a reserved keyword and cannot be used as an identifier

**Invalid examples that raise parser errors:**

```text
relvars              // no names — error
relvars Class,       // trailing comma — error
relvars Class, ,Ship // double comma — error
relvars Class Ship   // missing comma — error
```

## Complete Example

See `examples/14_relational_databases/relvars_basic.txt` for a full working
example with four relation variables and their schemas.

Build it:

```bash
txt2tex examples/14_relational_databases/relvars_basic.txt
```

---

## Relational Algebra

Phase 2.2 adds the five core Codd/Date relational algebra operators, plus
an assignment statement.  All operators use kernel LaTeX — no extra package
required.

### Restriction (sigma)

Select tuples satisfying a predicate:

```text
sigma[bore >= 16](Class)
```

Renders as: $\sigma_{bore \geq 16}(\mathrm{Class})$

### Projection (pi)

Keep only named attributes:

```text
pi[class, country](Class)
```

Renders as: $\pi_{class, country}(\mathrm{Class})$

The attribute list is comma-separated identifiers.  Relation names in the
list receive `\mathrm{}` wrapping if declared with `relvars`; attribute
names (lowercase, not declared) stay italic.

### Renaming (rho)

Rename attributes using `old as new` pairs:

```text
rho[ship as name](Outcome)
rho[A as B, C as D](R)
```

Renders as: $\rho_{ship \to name}(\mathrm{Outcome})$

Multiple pairs are comma-separated.

### Natural Join (bowtie)

Join on all common attributes:

```text
Ship bowtie Class
```

Renders as: $\mathrm{Ship} \bowtie \mathrm{Class}$

**Theta-join** — join with an explicit predicate:

```text
Ship bowtie [Ship.class = Class.class] Class
```

Renders as: $\mathrm{Ship} \bowtie_{Ship.class = Class.class} \mathrm{Class}$

### Division (div)

Relational division:

```text
R div S
```

Renders as: $R \div S$

### Assignment (:=)

Bind a name to an algebra expression.  This is a top-level statement (not
nested inside another expression):

```text
BigGuns := pi[class, country](sigma[bore >= 16](Class))
```

The assignment emits a `\begin{zed}...\end{zed}` block:

```latex
\begin{zed}
BigGuns := \pi_{class, country}(\sigma_{bore \geq 16}(\mathrm{Class}))
\end{zed}
```

### Operator Precedence

Algebra prefix operators (`sigma`, `pi`, `rho`) bind at atom level — they
are parsed as prefix-with-arguments, like function calls.  `bowtie` and
`div` are infix and sit at the same precedence as `cross` (Cartesian
product), above union/intersect.

```text
pi[a](R union S)          // pi wraps (R union S) — correct
pi[a](R) bowtie pi[b](S)  // join of two projected relations
```

### Complete Algebra Example

See `examples/14_relational_databases/algebra_basics.txt` for a working
file demonstrating all operators.

```bash
txt2tex examples/14_relational_databases/algebra_basics.txt
```

---

## Z Binding Calculus

Phase 2.3 adds binding brackets — the Z RM §3.7 notation for labelled tuples.
These appear in relational-calculus queries of the form used in the Oxford DAT
course exercises.

### Binding Syntax

A binding constructs a tuple whose components are labelled:

```text
{| name == s.name |}
```

Renders as: $\lblot name == s.name \rblot$

Multiple components are **comma-separated** (not semicolons — Z RM §3.7):

```text
{| name == s.name, displacement == c.displacement, numGuns == c.numGuns |}
```

Renders as:
$\lblot name == s.name, displacement == c.displacement, numGuns == c.numGuns \rblot$

An empty binding is valid (rare, but permitted by Z RM §3.7):

```text
{| |}
```

### Binding in Set Comprehension (DAT Q2 style)

The main use case is the expression part of a set comprehension:

```text
{ s : Ship | s.launched < 1921 . {| name == s.name |} }
```

This renders as a Z set comprehension with a binding body.  The relation
variable `Ship` receives `\mathrm{}` wrapping when declared with `relvars`.

A multi-variable comprehension uses `;` to separate variable-type pairs:

```text
{ s : Ship; c : Class | s.class = c.class .
  {| name == s.name, displacement == c.displacement, numGuns == c.numGuns |}
}
```

### Token Disambiguation

The two-character tokens `{|` (LBIND) and `|}` (RBIND) are distinct from
all existing tokens:

- `{` (LBRACE) — Set brace / subscript group
- `{|` (LBIND) — Binding bracket left
- `|` (PIPE) — Quantifier separator
- `|}` (RBIND) — Binding bracket right
- `(|` (LIMG) — Relational image left
- `|)` (RIMG) — Relational image right

The `==` inside `{| ... |}` reuses the ABBREV token.  The parser
disambiguates by position: inside binding brackets, `==` is the
label-equals operator; at top-level, it is an abbreviation definition.

### LaTeX Macros

The macros `\lblot` and `\rblot` are defined in both `fuzz.sty` (lines
275-276) and `zed-lbr.sty`/`zed-cm.sty`.  No preamble change is needed.

### Complete Bindings Example

See `examples/14_relational_databases/bindings.txt` for a working file
demonstrating all binding forms.

```bash
txt2tex examples/14_relational_databases/bindings.txt
```

## GROUP and UNGROUP

Date's GROUP and UNGROUP operators model nested relations — relation-valued
attributes where one attribute column contains a whole sub-relation.

### GROUP

Bundle a set of attributes into a single nested relation-valued attribute:

```text
R group ({A, B, ...} as alias)
```

LaTeX output:

```latex
R \mathop{\mathrm{GROUP}} (\{A, B\} \mathop{\mathrm{AS}} alias)
```

The `\mathop{}` wrapper gives proper binary-operator spacing in math mode.
No `.sty` changes are needed: `\mathrm` and `\mathop` are LaTeX kernel.

Example — bundle name and email into a contact nested relation:

```text
relvars GroupMembers

GroupMembers group ({name, email} as contact)
```

Renders as:

```latex
\mathrm{GroupMembers} \mathop{\mathrm{GROUP}}
  (\{name, email\} \mathop{\mathrm{AS}} contact)
```

Relation names declared with `relvars` receive `\mathrm{}` wrapping;
attribute names and aliases stay italic (default math mode).

### UNGROUP

Flatten a nested relation-valued attribute back to ordinary columns:

```text
R ungroup alias
```

LaTeX output:

```latex
R \mathop{\mathrm{UNGROUP}} alias
```

Example — recover the flat structure from a grouped relation:

```text
GroupMembers ungroup contact
```

### Chaining

GROUP and UNGROUP are left-associative at the same precedence as `bowtie`
and `div`.  Chaining is valid:

```text
R group ({A, B} as sub) ungroup sub
```

### Complete Example

See `examples/14_relational_databases/group_ungroup.txt`:

```bash
txt2tex examples/14_relational_databases/group_ungroup.txt
```
