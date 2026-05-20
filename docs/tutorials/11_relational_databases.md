# Tutorial 11: Relational Databases

**Level 2** — Requires familiarity with Z schemas (Tutorial 9).

## Primary Keys

The `pk` prefix marks an attribute as the primary key of a **named** schema.
txt2tex records this in the AST and emits a PK statement after the schema box:

```text
schema Book
  pk bookId : BookId
  isbn : ISBN
  pages : N
  year : N
end
```

Generated LaTeX (abridged):

```latex
\begin{schema}{Book}
bookId : BookId \\
isbn : ISBN \\
...
\end{schema}
\noindent$\mathrm{PK}(\mathrm{Book}) = \{bookId\}$
```

The schema body is plain Z — fuzz type-checks it cleanly. The PK line sits
outside any Z environment, so fuzz ignores it; pdflatex renders it in upright
math as a visible annotation below the schema box.

**Why not underline inside the schema box?** fuzz rejects any LaTeX macro
with a brace argument (such as `\underline{class}`) in the variable-name
position of a schema declaration. The PK line is the fuzz-compatible
alternative.

### Composite Primary Keys

Two `pk` lines list both attributes in the PK set:

```text
schema CentreStaff
  pk centreId : CentreID
  pk staffId : PersonID
end
```

Generated:

```latex
\noindent$\mathrm{PK}(\mathrm{CentreStaff}) = \{centreId, staffId\}$
```

### Comma-Separated pk Names

A single `pk` line may declare multiple names sharing one type:

```text
schema S
  pk a, b : T
end
```

Both `a` and `b` are included in the PK set.

### Scope: Named Schemas Only

`pk` is valid **only** inside named schema bodies. It is rejected elsewhere:

| Context | Result |
|---------|--------|
| `schema Name ... end` | accepted — named schema |
| `schema ... end` | ParserError — anonymous schema has no relation name |
| `axdef ... end` | ParserError — primary key is a relational concept |
| `gendef [X] ... end` | ParserError — primary key is a relational concept |
| `S defs [ pk a : T ]` | ParserError — inline schema text is anonymous |

### Syntax Rules

- `pk` must be followed by at least one attribute name and a colon
- `pk Delta S` and `pk Xi S` are rejected — Delta and Xi introduce
  schema inclusions, not attribute names
- `pk` is a reserved keyword and cannot be used as an identifier
- Decorated names are valid: `pk count' : N`

**Invalid examples that raise parser errors:**

```text
pk               // no attribute name — error
pk noType        // missing colon — error
pk Delta S       // Delta inclusion after pk — error
pk in axdef      // only schema bodies — error
```

### Complete Primary Keys Example

See `examples/14_relational_databases/primary_keys.txt`.

```bash
txt2tex examples/14_relational_databases/primary_keys.txt
```

---

## Relational Algebra

Phase 2.2 adds the five core Codd/Date relational algebra operators, plus
an assignment statement. All operators use kernel LaTeX — no extra package
required.

> **Fuzz compatibility.** Algebra expressions emit *outside* any Z
> environment — as `\noindent$\ldots$` LaTeX math — so fuzz silently
> skips them. Your schemas, axdefs, and other Z-side content in the
> same document still type-check cleanly. The rule is: write algebra
> as a top-level expression in your source (not inside a `zed`,
> `axdef`, `schema`, or `gendef` block). If you wrap algebra inside a
> Z block, fuzz parses the block contents strictly as Z notation and
> will reject the algebra keyword form.

### Restriction (sigma)

Select tuples satisfying a predicate:

```text
sigma[pages >= 200](Book)
```

Renders as: $\mathrm{Restrict}_{pages \geq 200}(Book)$

### Projection (pi)

Keep only named attributes:

```text
pi[bookId, isbn](Book)
```

Renders as: $\mathrm{Project}\{bookId, isbn\}(Book)$

The attribute list is comma-separated identifiers.

### Renaming (rho)

Rename attributes using `old as new` pairs:

```text
rho[bookId as id](Book)
rho[A as B, C as D](R)
```

Renders as: $\mathrm{Rename}_{bookId \to id}(Book)$

Multiple pairs are comma-separated.

### Natural Join (bowtie)

Join on all common attributes:

```text
Track bowtie Album
```

Renders as: $Track \otimes Album$

The source keyword is `bowtie`; the LaTeX emission is `\otimes` (`⊗`).

**Theta-join** — join with an explicit predicate:

```text
Track bowtie [Track.albumId = Album.albumId] Album
```

Renders as: $\mathrm{Join}_{Track.albumId = Album.albumId}(Track, Album)$

### Division (div)

Relational division:

```text
R div S
```

Renders as: $R \div S$

### Naming a query

Use `==` (Z abbreviation) to bind a name to an algebra expression.
txt2tex inspects the RHS: when it contains a relational construct (algebra,
binding, GROUP/UNGROUP), the abbreviation emits as `\noindent$...$` outside any Z block:

```text
LongBooks == pi[bookId, isbn](sigma[pages >= 200](Book))
```

Emits as:

```latex
\noindent$LongBooks \defs \mathrm{Project}\{bookId, isbn\}(\mathrm{Restrict}_{pages \geq 200}(Book))$
```

### Operator Precedence

Algebra prefix operators (`sigma`, `pi`, `rho`) bind at atom level — they
are parsed as prefix-with-arguments, like function calls. `bowtie` and
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
These appear in relational-calculus queries.

> **Fuzz compatibility.** Bindings emit *outside* any Z environment —
> as `\noindent$\ldots$` LaTeX math — so fuzz silently skips them.
> Schemas and axdefs in the same document still type-check cleanly.
> The rule is: write the binding-bearing comprehension as a top-level
> expression in your source (not inside a `zed`/`axdef`/`schema`
> block). If you wrap a binding inside a Z block, fuzz parses the
> contents strictly and rejects `==` inside `\lblot ... \rblot` even
> though both the brackets and the operator are defined in
> `fuzz.sty`.

### Binding Syntax

A binding constructs a tuple whose components are labelled:

```text
{| trackId == t.trackId |}
```

Renders as: $\lblot trackId == t.trackId \rblot$

Multiple components are **comma-separated** (not semicolons — Z RM §3.7):

```text
{| trackId == t.trackId, year == a.year, tracks == a.tracks |}
```

Renders as:
$\lblot trackId == t.trackId, year == a.year, tracks == a.tracks \rblot$

An empty binding is valid (rare, but permitted by Z RM §3.7):

```text
{| |}
```

### Binding in Set Comprehension

The main use case is the expression part of a set comprehension:

```text
{ t : Track | t.duration < 180 . {| trackId == t.trackId |} }
```

A multi-variable comprehension uses `;` to separate variable-type pairs:

```text
{ t : Track; a : Album | t.albumId = a.albumId .
  {| trackId == t.trackId, year == a.year, tracks == a.tracks |}
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

The `==` inside `{| ... |}` reuses the ABBREV token. The parser
disambiguates by position: inside binding brackets, `==` is the
label-equals operator; at top-level, it is an abbreviation definition.

### LaTeX Macros

The macros `\lblot` and `\rblot` are defined in both `fuzz.sty` (lines
275-276) and `zed-lbr.sty`/`zed-cm.sty`. No preamble change is needed.

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
GroupMembers group ({name, email} as contact)
```

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

GROUP and UNGROUP are left-associative at the same precedence as `bowtie` (`\otimes`)
and `div`. Chaining is valid:

```text
R group ({A, B} as sub) ungroup sub
```

### Complete Example

See `examples/14_relational_databases/group_ungroup.txt`:

```bash
txt2tex examples/14_relational_databases/group_ungroup.txt
```
