# Plan: Parser-backed inline math in `TEXT:` (Option 3)

**Status:** proposed (awaiting execution)
**Type:** T1 — cross-cutting architecture change + breaking migration
**Owner:** jra (principal); jms (semantics), rmh (engine/tests), ghr (docs), adb (regeneration)

## Motivation

`TEXT:` prose currently *auto-detects* math in undelimited English — deciding
whether `filter` is a word or an operator, whether `|` is "or" or `\mid`. That
detection is ~1000 lines of regex heuristics (≈15 functions in
`src/txt2tex/codegen/text_pipeline.py`, lines ~697–1740) and is *fundamentally*
unable to be robust: the ambiguity is inherent to guessing math in free prose.
It has produced real bugs (the `\mu`/`\mid` half-conversion; `$...$` mangling of
backslash commands; `P`→`\power` over-conversion).

txt2tex already owns the one robust thing needed: a real lexer → parser →
generator that turns whiteboard notation into LaTeX. Inline prose math should
reuse *that*, behind an explicit delimiter — not a second, regex-based math
engine.

## Design of record

- **`$...$` in `TEXT:` is the explicit inline-math delimiter. Its content is
  whiteboard notation, routed through the real lexer/parser/generator** (the
  same engine as `zed`/`axdef`/`schema` blocks), wrapped in `$...$`.
- **Prose outside `$...$` is escaped verbatim.** No auto-detection. English
  words that happen to be operators (`filter`, `or`) render as plain English.
- **`$...$` is strictly whiteboard.** Raw LaTeX goes through `LATEX:`; verbatim
  goes through `PURETEXT:`. One rule per tier, no overlap.

| Block | Contents | Engine |
|-------|----------|--------|
| `TEXT:` | prose; math in `$...$` | prose escaped; `$...$` → real parser |
| `PURETEXT:` | verbatim | escape only |
| `LATEX:` | raw LaTeX | passthrough |

This meets the project goal — users write **whiteboard notation, never LaTeX**
(`$forall x : X | P$`, not `$\forall x @ P$`) — while being robust (delimited +
parsed, no guessing) and far simpler (delete the heuristics).

## Invariant the change must preserve

Every committed `.tex`/`.pdf` that renders correctly today must still render
correctly after migration — no document loses fidelity. The migration makes each
existing `TEXT:` block's math *explicit*; it does not change meaning.

## Phases

### Phase 0 — jms consult (semantics)

Confirm before any code:

1. Routing a `$...$` span through the expression parser + generator yields the
   same LaTeX a math block would for the same source.
2. **Inline context flag.** Inline `$...$` is NOT a Z paragraph, so the codegen
   must run with `_in_z_paragraph = False` (e.g. `o9` → `\semi` not `\comp`;
   check `\power`, spacing). Confirm the correct flag state for the inline path.
3. Which constructs are legal inline (expressions: yes; paragraph-level
   constructs like `schema`/`axdef`: no) and the error to raise otherwise.

### Phase 0 findings (jms, DONE)

- Inline path must use `_in_z_paragraph = False` — necessary and sufficient.
  Only 3 generator sites branch on it: `o9`→`\semi` (`expressions.py:281`), and
  two comprehension line-break sites (`914`, `959-961`) that are unreachable
  inline (the `$...$` matcher forbids newlines). Current code already sets
  `False` in the `$...$` routing (the `_process_explicit_dollar_math` /
  inline-math path in `text_pipeline.py`).
- The `$...$` path already routes content through the real parser and gates on
  `isinstance(ast, Expr)`; on the `else` it silently passes the span through.
  Under strict mode, change that to **raise** (paragraph construct in `$...$`).
- Legal-inline boundary is `Parser.parse()`'s return type: `Expr` = legal;
  `Document` (schema/axdef/gendef/given/`::=`/`==`) = raise with a clear message.
- One entry point: `Parser(tokens).parse()`. Predicates and expressions both
  return `Expr`; no caller-side disambiguation.
- Strict `$...$`: delete the allow/block/unknown backslash classification
  (the `_classify_latex_commands` allow/block logic in the `$...$` routing);
  a `\`+letter LaTeX command in `$...$` → raise (the bare `\` set-difference
  operator stays valid whiteboard).
- `\power`/`\mu`/`@`/decorations are flag-independent — no inline-specific work.

### Phase 1 — rmh: parser-backed `$...$` (additive, behind the seam)

- In `text_pipeline.py`, replace the *content conversion* inside
  `_process_explicit_dollar_math` (and `_process_inline_math`) with a call into
  the existing engine: lex the span → parse as an expression → generate LaTeX
  (with the inline flag from Phase 0) → wrap in `$...$`.
- Reuse the existing lexer/parser/generator; do NOT write a new parser.
- Keep the bare-prose heuristics in place for now (delete in Phase 2) so the
  suite stays green while the new path lands.
- Tests: `$whiteboard$` → the exact LaTeX the math-block engine produces
  (`forall`→`\forall`, `land`→`\land`, `+->`→`\pfun`, `mu t : T | P . e`→…).
  Assert on emitted fragments.

### Phase 2 — rmh: delete bare-prose auto-detection

- Remove the ~15 heuristics: `_process_logical_formulas`,
  `_process_parenthesized_logic`, `_process_quantifiers`,
  `_process_set_expressions`, `_process_type_declarations`,
  `_process_function_applications`, `_process_relational_image`,
  `_process_superscripts`, `_process_standalone_keywords`,
  `_process_simple_expressions`, `_convert_comparison_operators`,
  `_convert_sequence_literals`, `_convert_operators_bare`,
  `_convert_unicode_symbols` (assess), and their orchestration in
  `_process_paragraph_text`.
- Keep: `$...$` extraction/routing, `_escape_latex` /
  `_escape_special_chars_outside_math`, `_process_citations`,
  `_process_manual_markup`. The dollar-sanitise machinery likely shrinks (content
  is parsed, not regex-scanned).
- Bare prose is now escape-only. This intentionally BREAKS every `TEXT:` block
  that relied on bare-math detection — that is the migration surface, handled in
  Phase 3. Rewrite the pipeline unit tests to the new model.
- Target: ~1000 lines removed from `text_pipeline.py`.

### Phase 3 — migration (the "proper list"): manual, one file at a time

74 example files and ~40 test files use `TEXT:`. **Source edits are made by
hand, one file at a time, with the Edit tool — NEVER with `sed`, a rewrite
script, `awk`, `perl -i`, or any batch process.** Batch rewriting of these
`.txt` sources has corrupted ("royally horked") files before; it is prohibited
here without exception. Automation is confined to *diagnosis* and *verification*
— never to *editing the sources*.

1. **Diagnostic harness (read-only).** A throwaway script runs the OLD pipeline
   and the NEW (escape-only + `$...$`) pipeline on each `TEXT:` block and REPORTS
   the runs the old pipeline auto-converted — i.e. the exact spans that need
   `$...$`. It writes nothing to any source; it only produces a per-file list of
   candidate spans.
2. **Manual wrapping.** For each file, read the report and the block, then wrap
   each genuine-math run in `$...$` using the Edit tool, reviewing the change in
   context — so a genuine English `->` or `|` is left as prose, not wrapped. One
   file, reviewed, before the next.
3. **Verify per file.** After a file's edits, regenerate its `.tex`/`.pdf` (adb)
   and confirm: output matches the old (or an intentional improvement), fuzz
   passes where applicable, and the PDF compiles. Only then move on.
4. Spot-check a sample visually to confirm no fidelity loss.

The migration is deliberately slow and per-file. Speed here is a false economy —
a corrupted source costs far more than a careful pass. No batch edits, ever.

### Phase 4 — docs: ghr + jra

- `USER_GUIDE.md`: rewrite the `TEXT:` section — the three-tier model; `$...$` =
  inline whiteboard math (with examples); `PURETEXT:` verbatim; `LATEX:` raw.
  State plainly: **no LaTeX needed; write whiteboard inside `$...$`.**
- `docs/DESIGN.md`: ADR — reject bare-prose auto-detection (unbounded ambiguity);
  choose delimited whiteboard inline math via the real parser.
- `FUZZ_VS_STD_LATEX.md`: note inline `$...$` uses the inline (non-Z-paragraph)
  codegen path.
- `CHANGELOG.md`: **breaking change** — `TEXT:` no longer auto-detects bare math;
  wrap inline math in `$...$`.

### Phase 5 — release: adb

Breaking change → **major version bump**. Follow the release workflow.

## Testing strategy

- **Inline math:** `$…whiteboard…$` → the same LaTeX the math-block engine emits
  (assert exact fragments).
- **Prose robustness (the win):** "you can filter the results or sort them" →
  plain English, NO `\filter`/`\lor`. Demonstrate the ambiguity is gone.
- **The mu case:** `$mu t : T | t.tier = 1 . t.venue$` → correct; a literal LaTeX
  snippet → `PURETEXT:` or `LATEX:`.
- **Every migrated example:** fuzz (where applicable) + PDF compile + spot visual.
- Rewrite the ~40 pipeline test files to the new model; each asserts actual
  output.

## Risks / open decisions

- **Strict `$...$` (whiteboard only).** DECIDED (jfreeman): `$...$` accepts
  whiteboard notation only; raw LaTeX must go through `LATEX:`. One rule, no
  ambiguity. A backslash command inside `$...$` is an error, not passthrough.
- **Over-wrapping in migration.** The diff-driven approach prevents wrapping
  genuine prose punctuation; verify no false positives on a sample.
- **Scale.** 74 + 40 files — large but mechanical and verifiable via the diff
  harness.
- **`_in_z_paragraph` inline state** (Phase 0) — must be correct or inline `o9`,
  `\power`, spacing differ from intent.

## Success criteria

- `TEXT:` prose never converts English words; inline math only via `$...$`
  (whiteboard).
- ≈1000 lines removed from `text_pipeline.py`.
- Every example type-checks (where applicable) and its PDF compiles.
- Zero "Missing `$`" / backslash-mangling / over-conversion bugs.
- A user needs zero LaTeX knowledge to present math in prose.
