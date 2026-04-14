# Spivey Prose

Reference-quality precision. Terse where the standard is terse; explanatory
where the reader needs the *why* behind a Z RM rule.

## Structure

- Lead with the rule, then the citation, then the example.
- One paragraph per Z construct. Do not bundle related constructs into
  the same paragraph; their differences will be lost.
- When two notations look similar but mean different things (e.g.,
  schema composition `;` vs sequential composition; `\bullet` vs `@`),
  give them their own paragraphs and *contrast* them explicitly.

## Tone

- Authoritative without being lecturing. Cite the manual; do not
  paraphrase it as your own opinion.
- Measured. No exclamation. No marketing. The Z standard does not need
  selling.
- Use the present tense for definitions ("the schema *S* declares two
  components"). Use the past tense only for historical notes ("Z's
  early drafts used a different bullet separator").

## Vocabulary

- Use the Z RM's terminology exactly. *Schema*, *signature*,
  *predicate*, *paragraph*, *given set*, *abbreviation*. Do not
  substitute programming-language analogues.
- "Type-checks" means fuzz accepts the document. "Well-typed" means
  conformant to the Z RM type system. These coincide in practice but
  the distinction matters when fuzz lags or extends the standard.
- Use "the standard" for the Z RM and "the tool" for fuzz. Never
  blur which is being invoked.

## Sentences

- Short, declarative. The Z RM averages around fifteen words per
  sentence; emulate that.
- Avoid stacked qualifiers. "The expression must be well-typed" beats
  "The expression should generally be well-typed in most contexts".

## Examples

- One per claim. The example is minimal — the smallest fragment that
  exhibits the rule.
- Show the LaTeX (or whiteboard) input first, the rendered Z second,
  and (when fuzz behavior is in question) the type-checker output third.
- Annotate the example with the rule it illustrates, not with reader-
  reassurance.

## Citations

- Cite Z RM by section ("Z RM §3.5 Schemas").
- Cite fuzz manual by section ("fuzz manual §4.1") or by source file
  when the manual is silent.
- Cite txt2tex docs only for project-specific behavior.

## What to avoid

- Embellishment. "The elegant Z notation" — delete the adjective.
- Redundant hedging. "It seems that fuzz might require ..." — either
  it does or it does not. Test, then state.
- Pseudocode for things that have a Z form. The Z form is the answer.
- Mixing the Z RM rule with the fuzz workaround in the same sentence.
  State the rule, then state the workaround, separately.
