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
