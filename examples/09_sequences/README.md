# Lecture 9: Sequences

This directory contains examples for Lecture 9, covering sequences and bags.

## Topics Covered

- Sequence types (`seq`, `iseq`)
- Sequence literals (Unicode `⟨⟩` or ASCII `<>`)
- Concatenation (`⌢` or ` ^ ` with spaces)
- Sequence length (`#`)
- Sequence functions (head, tail, last, front, rev)
- Pattern matching with sequences
- Filter operator (`filter` or `↾`)
- Bags (`bag`) and bag union (`bag_union` or `⊎`)

## Key Operators

```
seq(X)           →  seq X       [sequence type]
iseq(X)          →  iseq X      [injective sequence type]
⟨⟩               →  ⟨⟩          [empty sequence]
⟨a, b, c⟩        →  ⟨a, b, c⟩   [sequence literal]
s ⌢ t            →  s ⌢ t       [concatenation]
s ^ t            →  s ⌢ t       [concatenation - REQUIRES SPACES]
# s              →  # s         [length]
head s           →  head s      [first element]
tail s           →  tail s      [all but first]
s filter A       →  s ↾ A       [filter to set A]
bag(X)           →  bag X       [bag type]
[[a, b, c]]      →  ⟦a, b, c⟧   [bag literal]
b1 bag_union b2  →  b1 ⊎ b2     [bag union]
```

## Critical: Concatenation Whitespace

The `^` operator has dual meaning based on whitespace:

```
<x> ^ <y>        →  ⟨x⟩ ⌢ ⟨y⟩    [concatenation - WITH SPACE]
x^2              →  x²           [exponentiation - NO SPACE]
```

**Always use space before `^` for concatenation, or use `⌢` (U+2040).**

## Pattern Matching

Sequences enable recursive function definitions:

```
f(<>) = 0                        [empty sequence case]
f(<x> ^ s) = x + f(s)            [cons pattern: head and tail]
```

## Examples in This Directory

Browse the `.txt` files to see:
- Basic sequence operations
- Concatenation patterns
- Pattern matching for recursion
- Filter usage
- Bag operations

## See Also

- **docs/USER_GUIDE.md** - Section "Sequences"
- **docs/TUTORIAL_09.md** - Detailed tutorial for Lecture 9
- **Previous**: 08_functions/
- **Next**: 10_schemas/
