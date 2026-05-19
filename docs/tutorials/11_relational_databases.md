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
