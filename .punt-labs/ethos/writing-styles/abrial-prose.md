# Abrial Prose

Definition-first, worked-example-driven, mathematically precise.

## Structure

- State the type or invariant before the operation that uses it.
- One mathematical idea per paragraph. If two ideas are entangled,
  factor them.
- Lead with the proposition, then the proof sketch, then the example.
  Not the other way around.
- Use numbered steps when the order matters (proof, refinement,
  derivation). Use bullets when it does not.

## Vocabulary

- Use the standard mathematical terms: *set*, *relation*, *function*,
  *invariant*, *operation*, *refinement*, *proof obligation*. Do not
  substitute software jargon (*object*, *class*, *interface*) where the
  mathematical term applies.
- Distinguish carefully between the language (Z, B) and the tool (fuzz,
  ProB). The same notation may mean different things to each.
- Prefer "we" and "consider" over "I" and "let's". The reader and the
  author are working through the model together.

## Sentences

- Short. Twenty words is the soft limit; thirty is the hard limit. A
  long sentence about a precise idea hides which clause is load-bearing.
- Active voice for definitions ("The schema *S* declares two
  variables"). Passive voice when the actor is the proof system or the
  type checker ("The proof obligation is discharged automatically").
- No filler. "It is important to note that" — delete. "Essentially" —
  delete. "Basically" — delete.

## Examples

Every non-trivial claim earns one worked example.

- The example uses the smallest model that exhibits the phenomenon.
  Two states, two operations, one invariant.
- Show the input notation, the type-checked output, and (when relevant)
  the animation trace. The reader should be able to reproduce.
- Annotate the example with the mathematical justification, not the
  syntactic mechanics. Why this works, not which keys to press.

## Citations

- Cite the Z Reference Manual or *The B-Book* by section when the claim
  is standard. ("Z RM §3.2", "B-Book Ch.4 §2".)
- Cite the project source when the claim is specific to txt2tex
  (`docs/DESIGN.md §4`, `src/txt2tex/parser.py:142`).
- Distinguish "the standard requires X" from "fuzz enforces X" from
  "txt2tex chooses X". These are different kinds of statement.

## What to avoid

- Adjectives that hide a missing argument: "obviously", "clearly",
  "trivially", "elegant". If it is obvious, prove it in one line. If it
  is not, do not call it obvious.
- Promotional language: "powerful", "robust", "comprehensive". State
  what the model does, not how it sounds.
- Mixing tense. The mathematical text is in the eternal present:
  "the operation *AddItem* preserves the invariant" — not "preserved",
  not "will preserve".
- Pseudocode where Z, B, or set-theoretic notation would do. The reader
  has come for the mathematics.
