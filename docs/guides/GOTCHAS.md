# Gotchas

Known rough edges and workarounds.  Each entry describes a
situation where txt2tex behaves in a way that is correct but
surprising, or where the interaction between fuzz type-checking
and txt2tex's relational-algebra extensions creates a gap.

---

## 1. ~~Abbreviation chains that mix algebra and pure Z~~ (RESOLVED)

An abbreviation whose right-hand side is pure Z (`union`, `intersect`,
plain identifiers) but whose operands were defined by earlier
relational-algebra abbreviations used to fail fuzz, because the
operands were never declared inside a Z environment.

The engine now routes by reference.  A Z operator that mentions an
algebra-defined name is rendered as inline math too, so no
workaround is needed.  This input type-checks:

```text
A == pi[x](sigma[p](R))
B == pi[x](sigma[q](R))
C == A intersect B
```

`txt2tex --tex-only` emits all three as inline math and fuzz reports no
error:

```latex
\noindent
$A == \mathrm{Project}_{x}(\mathrm{Restrict}_{p}(R))$

\noindent
$B == \mathrm{Project}_{x}(\mathrm{Restrict}_{q}(R))$

\noindent
$C == A \cap B$
```

---

## 2. ~~Reserved single-letter identifiers~~ (PARTIALLY RESOLVED)

`F` and `P` are reserved keywords (`\finset` and `\power`).
Previously, `F == expr` failed because the parser treated `F` as a
prefix operator.

**Fixed:** `F` and `P` followed by `==` now parse as abbreviation
names.  They remain reserved in expression context (e.g. `F S`
still means `\finset S`).

| Letter | Token | Z operator |
|--------|-------|------------|
| `F`    | FINSET | `\finset` (finite sets) |
| `P`    | POWER  | `\power` (power set) |

`N` and `Z` are not reserved — they lex as plain identifiers and
have always worked as abbreviation names.

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
a relational-algebra construct are automatically routed to `\noindent$...$`
(inline math) instead of `\begin{zed}...\end{zed}`.  Fuzz
silently skips inline math.  Standalone expressions (not
abbreviations) also route to inline math.  The `.tex` and PDF
are always correct; the limitation is only on what fuzz can
verify.

**See also.** Gotcha #1: a pure-Z abbreviation that references
algebra-defined names is routed to inline math as well.

---

## 4. ~~Characteristic expression after `.` cannot start with a field access~~ (RESOLVED)

**Fixed in v1.4.1.**  The parser now uses whitespace to
disambiguate: tight `s.x` is field access, spaced `. s` is the
bullet separator.

---

## 5. ~~Rename `[new/old]` only works on bare identifiers~~ (RESOLVED)

**Fixed.**  `(S join T)[a/x]`, `sigma[p](R)[a/x]`, and
`pi[a,b](R)[c/a]` now parse correctly as relation renames on
compound expressions.  The `[` must immediately follow the closing
token (no whitespace) and the bracket must contain `/`.

---

## 6. ~~`sigma` and `pi` require parentheses around the relation~~ (RESOLVED)

**Fixed.**  Both `sigma[p]R` and `pi[a,b]R` (no parentheses) now
parse correctly.  Parentheses are still accepted and recommended
for complex relation arguments.

---

## 7. Unspaced `>` or `<` inside `sigma[...]` lexes as angle bracket

Tracking: [#121](https://github.com/jmf-pobox/txt2tex/issues/121).

**Symptom.** A sigma predicate with an unspaced `>` or `<` is
rejected:

```text
sigma[groupcount>1](R)
```

```text
Error: Unspaced '>' inside sigma[...] is parsed as an angle bracket — add spaces around the operator (e.g. sigma[x > 1] not sigma[x>1])

1 | sigma[groupcount>1](R)
  |      ^
```

The lexer disambiguates `>` and `<` based on spacing: without a
leading space, `>` becomes RANGLE (closing angle bracket `⟩`) and
`<` becomes LANGLE (opening angle bracket `⟨`).  The sigma
predicate parser then sees a broken expression and stops with the
error above.

The two-character operators `>=` and `<=` are not affected — they
always lex correctly regardless of spacing.

**Triggering examples.**

```text
sigma[x>1](R)            -- FAILS: > lexes as RANGLE
sigma[x<10](R)           -- FAILS: < lexes as LANGLE
sigma[x > 1](R)          -- OK: spaced > lexes as GREATER_THAN
sigma[x < 10](R)         -- OK: spaced < lexes as LESS_THAN
sigma[x>=1](R)           -- OK: >= always lexes as GREATER_EQUAL
sigma[x<=10](R)          -- OK: <= always lexes as LESS_EQUAL
```

**Workaround.** Always put spaces around `>` and `<` inside
`sigma[...]`:

```text
sigma[groupcount > 1](R)
sigma[x > 1 land y < 10](R)
```
