# Tutorial 9: Schemas and Composition

<!-- markdownlint-disable-next-line MD036 -->
**Lecture 9: Advanced Z Notation**

Learn schema composition, state schemas, operations, and zed blocks.

**Prerequisites:** Tutorial 8  
**Examples:** `examples/10_schemas/`

---

## Schema Notation

**Schema:** Groups related variables with constraints

```text
schema Counter
  count : N
  limit : N
where
  count <= limit
end
```

**Components:** Access with dot notation

```text
c.count
c.limit
```

## State Schemas

Model system state:

```text
schema Library
  books : P Book
  borrowed : Book +-> Member
where
  dom borrowed subseteq books
end
```

## Operation Schemas

Model state changes using primed variables ('):

```text
schema BorrowBook
  Library
  Library'
  book? : Book
  member? : Member
where
  book? in books
  book? notin dom borrowed
  borrowed' = borrowed union {book? |-> member?}
  books' = books
end
```

**Conventions:**

- `x'` (primed) - value after operation
- `x?` (input) - operation input
- `x!` (output) - operation output

## Schema Inclusion and Δ/Ξ

**Phase 1.1 feature.** Schema inclusion brings the components of one schema
into the declaration list of another.  Three forms are supported.

### Bare inclusion

```text
schema LoggedInUser
  User
  sessionToken : N
where
  sessionToken > 0
end
```

`User` on its own line (no colon) is a bare schema inclusion.  It brings all
User components and constraints into LoggedInUser.

### Delta inclusion — before/after state

The Z RM §3.7 convention: `Delta S` abbreviates including both the before-state
`S` and the after-state `S'` simultaneously.  Use this for operation schemas that
modify state:

```text
schema Counter
  count : N
where
  count >= 0
end

schema IncrCounter
  Delta Counter
  increment? : N
where
  count' = count + increment?
end
```

LaTeX output: `\Delta Counter`

### Xi inclusion — read-only operation

The Z RM §5.2 convention: `Xi S` asserts the state is unchanged.  Use this for
query operations:

```text
schema ReadCount
  Xi Counter
  result! : N
where
  result! = count
end
```

LaTeX output: `\Xi Counter`

### Generic instantiation

Inclusions can carry type parameters:

```text
schema PushNat
  Delta Stack[N]
  value? : N
end
```

LaTeX output: `\Delta Stack[\nat]`

### Schema-as-predicate

Once schemas are included in the declaration list, their names can appear in the
`where` clause as predicates.  The conjunction `S1 land S2` applies both schema
predicates:

```text
schema A
  x : N
end

schema B
  y : N
end

schema AB
  A
  B
  z : N
where
  A land B
  z = x + y
end
```

### Disambiguation rule

The parser uses a one-pass lookahead scan to distinguish a bare inclusion from a
typed declaration:

- If a colon `:` appears before the next newline, parse as a typed declaration.
- Otherwise, parse as a schema inclusion.

This means `count, limit : N` (two variables sharing a type) is never confused
with `Counter` (a bare inclusion), even when both appear on the same line start.

**See:** `examples/10_schemas/delta_xi_inclusion.txt` and
`examples/10_schemas/schema_as_predicate.txt`

### θ-Expression

**Phase 1.2 feature.** The `theta S` expression constructs the binding whose
components are the in-scope variables matching schema S's signature (Z RM §3.10).
It is the standard way to pass or record a complete state snapshot.

```text
schema AddBooking
  Delta AirlineState
  bookingId? : BookingId
  Booking
where
  bookings' = bookings oplus { bookingId? |-> theta Booking' }
end
```

Here `theta Booking'` packages the after-state binding for the new booking.
The unprimed form `theta S` refers to the before-state binding.

The primed form `theta S'` is idiomatic for state-transition operations:

```text
schema SnapshotState
  Xi AirlineState
  snapshot! : AirlineState
where
  snapshot! = theta AirlineState
end
```

**Rules:**

- `theta` is lowercase (the Z RM operator is `\theta`, not `\Theta`).
- `theta` is a reserved keyword: `theta'`, `theta?`, `theta!` are rejected
  by the lexer.
- The schema reference after `theta` may carry Phase-0 decoration: `theta S'`,
  `theta S?` are valid if `S'` and `S?` are valid identifiers in scope.

**Generated LaTeX:**  `theta S` emits `\theta S` — the standard Greek letter
macro, compatible with both `fuzz.sty` and `zed-cm.sty`.

**See:** `examples/10_schemas/theta_binding.txt`

## Horizontal Schema Definitions

**Phase 1.3 feature.** The `defs` keyword writes a Z RM §3.8 *horizontal
definition* — a single-line paragraph that assigns a new name to a schema
expression without creating a boxed schema environment.

```text
Name [generics]? defs RHS
```

The output is always `\begin{zed} Name \defs RHS \end{zed}`.  The `\defs`
macro is defined in `fuzz.sty` (line 280) as `\widehat=`.

### Schema reference RHS

The simplest form names an existing schema, possibly with a Delta or Xi prefix:

```text
OpAlias defs Delta Counter
```

Generated LaTeX:

```latex
\begin{zed}
OpAlias \defs \Delta Counter
\end{zed}
```

Other decorated forms:

```text
ReadOp defs Xi Counter
CounterCopy defs Counter
```

### Inline schema text RHS

The RHS may be an inline schema text `[ decl-list | pred-list ]`:

```text
NatPair defs [ x, y : N | x < y ]
```

Generated LaTeX:

```latex
\begin{zed}
NatPair \defs [ x : \nat; y : \nat | x < y ]
\end{zed}
```

Declarations are separated by `;`.  Multiple predicates are separated by `;`
in the source and joined with `\land` in the output:

```text
BoundedNat defs [n : N | n > 0; n < 100]
```

### Generic LHS

Square brackets on the LHS carry type parameters:

```text
StackAlias[X] defs GenStack[X]
```

Generated LaTeX:

```latex
\begin{zed}
StackAlias[X] \defs GenStack[X]
\end{zed}
```

### Constraints and rules

- `defs` is a reserved keyword; `defs'`, `defs?`, `defs!` are rejected by
  the lexer.
- Schema-calculus operators (`;`, `>>`, hide, project) on the RHS are not
  supported in Phase 1.3.  Those are Phase 3.2.
- A missing RHS (`Name defs` with nothing following) is a parse error with
  position information.

**See:** `examples/10_schemas/horizontal_defs.txt`

## Schema Renaming

**Phase 3.1 feature.** Schema renaming produces a schema identical to an
existing schema except that named components are given new names.  The
notation is per Z RM §3.11:

```text
NewName defs OldSchema[oldComponent/newComponent, ...]
```

### Single rename

```text
schema Counter
  count : N
where
  count >= 0
end

CounterN defs Counter[count/n]
```

Generated LaTeX:

```latex
\begin{zed}
CounterN \defs Counter[count/n]
\end{zed}
```

### Multiple renames

Multiple pairs are comma-separated:

```text
SwappedPoint defs Point[x/y, y/x]
```

Generated LaTeX: `SwappedPoint \defs Point[x/y, y/x]`

### Decorated schema reference

The decoration on the schema name is tightest-binding (Z RM §3.11):
`S'[a/b]` renames the primed schema `S'`, not the result of renaming
and then priming.  Because Phase 0's lexer bakes the prime into the
identifier token, `S'[a/b]` lexes as `IDENT("S'")` then `[` — the
rename handler sees the decorated identifier directly.

```text
Op2 defs Counter[count'/count]
```

### Decorated component names in pairs

The source and target names in each pair may themselves carry decoration:

```text
CounterOp defs Counter[count'/n]
```

### Disambiguation rule

The parser uses a scan of the bracket contents at depth 0 to distinguish
schema renaming from generic instantiation:

- Any `/` token at depth 0 inside `[...]` → schema rename `S[a/b, ...]`
- No `/` token → generic instantiation `S[X, Y, ...]` (Phase 1.1)

This means `Stack[N]` continues to parse as generic instantiation
unchanged, and `Counter[count/n]` parses as a rename.

**See:** `examples/10_schemas/schema_rename.txt`

## Schema Composition

Combine schemas using operators:

**Conjunction:**

```text
SchemaA land SchemaB
```

**Disjunction:**

```text
SchemaA lor SchemaB
```

**Sequential composition:**

```text
SchemaA o9 SchemaB
```

## Zed Blocks

Wrap `given` types, free-type definitions, and abbreviations in a `zed` block
to group them in a single `\begin{zed}...\end{zed}` LaTeX environment.
Use `axdef` and `schema` at the top level (not nested inside `zed`).

```text
zed
  given Person, Account
  Status ::= active | suspended | closed
end

axdef
  maxAccounts : N
where
  maxAccounts = 10
end

schema Bank
  accounts : Person +-> Account
where
  forall p : Person | # (accounts(| {p} |)) <= maxAccounts
end
```

**See:** `examples/10_schemas/zed_blocks.txt`

## Scoping

**Global scope:** given types, axdef, free types  
**Schema scope:** schema components  
**Quantifier scope:** forall/exists variables  
**Lambda scope:** lambda parameters

**See:** `examples/10_schemas/scoping_demo.txt`

## Complete Example

```text
=== Banking System ===

given Customer, Account

Status ::= open | closed

schema Bank
  accounts : Customer +-> Account
  status : Account -> Status
where
  ran accounts subseteq dom status
end

schema OpenAccount
  Bank
  Bank'
  customer? : Customer
  account! : Account
where
  customer? notin dom accounts
  account! notin ran accounts
  accounts' = accounts union {customer? |-> account!}
  status' = status union {account! |-> open}
end

schema CloseAccount
  Bank
  Bank'
  account? : Account
where
  account? in ran accounts
  status(account?) = open
  status' = status ++ {account? |-> closed}
  accounts' = accounts
end
```

## Summary

You've learned:

- ✅ Schema notation and components
- ✅ State schemas for system modeling
- ✅ Operation schemas with primed variables
- ✅ Schema inclusion and composition
- ✅ Zed blocks for grouping definitions
- ✅ Scoping rules

**Next:** [Tutorial: Advanced Features](10_advanced.md)

---

**Practice:** Explore `examples/10_schemas/`
