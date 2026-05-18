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

## Examples in This Directory

Browse the `.txt` files to see:

- Basic and generic schemas
- Axiomatic definitions with constraints
- Zed block usage
- Scoping demonstrations (axdef vs schema)
- **delta_xi_inclusion.txt** — Δ/Ξ airline booking probe (Phase 1.1)
- **schema_as_predicate.txt** — schema conjunction in where clause (Phase 1.1)

## See Also

- **docs/guides/USER_GUIDE.md** - Section "Schema Inclusion (Bare, Δ, Ξ)"
- **docs/tutorials/09_schemas.md** - Section "Schema Inclusion and Δ/Ξ"
- **Previous**: 09_sequences/
- **Next**: 11_text_blocks/
