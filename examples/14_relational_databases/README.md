# Relational Databases Examples

Examples demonstrating the `relvars` declaration paragraph for DAT
(Database Design) course support.

## The DAT Convention

The Oxford DAT course uses two typography conventions for relation schemas:

- **Relation names** (Class, Ship, Battle, Outcome) render **upright**:
  `\mathrm{Class}`
- **Attribute names** (class, name, bore, country) render **italic** (default
  math mode)

The `relvars` paragraph declares which identifiers are relation variables.
Everything else stays italic.

## Examples

### relvars_basic.txt

Declares four relation variables from the classic warships database and
defines their schemas. Shows the upright/italic distinction:

```text
relvars Class, Ship, Battle, Outcome

schema Class
  class : N
  country : N
  bore : N
end
```

In the compiled PDF:

- `Class` (relation name) → upright roman
- `class` (attribute name) → italic
- `N` (type) → `\nat` or `\mathbb{N}`

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

## Building

```bash
txt2tex examples/14_relational_databases/relvars_basic.txt
txt2tex examples/14_relational_databases/algebra_basics.txt
```
