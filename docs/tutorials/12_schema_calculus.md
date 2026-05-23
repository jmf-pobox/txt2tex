# Tutorial 12: Schema Calculus Operators

Level: Advanced.  Prerequisite: Tutorial 9 (Schemas).

Z RM §3.11 defines four schema-calculus operators that combine schemas into
new schemas.  This tutorial covers all four: composition, piping, hiding, and
projection.

---

## What schema calculus is for

Schema calculus lets you build complex operations from simpler ones.  Instead
of writing a monolithic schema for a compound operation, you define the
component operations separately and compose them.

---

## 1. Schema composition  `S ; T`

Composition sequences two operations: the output state of `S` feeds into the
input state of `T`.  The parser recognises `;` as schema composition when it
appears on the RHS of a `defs` paragraph; inside `axdef`, `schema`, and
`gendef` bodies `;` still separates declarations.

### Source

```text
schema Inc
  n, n' : N
where
  n' = n + 1
end

schema Double
  n, n' : N
where
  n' = n + n
end

IncThenDouble defs Inc ; Double
```

### Generated LaTeX

```latex
\begin{zed}
IncThenDouble \defs Inc \semi Double
\end{zed}
```

### Associativity

Composition is left-associative: `A ; B ; C` parses as `(A ; B) ; C`.

---

## 2. Schema piping  `S >> T`

Piping connects the output channel (decorated with `!`) of `S` to the input
channel (decorated with `?`) of `T`, then hides the channel components.

Piping has lower precedence than composition: `S ; T >> U` parses as
`(S ; T) >> U`.

### Source

```text
schema Send
  channel! : N
where
  channel! > 0
end

schema Receive
  channel? : N
where
  channel? < 100
end

Pipeline defs Send >> Receive
```

### Generated LaTeX

```latex
\begin{zed}
Pipeline \defs Send \pipe Receive
\end{zed}
```

---

## 3. Schema hiding  `S hide (x, y)`

Hiding removes named components from the schema signature, turning them into
existentially quantified variables in the predicate part.  Hiding binds
tighter than composition.

### Source

```text
schema State
  x, y, temp : N
where
  x < y
  temp > 0
end

Visible defs State hide (temp)
```

### Generated LaTeX

```latex
\begin{zed}
Visible \defs State \hide (temp)
\end{zed}
```

### Multiple names

```text
Reduced defs State hide (x, y)
```

---

## 4. Schema projection  `S project T`

Projection restricts the signature of `S` to the components declared in `T`,
keeping the predicate of `S` over those components.  Projection has the same
precedence level as hiding.

### Source

```text
schema Full
  x, y, z : N
where
  x < y
  y < z
end

schema View
  x, z : N
end

Projected defs Full project View
```

### Generated LaTeX

```latex
\begin{zed}
Projected \defs Full \project View
\end{zed}
```

---

## 5. Combining operators

Operators can be combined.  Precedence (tightest to loosest):

1. `hide` and `project`
2. `;` (composition)
3. `>>` (piping)

Parentheses override the default grouping.

### Example: hide then compose

```text
OpFiltered defs (OpA ; OpB) hide (temp)
```

You write `(OpA ; OpB)` to force grouping in the source, but txt2tex
drops the source parentheses in the emitted LaTeX:

Generated: `OpA \semi OpB \hide (temp)`

Because fuzz's `\hide` binds tighter than `\semi`, the rendered output
is read as `OpA \semi (OpB \hide (temp))` — the opposite of what the
source parentheses suggest.  To preserve grouping in the output, use
an explicit intermediate name:

```text
Joined defs OpA ; OpB
OpFiltered defs Joined hide (temp)
```

### Example: compose then pipe

```text
Step defs (OpA ; OpB) >> Receive
```

Composition produces the left operand of the pipe.

---

## 6. Acceptance probe

The canonical Phase 3.2 example from the build plan:

```text
schema OpA
  x, x' : N
where
  x' > x
end

schema OpB
  x, x' : N
where
  x' < 100
end

OpAB defs OpA ; OpB
```

This generates:

```latex
\begin{zed}
OpAB \defs OpA \semi OpB
\end{zed}
```

The `\semi` macro is defined in `fuzz.sty` (line 295) and `zed-cm.sty`
(line 493).  No preamble change is needed — the CLI bundles all required
assets.

---

## LaTeX macros reference

| Source        | LaTeX macro    | fuzz.sty line |
|---------------|----------------|---------------|
| `S ; T`       | `\semi`        | 295           |
| `S >> T`      | `\pipe`        | 296           |
| `S hide (x)`  | `\hide`        | 300           |
| `S project T` | `\project`     | 302           |

---

## See also

- `examples/15_schema_calculus/` — worked examples
- `docs/guides/USER_GUIDE.md §Schema Calculus Operators`
- Z Reference Manual §3.11
