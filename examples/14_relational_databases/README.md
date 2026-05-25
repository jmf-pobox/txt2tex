# Relational Databases Examples

Examples demonstrating relational-database schema notation.

## The PK Convention

The `pk` prefix marks primary-key attributes. A PK annotation is emitted
below the schema box. The `pk` prefix produces this:

```text
schema Book
  pk bookId : BookId
  isbn : ISBN
  pages : N
  year : N
end
```

The generator emits a `PK(Book) = {bookId}` annotation below the schema box.
`isbn`, `pages`, and `year` are plain declarations — no annotation. Schema names
stay in their default math font — no `\mathrm{}` wrapper.

## Examples

### primary_keys.txt

Demonstrates the `pk` prefix for marking primary-key attributes using a
library domain (Book, Member, Loan):

- Single primary key: `pk bookId : BookId`
- Composite primary key: two `pk` lines in one schema
- PK/FK constraints as plain Z predicates in `axdef`

### algebra_basics.txt

Demonstrates the relational algebra operators added in Phase 2.2:

- `sigma[pred](R)` — restriction (`\mathrm{Restrict}_{pred}(R)`)
- `pi[A, B](R)` — projection (`\mathrm{Project}_{A, B}(R)`)
- `R[new/old]` — renaming (`R[new/old]` literal pass-through; Z RM §3.11)
- `R join S` — natural join (`\mathrm{Join}(R, S)`)
- `R join [pred] S` — theta-join (`\mathrm{Join}_{pred}(R, S)`, function form)
- `R div S` — division (`R \div S`)

All operators use kernel LaTeX (no extra preamble packages required).

### group_ungroup.txt

Demonstrates Date's GROUP and UNGROUP operators for nested relations (Phase 4.1):

- `R group ({A, B} as alias)` — bundle attributes into a nested relation
- `R ungroup alias` — flatten a nested-relation attribute

LaTeX output uses `\mathop{\mathrm{GROUP}}` and `\mathop{\mathrm{UNGROUP}}`
for proper math-mode operator spacing (per jms round-2 refinement).

### bindings.txt

Demonstrates Z binding brackets per Z RM §3.7, used in relational-calculus
queries, with a music collection domain (Track, Album, Artist):

- `{| trackId == t.trackId |}` — single-component binding (`\lblot ... \rblot`)
- `{| a == e1, b == e2 |}` — multi-component binding with comma separators
- `{ t : Track | pred . {| trackId == t.trackId |} }` — binding in set comprehension
- `{ t : Track; a : Album | pred . {| ... |} }` — multi-variable comprehension
- `{| |}` — empty binding (Z RM permits it)

The `{|` and `|}` tokens are distinct from `{` (set brace), `|` (pipe),
`(|` (relational-image left), and `|)` (relational-image right).

### relational_calculus.txt

Demonstrates the Phase 3.2 multi-typed set-comprehension parser and generator
on a music streaming library domain (`Track`, `Artist`, `Album`, `Playlist`).

Six worked queries, each with a prose description and Z form:

1. **Single-relation selection** — `{ t : Track | t.genre = 'Jazz' . {| ... |} }`.
   Plain filter over one schema type.
2. **Two-relation join** — `{ t : Track; al : Album; ar : Artist | t.alid = al.alid land al.arid = ar.arid . {| ... |} }`.
   Three-variable comprehension joining three schema types on shared keys.
3. **Three-relation chain with playlist** — joins `PlaylistId <-> TrackId` with
   `Track` and `Album` in one comprehension.
4. **Binding output, duration filter** — characteristic expression is a
   two-component `{| ... |}` binding with no plain variable in the output.
5. **Multi-decl `forall`** — `forall p : PlaylistId; t : Track | ... . ...`
   asserts playlist membership implies album membership.
6. **No characteristic expression** — `{ t : Track; al : Album | ... }` with
   the dot-separator omitted; Z RM §3.9 signature default. Exercises the
   Q2(d) parser fix directly.

Exercises: multi-typed comprehension with conjunction predicates, Spivey-form
multi-decl syntax (`;`-separated declarations), bullet-vs-projection
disambiguation, and `{| name == e |}` bindings as characteristic expressions.
Fuzz type-checks clean.

### foreign_keys.txt

Demonstrates the full PK + FK pattern using a kitchen-management toy domain
(Recipe, Ingredient, RecipeIngredient, Employee).  Four worked patterns:

1. **Single-attribute PK** — `pk recipeId : RecipeId` underlines the attribute
   and auto-emits `PK(Recipe) = {recipeId}`.

2. **Composite PK** — two `pk` lines in one schema; txt2tex collapses them into
   `PK(RecipeIngredient) = {recipeId, ingredientId}`.

3. **Single-attribute FK** — a foreign key is a Z predicate, not a keyword.
   Two natural forms:
   - `forall ri : RecipeIngredient | exists r : Recipe | ri.recipeId = r.recipeId`
   - `pi[recipeId](RecipeIngredient) subset pi[recipeId](Recipe)`

   Both say the same thing: every value of the referencing attribute must
   appear in the referenced relation.  No special syntax or axdef
   declaration is needed — the constraint is a standard Z predicate using
   constructs the engine already supports.

4. **Composite FK + self-referential FK** — both FK predicates for
   RecipeIngredient stated as separate `forall`/`exists` predicates,
   plus a self-referential constraint on Employee:
   `forall e : Employee | exists m : Employee | e.managerId = m.employeeId`.

Fuzz type-checks the entire document cleanly.
Also exercises: `LINEBREAK:` between sections.

### normalisation.txt

Demonstrates functional dependencies and step-by-step normalisation on a
generic employee/project/department domain (#84):

- Universal relation with composite PK `(empID, projID)`
- Full FD set: partial dependencies on `empID` and `projID` alone; transitive
  dependency `dept -> deptHead`
- 2NF analysis: removes partial dependencies; identifies the remaining
  transitive violation
- 3NF decomposition into four relations: `Employee`, `Department`, `Project`,
  `Assignment` — no partial or transitive dependencies remain
- Lossless-join property stated in closing TEXT block

Fuzz type-checks clean against all four final schemas.

## Building

```bash
txt2tex examples/14_relational_databases/primary_keys.txt
txt2tex examples/14_relational_databases/algebra_basics.txt
txt2tex examples/14_relational_databases/bindings.txt
txt2tex examples/14_relational_databases/group_ungroup.txt
txt2tex examples/14_relational_databases/relational_calculus.txt
txt2tex examples/14_relational_databases/foreign_keys.txt
txt2tex examples/14_relational_databases/normalisation.txt
```
