# Complexity Report

_Generated 2026-07-04T22:04:19+00:00 at commit `dde0216`._

This snapshot is produced by `make complexity-report` (see `scripts/complexity_report.py`).  It composes radon, lizard, pydeps, and wily into a point-in-time view of the codebase plus a trend window if a wily history exists.

## Maintainability Index (radon mi)

Lower = harder to maintain.  Grades: A >= 20, B 10-19, C < 10.

| File | MI | Grade |
|------|---:|:-----:|
| `src/txt2tex/lexer.py` | 0.00 | C |
| `src/txt2tex/parser_pkg/expressions.py` | 0.00 | C |
| `src/txt2tex/codegen/expressions.py` | 20.36 | A |
| `src/txt2tex/codegen/proofs.py` | 27.89 | A |
| `src/txt2tex/ast_nodes.py` | 28.81 | A |
| `src/txt2tex/latex_gen.py` | 33.09 | A |
| `src/txt2tex/parser.py` | 33.93 | A |
| `src/txt2tex/parser_pkg/text_blocks.py` | 39.75 | A |
| `src/txt2tex/parser_pkg/paragraphs.py` | 40.57 | A |
| `src/txt2tex/parser_pkg/proofs.py` | 41.92 | A |
| `src/txt2tex/codegen/paragraphs.py` | 42.78 | A |
| `src/txt2tex/parser_pkg/schemas.py` | 45.91 | A |
| `src/txt2tex/codegen/text_blocks.py` | 46.51 | A |
| `src/txt2tex/cli.py` | 46.60 | A |
| `src/txt2tex/parser_pkg/algebra.py` | 47.32 | A |
| `src/txt2tex/codegen/text_pipeline.py` | 51.75 | A |
| `src/txt2tex/codegen/schemas.py` | 52.65 | A |
| `src/txt2tex/free_vars.py` | 54.21 | A |
| `src/txt2tex/repl.py` | 56.12 | A |
| `src/txt2tex/compile.py` | 60.70 | A |
| `src/txt2tex/codegen/_dispatch.py` | 66.10 | A |
| `src/txt2tex/codegen/paren_policy.py` | 67.09 | A |
| `src/txt2tex/parser_pkg/lexer_state.py` | 68.07 | A |
| `src/txt2tex/codegen/fuzz_routing.py` | 70.75 | A |
| `src/txt2tex/codegen/algebra.py` | 70.92 | A |
| `src/txt2tex/errors.py` | 74.27 | A |
| `src/txt2tex/parser_pkg/types.py` | 77.76 | A |
| `src/txt2tex/codegen/overflow.py` | 78.70 | A |
| `src/txt2tex/codegen/types.py` | 82.20 | A |
| `src/txt2tex/codegen/bindings.py` | 92.32 | A |
| `src/txt2tex/parser_pkg/errors.py` | 93.86 | A |
| `src/txt2tex/codegen/_toc.py` | 98.85 | A |
| `src/txt2tex/constants.py` | 100.00 | A |
| `src/txt2tex/__init__.py` | 100.00 | A |
| `src/txt2tex/__version__.py` | 100.00 | A |
| `src/txt2tex/tokens.py` | 100.00 | A |
| `src/txt2tex/parser_pkg/_base.py` | 100.00 | A |
| `src/txt2tex/parser_pkg/__init__.py` | 100.00 | A |
| `src/txt2tex/codegen/__init__.py` | 100.00 | A |
| `src/txt2tex/codegen/_smoke.py` | 100.00 | A |

## Cyclomatic Complexity ≥ D (radon cc)

Functions / methods with cyclomatic complexity grade D or worse.

| File | Line | Name | CC | Grade |
|------|-----:|------|---:|:-----:|
| `src/txt2tex/lexer.py` | 343 | `Lexer._scan_token` | 192 | F |
| `src/txt2tex/lexer.py` | 1039 | `Lexer._scan_identifier` | 138 | F |
| `src/txt2tex/parser_pkg/expressions.py` | 2195 | `_ExpressionsParser._parse_postfix` | 45 | F |
| `src/txt2tex/codegen/proofs.py` | 308 | `_ProofsCodegen._generate_proof_node_infer` | 37 | E |
| `src/txt2tex/lexer.py` | 230 | `Lexer` | 31 | E |
| `src/txt2tex/parser_pkg/paragraphs.py` | 184 | `_ParagraphsParser._parse_syntax_block` | 30 | D |
| `src/txt2tex/parser_pkg/expressions.py` | 607 | `_ExpressionsParser._parse_quantifier` | 30 | D |
| `src/txt2tex/codegen/text_blocks.py` | 83 | `_TextBlocksCodegen._generate_part` | 30 | D |
| `src/txt2tex/parser_pkg/expressions.py` | 1417 | `_ExpressionsParser._parse_set_comprehension_from_brace` | 29 | D |
| `src/txt2tex/codegen/proofs.py` | 563 | `_ProofsCodegen._generate_complex_assumption_scope` | 29 | D |
| `src/txt2tex/latex_gen.py` | 715 | `LaTeXGenerator._has_line_breaks_structural` | 28 | D |
| `src/txt2tex/parser_pkg/expressions.py` | 1871 | `_ExpressionsParser._parse_cross` | 28 | D |
| `src/txt2tex/parser.py` | 143 | `Parser.parse` | 26 | D |
| `src/txt2tex/parser.py` | 459 | `Parser._parse_document_item` | 26 | D |
| `src/txt2tex/free_vars.py` | 134 | `expr_free_vars` | 25 | D |
| `src/txt2tex/codegen/schemas.py` | 183 | `_SchemasCodegen._generate_schema` | 25 | D |
| `src/txt2tex/cli.py` | 163 | `main` | 24 | D |
| `src/txt2tex/parser_pkg/proofs.py` | 342 | `_ProofsParser._parse_proof_node` | 24 | D |
| `src/txt2tex/parser.py` | 684 | `Parser._parse_declaration_or_inclusion` | 22 | D |
| `src/txt2tex/latex_gen.py` | 544 | `LaTeXGenerator.generate_document` | 22 | D |
| `src/txt2tex/parser_pkg/expressions.py` | 2671 | `_ExpressionsParser._parse_atom` | 22 | D |
| `src/txt2tex/codegen/expressions.py` | 485 | `_ExpressionsCodegen._generate_logical_quantifier` | 22 | D |

## Lizard Warnings (CCN ≥ 20 or NLOC ≥ 100)

_25 function(s) exceed thresholds._

| File | Function | CCN | NLOC | Tokens | Params |
|------|----------|----:|-----:|-------:|-------:|
| `src/txt2tex/lexer.py` | `_scan_token` | 192 | 438 | 3373 | 1 |
| `src/txt2tex/lexer.py` | `_scan_identifier` | 138 | 399 | 2435 | 3 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_postfix` | 45 | 232 | 1127 | 2 |
| `src/txt2tex/codegen/proofs.py` | `_generate_proof_node_infer` | 37 | 100 | 616 | 2 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_set_comprehension_from_brace` | 33 | 142 | 827 | 1 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_quantifier` | 32 | 170 | 978 | 1 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_cross` | 30 | 156 | 821 | 1 |
| `src/txt2tex/codegen/text_blocks.py` | `_generate_part` | 30 | 135 | 905 | 2 |
| `src/txt2tex/parser_pkg/paragraphs.py` | `_parse_syntax_block` | 30 | 96 | 575 | 1 |
| `src/txt2tex/codegen/proofs.py` | `_generate_complex_assumption_scope` | 29 | 107 | 572 | 3 |
| `src/txt2tex/latex_gen.py` | `_has_line_breaks_structural` | 28 | 40 | 343 | 2 |
| `src/txt2tex/parser.py` | `parse` | 26 | 176 | 892 | 1 |
| `src/txt2tex/codegen/schemas.py` | `_generate_schema` | 26 | 121 | 709 | 2 |
| `src/txt2tex/parser.py` | `_parse_document_item` | 26 | 58 | 437 | 1 |
| `src/txt2tex/free_vars.py` | `expr_free_vars` | 25 | 67 | 529 | 1 |
| `src/txt2tex/cli.py` | `main` | 24 | 166 | 740 | 0 |
| `src/txt2tex/parser_pkg/proofs.py` | `_parse_proof_node` | 24 | 84 | 531 | 3 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_atom` | 22 | 130 | 709 | 1 |
| `src/txt2tex/parser.py` | `_parse_declaration_or_inclusion` | 22 | 120 | 644 | 1 |
| `src/txt2tex/codegen/expressions.py` | `_generate_logical_quantifier` | 22 | 72 | 451 | 3 |

_…5 more not shown._

## Module Structure (pydeps)

| Module | Fan-in | Fan-out |
|--------|-------:|--------:|
| `txt2tex` | 34 | 2 |
| `txt2tex.__version__` | 4 | 0 |
| `txt2tex.ast_nodes` | 25 | 0 |
| `txt2tex.cli` | 1 | 11 |
| `txt2tex.codegen` | 18 | 15 |
| `txt2tex.codegen._dispatch` | 15 | 2 |
| `txt2tex.codegen._smoke` | 3 | 3 |
| `txt2tex.codegen._toc` | 2 | 0 |
| `txt2tex.codegen.algebra` | 3 | 4 |
| `txt2tex.codegen.bindings` | 3 | 4 |
| `txt2tex.codegen.expressions` | 3 | 5 |
| `txt2tex.codegen.fuzz_routing` | 3 | 4 |
| `txt2tex.codegen.overflow` | 3 | 3 |
| `txt2tex.codegen.paragraphs` | 5 | 4 |
| `txt2tex.codegen.paren_policy` | 3 | 4 |
| `txt2tex.codegen.proofs` | 3 | 4 |
| `txt2tex.codegen.schemas` | 3 | 4 |
| `txt2tex.codegen.text_blocks` | 3 | 4 |
| `txt2tex.codegen.text_pipeline` | 5 | 6 |
| `txt2tex.codegen.types` | 3 | 4 |
| `txt2tex.compile` | 3 | 0 |
| `txt2tex.constants` | 2 | 0 |
| `txt2tex.errors` | 3 | 0 |
| `txt2tex.free_vars` | 2 | 2 |
| `txt2tex.latex_gen` | 3 | 19 |
| `txt2tex.lexer` | 4 | 2 |
| `txt2tex.parser` | 4 | 14 |
| `txt2tex.parser_pkg` | 12 | 11 |
| `txt2tex.parser_pkg._base` | 11 | 3 |
| `txt2tex.parser_pkg.algebra` | 3 | 5 |
| `txt2tex.parser_pkg.errors` | 3 | 4 |
| `txt2tex.parser_pkg.expressions` | 3 | 6 |
| `txt2tex.parser_pkg.lexer_state` | 3 | 4 |
| `txt2tex.parser_pkg.paragraphs` | 3 | 5 |
| `txt2tex.parser_pkg.proofs` | 3 | 5 |
| `txt2tex.parser_pkg.schemas` | 3 | 5 |
| `txt2tex.parser_pkg.text_blocks` | 3 | 5 |
| `txt2tex.parser_pkg.types` | 3 | 5 |
| `txt2tex.repl` | 2 | 10 |
| `txt2tex.tokens` | 13 | 0 |

## Recent Trend (wily)

LoC and cyclomatic complexity at the **oldest** and **newest** revisions in the wily window.  Files with zero net change in both metrics are omitted.

| File | Oldest commit | Oldest LoC | Oldest CC | Newest commit | Newest LoC | Newest CC | LoC d | CC d |
|------|--------------|-----------:|----------:|---------------|-----------:|----------:|------:|-----:|
| `src/txt2tex/latex_gen.py` | `0606052` (2026-05-19) | 5802 | 771 | `3b80a19` (2026-05-22) | 6815 | 868 | +1013 | +97 |
| `src/txt2tex/parser.py` | `c62874b` (2026-05-18) | 5425 | 794 | `17e0be0` (2026-05-22) | 6280 | 912 | +855 | +118 |
| `src/txt2tex/ast_nodes.py` | `c62874b` (2026-05-18) | 1230 | 69 | `3b80a19` (2026-05-22) | 1427 | 80 | +197 | +11 |
| `src/txt2tex/lexer.py` | `c62874b` (2026-05-18) | 1441 | 346 | `772861d` (2026-05-22) | 1635 | 394 | +194 | +48 |
| `src/txt2tex/tokens.py` | `c62874b` (2026-05-18) | 222 | 4 | `3b80a19` (2026-05-22) | 239 | 4 | +17 | +0 |
| `src/txt2tex/free_vars.py` | `92823b7` (2026-05-20) | 212 | 42 | `17e0be0` (2026-05-22) | 214 | 41 | +2 | -1 |

## Delta vs Prior Snapshot

Prior snapshot: 2026-05-25T08:52:21+00:00 @ `6a31c21`

**MI shifts (Δ ≥ 0.5):**
  src/txt2tex/codegen/expressions.py: MI 22.11 -> 20.36 (↓1.75)
  src/txt2tex/ast_nodes.py: MI 29.32 -> 28.81 (↓0.51)
  src/txt2tex/latex_gen.py: MI 38.89 -> 33.09 (↓5.80)
  src/txt2tex/codegen/paragraphs.py: MI 45.55 -> 42.78 (↓2.77)
  src/txt2tex/codegen/text_blocks.py: MI 47.11 -> 46.51 (↓0.60)
  src/txt2tex/cli.py: MI 47.60 -> 46.60 (↓1.00)
  src/txt2tex/parser_pkg/algebra.py: MI 51.04 -> 47.32 (↓3.72)
  src/txt2tex/codegen/text_pipeline.py: MI 11.90 -> 51.75 (↑39.85)
  src/txt2tex/codegen/schemas.py: MI 57.64 -> 52.65 (↓4.99)
  src/txt2tex/repl.py: MI 56.62 -> 56.12 (↓0.50)
  src/txt2tex/codegen/_dispatch.py: MI 100.00 -> 66.10 (↓33.90)
  src/txt2tex/codegen/fuzz_routing.py: MI 91.61 -> 70.75 (↓20.86)
  src/txt2tex/codegen/algebra.py: MI 74.99 -> 70.92 (↓4.07)

  D-or-worse functions: 23 → 22
  Lizard warnings: 26 → 25

---

_Generated by `scripts/complexity_report.py`.  Both `docs/complexity-report.md` and `docs/complexity-report.json` are committed so future runs can show deltas._
