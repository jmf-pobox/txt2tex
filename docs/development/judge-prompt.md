# Judge Prompt: Verification Inner Loop

**Status:** Companion to
[verification-procedure.md](verification-procedure.md). Lives on the
courseware-staging branch only.

This file is a **prompt template**. It is not loaded by code; the
inner-loop driver (the human or the main agent) fills the
placeholders and hands the result to a fresh Claude Code agent
invocation. A judge invocation is one-shot: the judge reads, writes
a verdict, and exits. The judge has no write access to the working
tree.

---

## How to use

1. Identify the question under verification: course `<C>`, sheet
   `<S>`, question `<Q>`, sub-question `<X>` (may be empty).
2. Locate the four inputs the judge needs (see §"Inputs" below).
3. Copy the template in §"Prompt template" verbatim. Fill every
   `{{double-brace}}` placeholder.
4. Spawn the judge:

   ```python
   Agent(
     subagent_type="general-purpose",
     description="Judge <C>-<S>-Q<Q><X>",
     prompt=<the filled template>
   )
   ```

5. The judge returns the YAML verdict block (§"Output schema") as
   its only text output. Parse it; record under
   `~/Coding/course-ox-<c>/verdicts/<S>-q<Q><X>-r<round>.yaml`.
6. Apply §5.5 of the verification procedure to decide the next
   action.

---

## Inputs the judge receives

The judge is told the absolute paths of four artifacts. It reads
them itself via the `Read` tool — do not paste their contents into
the prompt.

| Input | Modality | Path placeholder |
|-------|----------|------------------|
| Instructor's question (text) | text | `{{instructor_question_path}}` |
| Instructor's solution (text) | text | `{{instructor_solution_text_path}}` |
| Instructor's solution (rendered) | image PNG(s) | `{{instructor_solution_image_paths}}` (one or more, comma-separated) |
| Our `.tex` excerpt for the question | text | `{{our_tex_excerpt_path}}` |
| Our `.txt` source for the question | text | `{{our_txt_excerpt_path}}` |
| Our solution (rendered) | image PNG(s) | `{{our_solution_image_paths}}` (one or more, comma-separated) |

If the instructor solution is available only as a PDF (not a
separable text file), pass `null` for
`{{instructor_solution_text_path}}` and the judge will rely solely
on the PNG. Note that judgments degrade when text is absent: math
notation in raster form is harder to disambiguate.

---

## Prompt template

> Copy from below — replace every `{{ ... }}` with the concrete
> value.

```text
You are an LLM judge evaluating whether one solution to a
mathematics exercise (in Z notation / schema calculus / relational
algebra) is acceptably equivalent to another. You operate as a
sub-agent of the txt2tex verification procedure. You have read
access to the working tree and the listed paths. You DO NOT write,
edit, or commit anything. Your only output is the YAML verdict at
the end of this prompt.

The course is {{course_name_long}} ({{course_short}}). The
question is {{course_short}} exercise {{sheet}} question {{Q}}
{{X}}.

Read the following files in this order:

  Question prompt:
    {{instructor_question_path}}

  Instructor solution (text, may be null):
    {{instructor_solution_text_path}}

  Instructor solution rendered:
    {{instructor_solution_image_paths}}

  Our source (txt2tex whiteboard notation):
    {{our_txt_excerpt_path}}

  Our generated LaTeX excerpt:
    {{our_tex_excerpt_path}}

  Our solution rendered:
    {{our_solution_image_paths}}

The PNG is what a student would submit and what the instructor
would grade. Treat the PNG pair (instructor's + ours) as the
primary evidence. The text sources are supporting context — useful
for disambiguating notation in the raster — but the decision is
about how the two PNGs read to a Z-trained reader, not about how
the source text compares. A verdict reached without comparing both
PNGs is invalid.

The comparison is QUALITATIVE, not pixel-level. Different LaTeX
engines, different fonts, and different placement on the page are
expected and not penalised. You are not running a perceptual diff
or a structural-similarity score; you are forming a human-style
judgment about whether the two renderings make the same
mathematical statement and read well.

You will judge two axes independently:

  AXIS A: SEMANTIC EQUIVALENCE (do they say the same thing?)
  AXIS B: LAYOUT ACCEPTABILITY (does ours read well as a submission?)

You must form a confidence value in [0.0, 1.0] for the overall
verdict. Treat 0.85 as the threshold below which a human will
spot-check your verdict — do not inflate confidence to clear that
threshold. If you are unsure, say so.

------------------------------------------------------------
AXIS A: SEMANTIC EQUIVALENCE
------------------------------------------------------------

PASS this axis when all of the following hold:

  A1. Every quantifier (forall, exists, exists1, mu, lambda) in the
      instructor solution has a corresponding quantifier in ours
      over an equivalent domain. Quantifier ordering and binding
      structure may differ as long as the meaning is preserved.

  A2. Every schema in the instructor solution has a corresponding
      schema in ours with the same primary key and the same set of
      fields (modulo renaming and ordering).

  A3. Predicate logic statements are logically equivalent under
      classical first-order rewriting: de Morgan, contraposition,
      currying of implication, predicate distribution over
      conjunction, etc.

  A4. Cross-schema invariants (zed paragraphs, FK predicates,
      global constraints) are present in ours when present in the
      instructor's, and they capture the same property.

  A5. Numerical answers (counts, ranges, marks, bounds) match
      exactly.

  A6. The instructor's solution and ours both answer the question
      that was actually asked. (A correct solution to the wrong
      question is not equivalent.)

FAIL this axis when any of A1–A6 fails.

UNCLEAR this axis when the instructor solution is ambiguous, the
instructor PNG is illegible for the relevant region, or the math
notation cannot be disambiguated from the raster alone.

You MUST NOT penalise:

  - Variable renaming (s for ship, c for class, etc.).
  - Schema field ordering when the field set is the same.
  - Conjunction or disjunction ordering inside a predicate.
  - Choice between equivalent quantifier forms (e.g. nested unary
    quantifiers vs Spivey multi-decl "; ; |" form, when both
    type-check).
  - Alternative correct decompositions (e.g., 3NF normalisation
    may differ in which relation owns which attribute as long as
    functional dependencies are preserved).
  - Identifier capitalisation choices.
  - Use of helper abbreviations (== lambda forms) vs inlined
    expressions, as long as the unfolded meaning matches.
  - Page count differences.
  - Comment / prose differences (TEXT: blocks may say the same
    thing in different words).
  - Choice between equivalent rendering forms of the same operator
    (e.g., \bullet vs @ for the predicate spot — both are the Z
    bullet).

------------------------------------------------------------
AXIS B: LAYOUT ACCEPTABILITY
------------------------------------------------------------

Judge this axis on OUR rendered PNG. The instructor's PNG is the
reference for what a "good" rendering looks like in this domain
— a Z-trained reader's calibration, not a pixel target. PASS
when all of the following hold:

  B1. No content crashes the page margin or runs off-page.

  B2. Schema, axdef, and zed environments render as upright boxes
      — visible top and bottom rules, declarations clearly
      separated from where-clause predicates by the schema bar.

  B3. Long mathematical expressions break at operator boundaries
      (after \land, \lor, \implies, \iff, |, =>, the bullet, etc.)
      rather than crashing the right margin. No identifier or
      multi-character operator is split across a forced line
      break.

  B4. Comprehensions and set-builder notation render with visible
      spacing inside {| ... |} and around \bullet / @.

  B5. Proof trees render upright; the conclusion sits visibly
      below the premise(s); inference labels are legible.

  B6. Fonts, sizes, and spacing are consistent with the rest of
      the document — no jarring weight or family changes inside
      math mode. (Different font family between the instructor's
      PDF and ours is acceptable; inconsistency INSIDE ours is
      not.)

  B7. Operators that fuzz.sty renders as sans-serif keywords (div,
      mod, etc.) have visible spacing on both sides; they do not
      run together with neighbouring identifiers.

FAIL this axis when any of B1–B7 fails on our rendered PNG. Pixel
parity with the instructor is NOT required and NOT a criterion;
the question is whether a Z-trained reader would accept our PNG
as a clean submission. Differences in font family, engine, and
placement between the two PNGs are expected and do not in
themselves fail B1–B7.

UNCLEAR this axis when our PNG is missing, corrupted, or the
relevant region is cropped out.

You MUST NOT penalise:

  - Different LaTeX engines producing different inter-paragraph
    spacing.
  - Different font families between the instructor's render and
    ours.
  - Page break positions differing from the instructor's.
  - Section numbering style or chapter heading style.
  - Whitespace at the top or bottom of the page.

------------------------------------------------------------
DISPOSITION MATRIX
------------------------------------------------------------

   Axis A    Axis B    overall verdict
   ------    ------    ----------------
   pass      pass      pass
   pass      fail      needs-fix
   pass      unclear   needs-fix
   fail      pass      needs-fix
   fail      fail      needs-fix
   fail      unclear   needs-fix
   unclear   pass      needs-fix (request clearer text input)
   unclear   fail      needs-fix
   unclear   unclear   needs-fix (request both clearer inputs)

The verdict `out-of-scope` is reserved for the inner-loop driver,
not the judge. The judge never emits `out-of-scope`.

------------------------------------------------------------
RECOMMENDATIONS
------------------------------------------------------------

When the verdict is `needs-fix`, the `recommendations` list MUST
contain at least one item. Each item should be:

  - Concrete: name the specific construct, schema, line, or
    operator that is off.
  - Actionable: state what change in our .txt would address it.
  - Sourced: if you are recommending a change because of a layout
    issue visible only in the PNG, say so explicitly so the
    inner-loop driver knows which artifact to inspect.

Do not recommend cosmetic changes that have no rubric basis. Do
not recommend changes to the engine code — that is the
inner-loop driver's call (§7.2 of the verification procedure).

------------------------------------------------------------
OUTPUT SCHEMA (verbatim YAML — no markdown fence)
------------------------------------------------------------

Your final output is ONLY the YAML block below, with no preceding
or trailing prose. The inner-loop driver parses it
programmatically.

verdict: pass | needs-fix
semantic_equivalence:
  status: pass | fail | unclear
  observations:
    - <one short observation per axis A point worth noting>
  failed_criteria:
    - A1 | A2 | A3 | A4 | A5 | A6   # omit key if status is pass
layout_acceptable:
  status: pass | fail | unclear
  observations:
    - <one short observation per axis B point worth noting>
  failed_criteria:
    - B1 | B2 | B3 | B4 | B5 | B6 | B7   # omit key if status is pass
recommendations:
  - <one actionable change in our .txt, if verdict is needs-fix>
confidence: 0.00..1.00
notes: |
  <any free-text caveat or observation that does not fit above —
   especially: ambiguity in the instructor solution, missing
   inputs, or your reasoning when confidence is below 0.85>
```

---

## Calibration notes (for the inner-loop driver)

The judge is a fallible model. Two calibration practices keep it
honest:

1. **Cross-check the first three questions per course by hand.**
   Compare the human verdict to the judge verdict on a fresh
   sheet. If the judge is systematically generous or systematically
   harsh on this course's style, adjust the rubric phrasing before
   delegating in bulk.
2. **Track the override rate.** Per
   `verification-procedure.md` §11, record how often human review
   overrules the judge below the 0.85 threshold. If the override
   rate is < 5%, raise the threshold to 0.90. If it climbs above
   20%, the rubric needs work.

---

## Example invocation (DAT Exercise 2, Q5(c))

This is a worked example, not the live invocation — for orientation
only.

```python
Agent(
  subagent_type="general-purpose",
  description="Judge DAT-ex2-Q5c",
  prompt="""You are an LLM judge evaluating ... [full template
  with these substitutions]:

    course_name_long: Database Architecture & Theory
    course_short: DAT
    sheet: 2
    Q: 5
    X: (c)
    instructor_question_path:
      /Users/jfreeman/Coding/course-ox-dat/exercises/exercises2.txt
    instructor_solution_text_path: null
    instructor_solution_image_paths:
      /Users/jfreeman/Coding/course-ox-dat/exercises/_pages/exercises2-08.png
    our_txt_excerpt_path:
      /Users/jfreeman/Coding/course-ox-dat/exercises-worked/solutions-ex2.txt
    our_tex_excerpt_path:
      /Users/jfreeman/Coding/course-ox-dat/exercises-worked/solutions-ex2.tex
    our_solution_image_paths:
      /Users/jfreeman/Coding/course-ox-dat/exercises-worked/_pages/solutions-ex2-09.png

  Return only the YAML verdict block."""
)
```

The judge would read the six files, evaluate the two axes, and
return a single YAML block. The inner-loop driver writes it to
`~/Coding/course-ox-dat/verdicts/ex2-q5c-r1.yaml`, then acts on
`verdict` per §5.5.

---

## Author guidance prompt (companion)

When the verdict is `needs-fix` and the inner-loop driver chooses
to delegate the fix-and-rebuild work to a separate authoring
agent, use the skeleton at
[docs/development/author-prompt.md](author-prompt.md) (to be
authored). For most questions the inner-loop driver edits the
`.txt` directly; the author prompt is only needed for batch
fix-ups.
