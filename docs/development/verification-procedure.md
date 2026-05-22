# Verification Procedure: Reproducing Instructor Solutions

**Status:** Active on the courseware staging branch. Do not merge to
`jmf-pobox/txt2tex` `main` without explicit student sign-off — this
procedure references course material (SEM / SBM / DAT) that the
isolation rule keeps out of the public repo. See
[memory: courseware-fork-isolation] and
[CLAUDE.md](../../CLAUDE.md).

---

## 1. Purpose

Establish full confidence in the `.txt → .tex → .pdf` pipeline by
demonstrating that, for the Oxford courses currently used as
ground truth (SEM — Software Engineering Mathematics; SBM —
Schema-Based Modelling; DAT — Database Architecture & Theory), the
generated solution PDFs are **equivalent in meaning and acceptable
in layout** to instructor-provided solutions across every question.

This is the project's exit gate for the engine work in
`feat/phase-3-2-schema-calculus`. Until the gate is met course by
course, the public release on `jmf-pobox/txt2tex` is not advanced.

## 2. Scope

Three courses, every exercise sheet, every question.

| Course | Working tree | Exercises | Notes |
|--------|--------------|-----------|-------|
| SEM    | `~/Coding/course-ox-sem/`  | All published sheets | Foundations: predicate logic, sets, relations, schemas |
| SBM    | (forthcoming working tree) | All published sheets | Schema calculus and refinement |
| DAT    | `~/Coding/course-ox-dat/`  | All published sheets | Relational model, algebra, calculus, normalisation, FK |

A question is **in scope** if the instructor's solution can be
expressed in Z-style mathematical notation. Free-text discussion
prose is in scope too — txt2tex emits `TEXT:` and `LATEX:` blocks
for it.

A question is **out of scope** only if the instructor's solution is
intrinsically not Z-expressible — a hand-drawn diagram that *is* the
answer, free-text discussion that is itself the deliverable, an
artifact from outside the engine's notation target. "We have not
implemented that construct yet" is **not** an out-of-scope reason; it
is an engine work item under §7.3. Out-of-scope determination is made
in §5.1 before authoring begins, not as an escape hatch for a
difficult row.

## 3. Definitions

**Equivalence.** Two solutions are equivalent when a Z-trained
reader would judge them to make the same mathematical statement.
Equivalent solutions need not be identical: different variable
names, alternative but logically equivalent predicate forms,
permuted conjunction order, and alternative schema decompositions
are all admissible.

**The PNG is the authoritative deliverable.** Students turn in a
PNG (or a PDF rendered to PNGs page-by-page). The PNG is the
artifact being graded by the instructor. Therefore:

- The `.txt`, the `.tex`, and the `.pdf` are intermediate.
- The PNG is what verification ultimately measures.
- The judgment is made on the PNG, with the source `.txt` / `.tex`
  available only as supporting evidence — never as a substitute.

**Layout acceptable.** The PNG is layout-acceptable when:

- No overfull / underfull box visibly cuts into a margin.
- Schema boxes, axdef boxes, comprehensions, quantifiers, and proof
  trees render upright and well-spaced — not as "blob runs."
- Mathematical operators have the expected typographic weight and
  spacing for a Z document (sans-serif `div`, italic identifiers,
  upright keywords, proper bullet `\bullet` / spot `@`).
- Long lines break at logical points (after operators, after `|`,
  after `=>`, etc.) rather than crashing the right margin.

**The PNG comparison is qualitative, not automated.** It is the
judgment a human grader would make looking at the two images side
by side. Pixel-level diffs (e.g. `imagemagick compare -metric AE`,
structural-similarity scores) are **not** used and should not be
substituted. Different LaTeX engines, different fonts, and minor
placement differences are expected; the question is whether the
two PNGs read the same to a Z-trained reader.

**Judge.** Equivalence and layout are decided by an LLM acting as
judge, with the rubric in §6. The judge operates on the **PNG
pair** (instructor + ours) as primary evidence, with the text
sources available as supporting context. A judgment based only on
text — without seeing both PNGs — is not valid and must not be
recorded.

## 4. Outer Loop (per course)

For each course `C` in {SEM, SBM, DAT}:

1. **Establish the source set.** Locate the official exercise sheets
   and instructor solutions in `~/Coding/course-ox-<c>/exercises/`
   (or equivalent). Verify every sheet is present.
2. **Build the question manifest.** Enumerate every question into a
   tracking file `~/Coding/course-ox-<c>/verification.tsv` with
   columns:

   ```text
   sheet  q  subq  source_page  status  disposition  notes_path
   ```

   Initial status is `pending`. Disposition is empty until §5
   completes. The parser at `.tmp/build_manifest.py` extracts the
   manifest from a `pdftotext -layout` dump:

   ```bash
   uv run python .tmp/build_manifest.py \
     ~/Coding/course-ox-<c>/exercises/exercises.txt \
     --out ~/Coding/course-ox-<c>/verification.tsv
   ```

   For multi-sheet courses (DAT has `exercises1.pdf` and
   `exercises2.pdf`), run once per sheet with `--sheet <N>` and
   concatenate. Only leaf rows are emitted — when an exercise has
   nested sub-parts `(a) (i) (ii) ...`, the umbrella `(a)` row is
   suppressed in favour of `a-i`, `a-ii`, etc. Single-part
   exercises emit one row with `subq=""`.
3. **Iterate the inner loop (§5) over the manifest** until every
   row has a terminal disposition (`pass` or `out-of-scope`).
4. **Course-level pass criteria** — see §9.
5. **Sign-off.** When the course passes, record the date and the
   commit hash in the manifest header and write a single course-
   verification memo under `~/Coding/course-ox-<c>/SIGN-OFF.md`.

## 5. Inner Loop (per question)

For each row of the manifest:

### 5.1 Read

- Open the instructor's question text.
- Open the instructor's solution.
- Decide tentatively whether the question is in scope (§2). If
  out-of-scope, set `disposition=out-of-scope`, write reason in
  `notes_path`, move to next row.

### 5.2 Author the txt2tex source

- Create or extend a `.txt` file under
  `~/Coding/course-ox-<c>/exercises-worked/solutions-<sheet>.txt`.
- Match the section / question header convention already used in
  that file. Use the project's `=== Question N ===` and `(a) (b)
  (c)` separator forms.
- Author the solution in whiteboard Z syntax. Honour the project
  rules: zero `LATEX:` escape blocks unless absolutely necessary,
  `lnot` not `not`, `\t1` not `\quad`, `==` for abbreviations,
  multi-decl Spivey form for chained quantifiers, etc.
  See [USER_GUIDE.md](../guides/USER_GUIDE.md) and
  [FUZZ_VS_STD_LATEX.md](../guides/FUZZ_VS_STD_LATEX.md).

### 5.3 Build

From the working directory of the course:

```bash
uv run --project ~/Coding/txt2tex txt2tex \
  ~/Coding/course-ox-<c>/exercises-worked/solutions-<sheet>.txt
```

Required outcomes:

- `Type checking: passed` (fuzz typecheck must be clean for the
  question's portion of the file).
- `Generated: solutions-<sheet>.pdf`.
- No overfull-box warning attributable to this question's content
  (run the build with the project's overflow detector active).

If any of these fail, the question is **not yet ready for judge.**
Diagnose; revise the `.txt`; rebuild. Treat fuzz rejection as a
real bug in the authored solution — usually a notation
ambiguity, not a typechecker false positive. If a typechecker
false positive is genuinely suspected, consult jms before
working around it.

### 5.4 Render to PNG

This step is **mandatory** and produces the artifact the judge
actually evaluates. The PNG is what a student submits and what the
instructor grades; the `.tex` and `.pdf` are intermediates, the PNG
is the deliverable.

Render our PDF at 200 DPI, one PNG per page:

```bash
pdftoppm -r 200 -png \
  ~/Coding/course-ox-<c>/exercises-worked/solutions-<sheet>.pdf \
  ~/Coding/course-ox-<c>/exercises-worked/_pages/solutions-<sheet>
```

This produces `solutions-<sheet>-NN.png` (one per page,
1-indexed). Render the instructor's PDF the same way at the same
DPI for side-by-side comparison:

```bash
pdftoppm -r 200 -png \
  ~/Coding/course-ox-<c>/exercises/solutions-<sheet>.pdf \
  ~/Coding/course-ox-<c>/exercises/_pages/solutions-<sheet>
```

Identify the pages that contain the question under review. Multi-
page questions list every relevant page. Both PNG sets are inputs
to §5.5; the judge sees both and decides on the basis of the pair.

Do **not** run pixel-level or perceptual-diff tools as a substitute
for the judge. The comparison is qualitative (§3); automating it
at the pixel level produces noise on font / engine / spacing
differences that the rubric explicitly does not penalise.

### 5.5 Judge

Spawn an LLM-judge agent (see §6) with:

- The instructor's source (question text + solution text).
- The instructor's solution PNG(s).
- The generated `.tex` excerpt for the question.
- The generated solution PNG(s).
- The rubric (§6).

The judge returns a structured verdict:

```yaml
verdict: pass | needs-fix | out-of-scope
semantic_equivalence: pass | fail | unclear
layout_acceptable: pass | fail | unclear
observations:
  - <free-text observation about meaning>
  - <free-text observation about layout>
recommendations:
  - <if needs-fix: specific change suggestion>
confidence: 0..1
```

The verdict and `confidence` together determine the next step:

| Verdict       | Confidence | Action |
|---------------|------------|--------|
| `pass`        | ≥ 0.85     | Mark row `pass`. Done. |
| `pass`        | < 0.85     | Human spot-check before marking `pass`. |
| `needs-fix`   | any        | Apply recommendations; rebuild; re-judge. |
| `out-of-scope`| any        | Mark `out-of-scope` with reason. |

### 5.6 Iterate or Accept

If `needs-fix`, revise `.txt` (and/or escalate a true engine bug
via a mission contract to rmh — do not silently work around an
engine defect). Re-run from §5.3. Maximum **5 rounds** per
question; if not converged, escalate to the student.

When an authoring fix is applied, also check the relevant
documentation. If the fix was prompted by surprise at how the
engine treats a construct, the surprise is itself a doc defect —
update the user guide, syntax reference, or tutorial so that the
next author does not hit the same surprise. The verification round
is not complete until both the source and the docs are correct.

When the row reaches `pass` or `out-of-scope`, commit the changes:

```bash
git add ~/Coding/course-ox-<c>/exercises-worked/solutions-<sheet>.{txt,tex,pdf}
git commit -m "verify(<c>-<sheet>): Q<n> <subq> <pass|out-of-scope>"
```

Then move to the next row.

## 6. LLM-as-Judge Specification

### 6.1 Rubric

**Semantic equivalence rubric — pass when ALL hold:**

1. Every quantifier (`forall`, `exists`, `exists1`, `mu`, `lambda`)
   in the instructor's solution has a corresponding quantifier in
   ours over equivalent domains.
2. Every schema in the instructor's solution has a corresponding
   schema in ours with the same primary key and same set of fields
   (modulo renaming and ordering).
3. Predicate logic statements are logically equivalent under
   classical propositional + first-order rewriting (de Morgan,
   contraposition, predicate distribution over conjunction, etc.).
4. Cross-schema invariants (zed paragraphs / FK statements / global
   constraints) are present in ours when present in the
   instructor's, and they capture the same property.
5. Numerical answers (counts, ranges, marks) match exactly.

**Layout-acceptable rubric — pass when ALL hold:**

1. No content crashes the page margin.
2. Schema / axdef / zed boxes render as boxes — not as collapsed
   strips with overlapping lines.
3. Long mathematical expressions break at operator boundaries; no
   identifier or operator is split across a forced line break.
4. Comprehensions and set-builder notation render with visible
   spacing inside `{|...|}` and around `\bullet` / `@`.
5. Proof trees render upright and the conclusion is visibly below
   the premises.
6. Fonts, sizes, and spacing are consistent with the rest of the
   document — no jarring weight or family changes inside math mode.

### 6.2 What the judge does NOT penalise

- Variable renaming (`s` for `ship`, `c` for `class`, etc.).
- Schema field ordering when the field set is the same.
- Conjunction ordering inside a predicate.
- Choice between equivalent quantifier forms (e.g. nested unary
  quantifiers vs Spivey multi-decl `; ; |` form, when both
  type-check).
- Alternative correct decompositions (e.g., 3NF normalisations can
  differ in which relation owns which attribute).
- Choice of identifier capitalisation.
- Page count differences.
- Font family differences between the engines used.

### 6.3 Judge prompt skeleton

A reusable prompt for the judge agent lives at
`docs/development/judge-prompt.md` (to be authored alongside this
procedure). It is parameterised by `<course>`, `<sheet>`,
`<question>`, and reads the rubric (§6.1) and the
non-penalty list (§6.2) inline.

### 6.4 Judge model

The judge runs as a sub-agent in the main session. It is not given
write access to the working tree; it returns the YAML verdict only.
The human reviewer (the student) decides whether to apply
`recommendations` or to override.

## 7. Triage & Escalation

**The course-level bar is 100% pass.** Every row whose instructor
solution is Z-expressible must end at `pass`. "Notation gap" is not
an escape from the bar — it is an engine work item. "Out of scope"
is reserved for solutions that intrinsically cannot be expressed in
the engine's target notation (hand-drawn diagrams, free-text
discussion that is itself the answer, etc.), and that determination
is made up front in §5.1 before authoring — not as a disposition for
a question that turned out to be hard.

The inner loop can produce four kinds of finding:

1. **Authoring error.** Our `.txt` is wrong relative to the
   instructor's solution. Fix the `.txt`. **Then verify the
   documentation.** If the authoring fix was prompted by surprise at
   how the engine treats a construct — operator behaviour, escape
   rule, block syntax — the relevant guide
   (`USER_GUIDE.md`, `PROOF_SYNTAX.md`, `FUZZ_VS_STD_LATEX.md`, the
   tutorials) must state the rule clearly. If it does not, the docs
   are themselves a defect and must be updated in the same change.
2. **Engine defect.** Our notation is correct but the engine
   renders or typechecks it badly. Write a mission contract for
   rmh; cite the failing question; pin a regression test based on
   the failing case. Do not work around in the `.txt`.
3. **Notation gap.** Our `.txt` cannot express the instructor's
   solution because the engine does not yet support the needed
   construct. This is an **engine work item**, not an out-of-scope
   disposition. Add an entry to
   [docs/guides/MISSING_FEATURES.md](../guides/MISSING_FEATURES.md),
   write a mission contract to close the gap, and drive the row to
   `pass` once the engine work lands. The row stays in
   `needs-fix` (or `pending` if not yet attempted) until then; it
   does not get marked `out-of-scope`.
4. **Instructor error or ambiguity.** Rare, but it happens. Record
   in `notes_path`; mark `pass` with a comment; consult the
   student before claiming the instructor is wrong.

Engine defects (category 2) and notation gaps (category 3) both
block the course-level pass until closed, because they are the very
thing the verification is meant to catch.

## 8. Tracking Artifacts

Per course, in `~/Coding/course-ox-<c>/`:

- `exercises/` — the instructor-provided source material: source
  PDFs, `pdftotext -layout` dumps as `.txt`, and a `_pages/`
  subdirectory containing one PNG per page rendered at 200 DPI.
- `verification.tsv` — the manifest. One row per question / sub-
  question. Status transitions: `pending → in-progress → pass |
  needs-fix | out-of-scope`.
- `exercises-worked/` — authored `.txt`, generated `.tex` and
  `.pdf`, plus a `_pages/` raster directory of our rendered output.
- `verdicts/` — one YAML file per question / round, named
  `<sheet>-q<n><subq>-r<round>.yaml`, containing the judge's
  verdict from §5.5.
- `SIGN-OFF.md` — final attestation when the course passes.

Per the courseware isolation rule, none of the per-course
directories live in `jmf-pobox/txt2tex`; they live next to the
engine repo, not inside it. The instructor's source PDFs and any
proprietary course material must not leave the per-course
directory.

**Current scale (manifest counts as of 2026-05-21):**

| Course | Exercises | Leaf rows in manifest |
|--------|-----------|------------------------|
| SEM    | 53 (Ex 1–52 + one unnumbered "final modelling question") | 183 |
| SBM    | 33 (Ex 1–21 and 23–34; Ex 22 absent from the source) | 75 |
| DAT    | 10 (Sheet 1: Q 1–5; Sheet 2: Q 1–5)                 | 21  |

Total: 279 leaf rows.

## 9. Definition of Done

**Per question:** the manifest row is `pass` or `out-of-scope`
with a recorded reason.

**Per course:**

- **100% of rows that were Z-expressible at the time of authoring
  reach `pass`.** Engine-side fixes (§7.2) and notation-gap closures
  (§7.3) are completed; authoring fixes (§7.1) are applied; the
  manifest shows zero `needs-fix` rows.
- The only rows permitted to end at `out-of-scope` are those
  classified as not Z-expressible in §5.1, before authoring. Each
  such row records the structural reason (hand-drawn artifact, etc.)
  in `notes_path`.
- Every engine-defect finding (§7.2) is fixed and every notation-gap
  finding (§7.3) is closed with the affected questions at `pass`.
- Every authoring fix (§7.1) was accompanied by a documentation
  review; any user-guide / tutorial defect surfaced during
  verification is fixed in the same branch.
- A `SIGN-OFF.md` exists, dated, citing the engine commit hash
  used for the final pass.

**Engine-wide (release gate):**

- All three courses (SEM, SBM, DAT) are signed off.
- No engine defect found during verification is still open.
- The full test suite (`make check`) passes on the engine commit
  named in every course's `SIGN-OFF.md`.
- A summary memo `docs/development/verification-summary.md` is
  authored, listing each course's date, commit, question count,
  pass count, and out-of-scope count.

Only then is the branch eligible for merge / cherry-pick to
`jmf-pobox/txt2tex` `main`.

## 10. Practical Notes

### 10.1 Inner-loop cycle time

Authoring + build + render + judge should take 5–15 minutes per
straightforward question, more for complex multi-part questions.
Budget accordingly; this is a multi-week effort across the three
courses.

### 10.2 Parallelism

The inner loop within a sheet is mostly independent across
questions — but build conflicts can arise if two parallel inner
loops touch the same `solutions-<sheet>.txt`. Prefer one question
per `.txt` file, or batch sequentially within a sheet.

### 10.3 Engine drift during verification

If the engine changes mid-course (e.g. an rmh-led fix from §7.2),
previously-passed questions must be re-built and quickly
re-rendered. Re-judging is only required when the visual output
changed; a content-equivalent regenerate that produces a byte-
identical PNG can be marked `pass` without re-running the judge.

### 10.4 Authoring discipline

Resist the temptation to "match the instructor's exact layout."
Match the instructor's **meaning**. The judge rewards equivalence,
not pixel parity. Over-engineering layout to imitate the instructor
hides engine defects that would otherwise surface on the next
question.

### 10.5 Repository discipline reminder

All verification commits land on the courseware-staging fork
(`courseware` remote in this working tree), not on `origin`. See
[memory: courseware-fork-isolation].

## 11. Open Questions

- **Tooling for the manifest.** TSV is the floor; a richer schema
  (e.g. a small Z spec for `verification.tsv` itself) could be
  type-checked. Defer until v2 of the procedure.
- **Judge calibration.** The 0.85 confidence threshold in §5.5 is
  a guess. Track judge confidence vs human override rate over the
  first sheet of each course; revise.

---

**Author:** jra (txt2tex principal). Reviewers prior to first use:
ghr (documentation tone), mdm (CLI commands cited in §5.3 and §5.4),
the student (procedure fitness).
