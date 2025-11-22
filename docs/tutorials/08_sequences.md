# Tutorial 8: Sequences

**Lecture 8: Sequences and Bags**

Learn sequence notation, sequence operations, pattern matching, and bags (multisets).

**Prerequisites:** Tutorial 7  
**Examples:** `examples/09_sequences/`

---

## Sequence Basics

**Sequence:** Ordered collection (unlike sets)

**Notation:**
```
⟨⟩                   (empty sequence - Unicode)
<>                   (empty sequence - ASCII)
⟨1, 2, 3⟩            (sequence literal - Unicode)
<1, 2, 3>            (sequence literal - ASCII)
```

**Type:**
```
s : seq N            (sequence of natural numbers)
```

**See:** `examples/09_sequences/sequence_basics.txt`

## Sequence Operations

### Head and Tail

```
head <1, 2, 3> = 1
tail <1, 2, 3> = <2, 3>
```

### Last and Front

```
last <1, 2, 3> = 3
front <1, 2, 3> = <1, 2>
```

### Reverse

```
rev <1, 2, 3> = <3, 2, 1>
```

### Concatenation

```
<1, 2> ⌢ <3, 4> = <1, 2, 3, 4>
<1, 2> ^ <3, 4> = <1, 2, 3, 4>    (ASCII alternative)
```

### Length (Cardinality)

```
# <1, 2, 3> = 3
# <> = 0
```

**See:** `examples/09_sequences/sequence_operations.txt`, `examples/09_sequences/concatenation.txt`

## Pattern Matching

Define functions recursively using sequence patterns:

```
axdef
  total : seq N -> N
where
  total(<>) = 0
  forall x : N; s : seq N |
    total(<x> ^ s) = x + total(s)
end
```

**Pattern:** `<x> ^ s` means "a sequence with first element x and remaining elements s"

**See:** `examples/09_sequences/pattern_matching.txt`

## Sequence Filter

**filter operator:** Keep only elements from a set

```
s filter A          (ASCII)
s ↾ A               (Unicode)
```

**Example:**
```
<1, 2, 3, 4, 5> filter {2, 4, 6} = <2, 4>
```

**See:** `examples/09_sequences/sequence_filter.txt`

## Bags (Multisets)

**Bag:** Unordered collection that allows duplicates

**Notation:**
```
[[1, 2, 2, 3, 3, 3]]
```

**Type:**
```
b : bag N
```

**Operations:**
```
b1 bag_union b2     (add multiplicities)
b1 ⊎ b2             (Unicode)
```

**See:** `examples/09_sequences/bags.txt`

## Complete Example

```
=== Sequence Examples ===

** Example 1: Basic Sequences **

<1, 2, 3, 4, 5>

** Example 2: Sequence Operations **

axdef
  s : seq N
  first : N
  rest : seq N
  reversed : seq N
where
  s = <1, 2, 3>
  first = head s
  rest = tail s
  reversed = rev s
end

TEXT: first = 1, rest = <2, 3>, reversed = <3, 2, 1>

** Example 3: Pattern Matching **

axdef
  sum : seq N -> N
where
  sum(<>) = 0
  forall x : N; s : seq N |
    sum(<x> ^ s) = x + sum(s)
end

TEXT: sum(<1, 2, 3>) = 1 + sum(<2, 3>) = 1 + 2 + sum(<3>) = 1 + 2 + 3 + sum(<>) = 6

** Example 4: Bags **

[[1, 1, 2, 3, 3, 3]]

TEXT: A bag where 1 appears twice and 3 appears three times.
```

## Summary

You've learned:
- ✅ Sequence notation (⟨⟩ and <>)
- ✅ Sequence operations (head, tail, concat, reverse)
- ✅ Pattern matching on sequences
- ✅ Sequence filter
- ✅ Bags (multisets)

**Next Tutorial:** [Tutorial 9: Schemas and Composition](docs/tutorials/09_schemas.md)

---

**Practice:** Explore `examples/09_sequences/`
