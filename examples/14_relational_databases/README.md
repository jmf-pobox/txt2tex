# Relational Databases Examples

Examples demonstrating relational-database schema notation for DAT
(Database Design) course support.

## The DAT Convention

The Oxford DAT course marks primary keys by underlining the attribute name
in the schema body. The `pk` prefix produces this:

```text
schema Class
  pk class : ClassName
  country : CountryName
  bore : N
end
```

The rendered PDF shows `class` underlined; `country` and `bore` are plain
italic. Schema names stay in their default math font — no `\mathrm{}` wrapper.

## Examples

### primary_keys.txt

Demonstrates the `pk` prefix for marking primary-key attributes:

- Single primary key: `pk class : ClassName`
- Composite primary key: two `pk` lines in one schema
- PK/FK constraints as plain Z predicates in `axdef`

### algebra_basics.txt

Demonstrates the relational algebra operators added in Phase 2.2:

- `sigma[pred](R)` — restriction (`\sigma`)
- `pi[A, B](R)` — projection (`\pi`)
- `rho[A as B](R)` — renaming (`\rho`)
- `R bowtie S` — natural join (`\bowtie`)
- `R bowtie [pred] S` — theta-join (`\bowtie_{pred}`)
- `R div S` — division (`\div`)
- `T := R` — assignment

All operators use kernel LaTeX (no extra preamble packages required).

### group_ungroup.txt

Demonstrates Date's GROUP and UNGROUP operators for nested relations (Phase 4.1):

- `R group ({A, B} as alias)` — bundle attributes into a nested relation
- `R ungroup alias` — flatten a nested-relation attribute

LaTeX output uses `\mathop{\mathrm{GROUP}}` and `\mathop{\mathrm{UNGROUP}}`
for proper math-mode operator spacing (per jms round-2 refinement).

### bindings.txt

Demonstrates Z binding brackets per Z RM §3.7, used in relational-calculus
queries (DAT course style):

- `{| name == s.name |}` — single-component binding (`\lblot ... \rblot`)
- `{| a == e1, b == e2 |}` — multi-component binding with comma separators
- `{ s : Ship | pred . {| name == s.name |} }` — binding in set comprehension
- `{ s : Ship; c : Class | pred . {| ... |} }` — multi-variable comprehension
- `{| |}` — empty binding (Z RM permits it)

The `{|` and `|}` tokens are distinct from `{` (set brace), `|` (pipe),
`(|` (relational-image left), and `|)` (relational-image right).

## Building

```bash
txt2tex examples/14_relational_databases/primary_keys.txt
txt2tex examples/14_relational_databases/algebra_basics.txt
txt2tex examples/14_relational_databases/bindings.txt
txt2tex examples/14_relational_databases/group_ungroup.txt
```
