# Generic Definition Research: Features 3 & 4

**Date**: 2025-11-21
**Objective**: Determine fuzz-compatible implementation for Features 3 & 4 from gendef_advanced.txt
**Requirement**: Full fuzz typechecker compatibility (Option A)

## Executive Summary

**Finding**: Features 3 and 4 (free types and schemas inside `gendef` blocks) are **aspirational syntax** not supported by the fuzz typechecker. These examples exist in gendef_basic.txt and gendef_advanced.txt but do not compile.

**Recommendation**: These features cannot be implemented with full fuzz compatibility. They should be marked as **future enhancements** requiring either:
1. Extensions to the fuzz typechecker itself (outside our scope), OR
2. Alternative expression using existing fuzz-compatible patterns (documented below)

## Research Process

### Phase 1: Fuzz Manual Analysis

Analyzed fuzz manual parts 1-5, focusing on formal syntax specification (part 5, section 7).

**Key Finding from Formal Grammar** (fuzz manual page 55):

```
Generic-Box ::= \begin{gendef}[Gen-Formals]
                Decl-Part
                [ \where
                Axiom-Part ]
                \end{gendef}

Decl-Part ::= Basic-Decl Sep . . . Sep Basic-Decl

Basic-Decl ::= Decl-Name, . . . , Decl-Name : Expression
             | Schema-Ref
```

**Conclusion**: The fuzz grammar explicitly limits `gendef` blocks to:
- Declarations (`name : type` pairs)
- Schema references (to previously defined schemas)
- Optional `where` clause with predicates

Free type definitions (`::=`) and schema definitions (`schema Name ... end`) can ONLY appear as `Item`s in unboxed paragraphs (`\begin{zed}...\end{zed}`), NOT inside `gendef` blocks.

### Phase 2: Example Analysis

Examined existing examples to understand current usage patterns.

#### Working Examples (gendef_basic.txt, lines 26-172):
- Generic identity function
- Generic pair functions (first, second)
- Generic singleton set
- Generic sequence operations
- All use declarations with type expressions

#### Non-Working Examples:

**Example 7** (gendef_basic.txt, lines 106-108):
```
gendef [X]
  Maybe_X ::= nothing | just⟨X⟩
end
```
**Status**: Does NOT compile
**Error**: `Expected ':' in declaration`

**Example 5** (gendef_advanced.txt, lines 88-90):
```
gendef [X]
  Tree_X ::= leaf | node⟨X × Tree_X × Tree_X⟩
end
```
**Status**: Does NOT compile
**Error**: `Expected ':' in declaration` at line 89, column 10

**Example 6** (gendef_advanced.txt, lines 98-105):
```
gendef [X]
  schema Container_X
    contents : seq X
    capacity : N
  where
    # contents <= capacity
  end
end
```
**Status**: Does NOT compile (nested schema not supported)

#### Instructor's Warning

Found in gendef_basic.tex:161:
> "However, free types with generic parameters require special syntax."

This confirms the instructor is aware that generic free types need different syntax than currently implemented.

### Phase 3: Fuzz Compatibility Testing

Tested various syntax patterns to determine what fuzz actually supports.

**Test 1**: Free type in gendef ❌
```
gendef [X]
  Maybe_X ::= nothing | just⟨X⟩
end
```
Result: Parser error

**Test 2**: Generic parameters in zed block ❌
```
[X]
Tree_X ::= leaf | node⟨X cross Tree_X cross Tree_X⟩
```
Result: Parser error (our parser doesn't support `[X]` as an Item)

**Test 3**: Standard gendef with declarations ✅
```
gendef [X]
  id : X -> X
where
  forall x : X | id(x) = x
end
```
Result: Compiles successfully

## Features Analysis

### Feature 3: Free Types Inside gendef

**What it attempts**:
```
gendef [X]
  Tree_X ::= leaf | node⟨X × Tree_X × Tree_X⟩
end
```

**Why it fails**:
- Fuzz grammar doesn't allow `::=` inside `gendef` blocks
- Parser expects `:` for declarations, gets `::=`

**Fuzz-compatible alternative**: None that preserves the same semantic meaning.

**Standard Z notation**: Generic free types are typically defined in unboxed paragraphs with formal parameters:
```latex
\begin{zed}
[X] \\
Tree_X ::= leaf \mid node \langle X \cross Tree_X \cross Tree_X \rangle
\end{zed}
```

**Our implementation status**: Our parser doesn't support `[X]` as an Item in zed blocks (this would need to be implemented first).

### Feature 4: Schemas Inside gendef

**What it attempts**:
```
gendef [X]
  schema Container_X
    contents : seq X
    capacity : N
  where
    # contents <= capacity
  end
end
```

**Why it fails**:
- Fuzz grammar doesn't allow nested `schema` definitions
- `gendef` can only contain declarations and predicates

**Fuzz-compatible alternative**: Define generic schema outside gendef, using schema parameters:
```latex
\begin{schema}{Container}[X]
contents : \seq X \\
capacity : \nat
\where
\# contents \leq capacity
\end{schema}
```

**Our implementation status**: Need to verify if our parser supports generic parameters on schemas (`{Name}[X]` syntax).

## Fuzz Typechecker Limitations

Based on formal grammar analysis and testing, fuzz does NOT support:

1. **Free type definitions inside gendef blocks**
   - Syntax: `gendef [X] Type_X ::= ... end`
   - Fuzz requirement: Free types must be in unboxed (zed) paragraphs

2. **Schema definitions inside gendef blocks**
   - Syntax: `gendef [X] schema S_X ... end end`
   - Fuzz requirement: Schemas must be defined separately

3. **Generic parameters in unboxed paragraphs** (possibly)
   - Syntax: `[X] Type ::= ...` in zed blocks
   - Status: Need to verify if fuzz supports this
   - Our parser: Doesn't currently support this

## Recommendations

### Option A: Mark as Future Enhancements (RECOMMENDED)

Accept that Features 3 & 4 require syntax extensions beyond standard fuzz:

1. Document in `FUZZ_FEATURE_GAPS.md` that these are aspirational features
2. Create test files marked as "future" or "not-yet-supported"
3. Focus implementation efforts on features that ARE fuzz-compatible

### Option B: Implement Workarounds

For users who need generic structures now:

**For Generic Free Types**:
- Use parameterized type abbreviations instead of free types
- Define separate instances for each concrete type
- Use gendef to define operations on the generic type

Example:
```
given Tree_Nat
given Tree_Person

gendef [X]
  mkLeaf : Tree_X
  mkNode : X cross Tree_X cross Tree_X -> Tree_X
where
  ...
end
```

**For Generic Schemas**:
- Define schemas with generic parameters using standard syntax
- Use schema references in gendef blocks

Example:
```
schema Container [X]
  contents : seq X
  capacity : N
where
  # contents <= capacity
end

gendef [X]
  emptyContainer : Container[X]
where
  ...
end
```

### Option C: Extended Research

If full support is required, additional research needed:

1. Study Mike Spivey's fuzz source code to understand if/how generic free types are supported
2. Check if newer versions of fuzz added this support
3. Investigate if ZRM (Z Reference Manual) specifies this syntax
4. Examine how other Z tools (e.g., CZT, Z/EVES) handle generic free types

## Implementation Decision Required

**Question for User**: Given that Features 3 & 4 are not supported by fuzz:

1. **Accept limitation**: Mark gendef_advanced.txt examples as aspirational/future, focus on implementing fuzz-compatible features?

2. **Implement workarounds**: Provide alternative syntax that achieves similar goals using fuzz-compatible patterns?

3. **Extended research**: Investigate further to find if there's a fuzz-compatible way we haven't discovered yet?

## References

- Fuzz manual part 5, Section 7 (Syntax Summary)
- Fuzz manual part 2, Section 3.9.2 (Generic definitions)
- examples/06_definitions/gendef_basic.txt (lines 106-108, non-working example)
- examples/06_definitions/gendef_advanced.txt (lines 88-90, 98-105, non-working examples)
- docs/SESSION_RESUME_GENDEF_ADVANCED.md (project context)

## Next Steps

Awaiting user decision on which option to pursue before proceeding with implementation.
