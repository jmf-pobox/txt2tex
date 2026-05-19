# Schema Notation

This directory contains examples of Z schema notation, including schemas, axiomatic definitions, and zed blocks.

## Topics Covered

- Basic schemas
- Generic schemas with type parameters
- Anonymous schemas
- Axiomatic definitions (`axdef`)
- Zed blocks (unboxed paragraphs)
- **Critical**: Schema vs axdef scoping rules

## Container Types

### Schemas

```text
schema State
  count : N
where
  count >= 0
end
```

**Scoping**: Components have **LOCAL** scope - cannot be referenced outside the schema.

### Axiomatic Definitions

```text
axdef
  population : N
where
  population > 0
end
```

**Scoping**: Identifiers have **GLOBAL** scope - accessible throughout the document.

### Zed Blocks

```text
zed
  forall x : N | x >= 0
end
```

**Purpose**: Unboxed Z notation paragraphs for predicates and abbreviations.

## Critical Scoping Rule

**This is the most common source of fuzz errors:**

```text
// ❌ WRONG: Schema components are LOCAL
schema Library
  books : F BookId
where
  ...
end

Answer == {b : dom books | ...}  // ERROR: books not in scope!

// ✅ RIGHT: Use axdef for GLOBAL identifiers
axdef
  books : F BookId
where
  ...
end

Answer == {b : dom books | ...}  // OK: books is globally accessible
```

**Rule**: Use `axdef` when other parts of your specification need to reference the declared identifiers. Use `schema` for encapsulated type definitions.

## Schema Inclusion (Phase 1.1)

Three forms of schema inclusion are supported in `schema`, `axdef`, and `gendef`
declaration lists per Z RM §3.7 and §5.2:

```text
schema Operation
  Delta State       // before/after state (Δ convention)
  Xi OtherState     // read-only operation (Ξ convention)
  AnotherSchema     // bare inclusion (brings components into scope)
  x? : N            // typed declaration
where
  ...
end
```

**Disambiguation:** A line with a colon (`:`) is always a typed declaration,
even if the identifier to its left matches a schema name.  `count, limit : N`
declares two variables; `Counter` alone is a bare schema inclusion.

## θ-Expression (Phase 1.2)

The `theta S` keyword constructs the binding whose components are the
in-scope variables matching schema S's signature (Z RM §3.10).

```text
schema AddBooking
  Delta AirlineState
  bookingId? : BookingId
  Booking
where
  bookings' = bookings oplus { bookingId? |-> theta Booking' }
end
```

- `theta Booking'` packages the after-state binding for the new booking.
- `theta S` (unprimed) refers to the before-state binding.
- `theta S = theta S'` is the standard Ξ-style frame condition.

**Rule:** `theta` is a reserved keyword.  `theta'`, `theta?`, `theta!`
are not valid — the lexer rejects them.

## Horizontal Schema Definitions (Phase 1.3)

The `defs` keyword writes a Z RM §3.8 horizontal definition — a single-line
form that assigns a name to a schema expression without a boxed paragraph.

Two RHS forms:

```text
// Schema reference (possibly decorated)
OpAlias defs Delta Counter

// Inline schema text
NatPair defs [ x, y : N | x < y ]
```

Both forms emit `\begin{zed} Name \defs RHS \end{zed}`.

The `\defs` macro (defined in `fuzz.sty` as `\widehat=`) is available without
any preamble additions.

Generic type parameters on the LHS are written in square brackets:

```text
StackAlias[X] defs GenStack[X]
```

Multiple predicates in an inline schema text are separated by `;`:

```text
BoundedNat defs [n : N | n > 0; n < 100]
```

## Examples in This Directory

Browse the `.txt` files to see:

- Basic and generic schemas
- Axiomatic definitions with constraints
- Zed block usage
- Scoping demonstrations (axdef vs schema)
- **delta_xi_inclusion.txt** — Δ/Ξ airline booking probe (Phase 1.1)
- **schema_as_predicate.txt** — schema conjunction in where clause (Phase 1.1)
- **theta_binding.txt** — θ-expression in state-transition operations (Phase 1.2)
- **horizontal_defs.txt** — horizontal schema definitions with `defs` (Phase 1.3)
- **schema_rename.txt** — schema renaming `S[old/new, ...]` (Phase 3.1, Z RM §3.11)

## See Also

- **docs/guides/USER_GUIDE.md** - Section "Schema Inclusion (Bare, Δ, Ξ)",
  subsection "θ-Expression", and subsection "Horizontal Schema Definitions"
- **docs/tutorials/09_schemas.md** - Section "Schema Inclusion and Δ/Ξ",
  subsection "θ-Expression", and subsection "Horizontal Schema Definitions"
- **Previous**: 09_sequences/
- **Next**: 11_text_blocks/
