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
```
schema State
  count : N
where
  count >= 0
end
```
**Scoping**: Components have **LOCAL** scope - cannot be referenced outside the schema.

### Axiomatic Definitions
```
axdef
  population : N
where
  population > 0
end
```
**Scoping**: Identifiers have **GLOBAL** scope - accessible throughout the document.

### Zed Blocks
```
zed
  forall x : N | x >= 0
end
```
**Purpose**: Unboxed Z notation paragraphs for predicates and abbreviations.

## Critical Scoping Rule

**This is the most common source of fuzz errors:**

```
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

## Examples in This Directory

Browse the `.txt` files to see:
- Basic and generic schemas
- Axiomatic definitions with constraints
- Zed block usage
- Scoping demonstrations (axdef vs schema)

## See Also

- **docs/guides/USER_GUIDE.md** - Section "Schema Notation"
- **docs/tutorials/10_advanced.md** - Advanced schema patterns
- **Previous**: 09_sequences/
- **Next**: 11_text_blocks/
