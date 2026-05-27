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
a DAT construct are automatically routed to `\noindent$...$`
(inline math) instead of `\begin{zed}...\end{zed}`.  Fuzz
silently skips inline math.  Standalone expressions (not
abbreviations) also route to inline math.  The `.tex` and PDF
are always correct; the limitation is only on what fuzz can
verify.

**See also.** Gotcha #1 for the edge case where this routing
logic is fooled by a pure-Z expression that references
algebra-defined names.

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

**Symptom.** A sigma predicate with an unspaced `>` or `<` fails
to parse:

```text
sigma[groupcount>1](R)
```

```text
Error: Expected ']' after sigma predicate

1 | sigma[groupcount>1](R)
  |      ^
```

The lexer disambiguates `>` and `<` based on spacing: without a
leading space, `>` becomes RANGLE (closing angle bracket `⟩`) and
`<` becomes LANGLE (opening angle bracket `⟨`).  The sigma
predicate parser then sees a broken expression and reports a
missing `]`.

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
sigma[x > 1 and y < 10](R)
```
