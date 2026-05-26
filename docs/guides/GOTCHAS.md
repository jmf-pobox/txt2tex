# Gotchas

Known rough edges and workarounds.  Each entry describes a
situation where txt2tex behaves in a way that is correct but
surprising, or where the interaction between fuzz type-checking
and txt2tex's relational-algebra extensions creates a gap.

---

## 1. Abbreviation chains that mix algebra and pure Z

**Symptom.** Fuzz rejects an abbreviation whose right-hand side is
pure Z (`union`, `intersect`, `subset`, plain identifiers) but
whose operands were defined in earlier abbreviations that used
relational-algebra operators (`pi`, `sigma`, `join`, etc.).

```text
A == pi[x](sigma[p](R))
B == pi[x](sigma[q](R))
C == A intersect B
```

`A` and `B` route to inline math (`$A == ...$`) because their
RHS contains DAT constructs.  `C` looks like ordinary Z —
two identifiers joined by `\cap` — so the engine puts it
inside `\begin{zed}...\end{zed}`.  Fuzz then rejects `A` and
`B` as undeclared because their definitions were never visible
inside a Z environment.

**Workaround.** Write the final step as a standalone expression
(not an abbreviation):

```text
A == pi[x](sigma[p](R))
B == pi[x](sigma[q](R))

pi[x](sigma[p](R)) intersect pi[x](sigma[q](R))
```

The standalone expression routes to inline math and fuzz skips
it.  The `.tex` and PDF render correctly in both cases; the
difference is only whether fuzz complains.

---

## 2. Reserved single-letter identifiers

**Symptom.** Using `F`, `P`, `N`, or `Z` as an abbreviation name
or variable name causes a parse error or unexpected rendering.

```text
F == A union B
```

`F` is the `\finset` (finite set) operator keyword.  `P` is
`\power` (power set).  `N` is `\nat` (natural numbers).  `Z` is
`\arithmos` (integers).  The lexer consumes these before the
parser sees them.

**Workaround.** Use multi-character names: `FC`, `PS`, `Nums`,
etc.

---

## 3. Fuzz does not understand relational algebra

**Symptom.** Fuzz type-checking fails on expressions containing
`pi`, `sigma`, `join`, `div`, `group`, or `ungroup` when those
expressions appear inside a Z environment (`\begin{zed}`,
`\begin{axdef}`, `\begin{schema}`).

These operators are txt2tex extensions that emit as
`\mathrm{Project}`, `\mathrm{Restrict}`, `\mathrm{Join}`, etc.
Fuzz has no rules for them.

**How the engine handles this.** Abbreviations whose RHS contains
a DAT construct are automatically routed to `\noindent$...$`
(inline math) instead of `\begin{zed}...\end{zed}`.  Fuzz
silently skips inline math.  Standalone expressions (not
abbreviations) also route to inline math.  The `.tex` and PDF
are always correct; the limitation is only on what fuzz can
verify.

**See also.** Gotcha #1 for the edge case where this routing
logic is fooled by a pure-Z expression that references
algebra-defined names.
