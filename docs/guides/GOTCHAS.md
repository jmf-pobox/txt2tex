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

---

## 4. Characteristic expression after `.` cannot start with a field access

**Symptom.** A set comprehension whose characteristic expression
begins with a dotted field access fails to parse:

```text
{ s : S | pred . s.x }
```

The parser cannot disambiguate `.` as the comprehension separator
(bullet) from `.` as a field-access operator.  It consumes `. s`
as a field projection on the last token of the predicate, then
chokes on `.x`.

**Workaround.** Parenthesise the characteristic expression:

```text
{ s : S | pred . (s.x) }
```

Or use binding notation (the Z-canonical form for relational
calculus, which returns a named-attribute relation):

```text
{ s : S | pred . {| x == s.x |} }
```

This is a parser bug, not a design limitation.  Tracked for fix.

---

## 5. Rename `[new/old]` only works on bare identifiers

**Symptom.** Applying a rename postfix to a compound expression
fails, even when parenthesised:

```text
(S join T)[a/x]         // parse error
sigma[p](R)[a/x]        // parse error
```

The parser treats `[` after a non-identifier as the start of a
generic-instantiation parameter list, not a rename.

**Workaround.** Assign the compound expression to an abbreviation,
then rename the abbreviation:

```text
A == S join T
A[a/x]
```

This is a parser limitation.  Rename dispatches correctly when the
base is a bare identifier (`S[a/x]`) or a decorated identifier
(`S'[a/x]`).
