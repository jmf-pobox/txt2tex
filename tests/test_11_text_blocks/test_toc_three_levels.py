"""Tests for three-level table-of-contents heading hierarchy.

Covers: Section (===), Solution (**), Part (subsection mode) heading
commands and addcontentsline emissions, plus depth filtering via
CONTENTS: keyword and toc_depth_from_keyword.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Contents, Document, Section
from txt2tex.codegen._toc import toc_depth_from_keyword
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _latex(src: str, **kwargs: bool) -> str:
    """Parse src and return generated LaTeX body."""
    lexer = Lexer(src)
    tokens = lexer.tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(**kwargs)
    return gen.generate_document(ast)


# ---------------------------------------------------------------------------
# toc_depth_from_keyword unit tests
# ---------------------------------------------------------------------------


class TestTocDepthFromKeyword:
    """Unit tests for the keyword-to-depth mapping."""

    def test_empty_string_gives_2(self) -> None:
        assert toc_depth_from_keyword("") == 2

    def test_1_gives_1(self) -> None:
        assert toc_depth_from_keyword("1") == 1

    def test_2_gives_2(self) -> None:
        assert toc_depth_from_keyword("2") == 2

    def test_3_gives_3(self) -> None:
        assert toc_depth_from_keyword("3") == 3

    def test_full_gives_3(self) -> None:
        assert toc_depth_from_keyword("full") == 3

    def test_all_gives_3(self) -> None:
        assert toc_depth_from_keyword("all") == 3

    def test_full_case_insensitive(self) -> None:
        assert toc_depth_from_keyword("FULL") == 3

    def test_all_case_insensitive(self) -> None:
        assert toc_depth_from_keyword("ALL") == 3

    def test_2_with_whitespace(self) -> None:
        assert toc_depth_from_keyword("  2  ") == 2

    def test_unrecognised_gives_2(self) -> None:
        assert toc_depth_from_keyword("unknown") == 2


# ---------------------------------------------------------------------------
# Heading command tests (the *starred* heading that appears in output)
# ---------------------------------------------------------------------------


class TestSectionHeadingCommand:
    r"""=== Title === must emit \section*{…}."""

    def test_section_emits_section_star(self) -> None:
        latex = _latex("=== Introduction ===\n")
        lines = latex.splitlines()
        assert r"\section*{Introduction}" in lines

    def test_section_emits_addcontentsline(self) -> None:
        latex = _latex("=== Introduction ===\n")
        lines = latex.splitlines()
        assert r"\addcontentsline{toc}{section}{Introduction}" in lines


class TestSolutionHeadingCommand:
    r"""** Q1 ** must emit \subsection*{…} (not \section*{…})."""

    def test_solution_emits_subsection_star(self) -> None:
        latex = _latex("** Q1 **\n\nx = 1\n")
        lines = latex.splitlines()
        assert r"\subsection*{Q1}" in lines

    def test_solution_emits_addcontentsline_at_subsection(self) -> None:
        latex = _latex("** Q1 **\n\nx = 1\n")
        lines = latex.splitlines()
        assert r"\addcontentsline{toc}{subsection}{Q1}" in lines

    def test_solution_does_not_emit_section_star(self) -> None:
        latex = _latex("** Q1 **\n\nx = 1\n")
        # \section* must not appear for a solution marker
        assert r"\section*{Q1}" not in latex


class TestPartHeadingCommand:
    r"""(a) in subsection mode must emit \subsubsection*{…}."""

    def test_part_emits_subsubsection_star(self) -> None:
        # Top-level part (no enclosing solution) triggers subsection mode
        latex = _latex("(a) Some content\n")
        lines = latex.splitlines()
        assert r"\subsubsection*{(a)}" in lines

    def test_part_emits_addcontentsline_at_subsubsection(self) -> None:
        latex = _latex("(a) Some content\n")
        lines = latex.splitlines()
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" in lines

    def test_part_does_not_emit_subsection_star(self) -> None:
        latex = _latex("(a) Some content\n")
        assert r"\subsection*{(a)}" not in latex


# ---------------------------------------------------------------------------
# Depth filter tests
# ---------------------------------------------------------------------------


class TestDepthFilter:
    """CONTENTS: depth controls which addcontentsline calls are emitted."""

    _FULL_DOC = "CONTENTS: {depth}\n\n=== Title ===\n\n** Q1 **\n\n(a) Part content\n"

    def _latex_for_depth(self, depth_keyword: str) -> str:
        src = self._FULL_DOC.format(depth=depth_keyword)
        return _latex(src)

    # CONTENTS: 1 — explicit depth-1: only section level
    def test_explicit_depth1_section_present(self) -> None:
        latex = self._latex_for_depth("1")
        assert r"\addcontentsline{toc}{section}{Title}" in latex

    def test_explicit_depth1_subsection_absent(self) -> None:
        latex = self._latex_for_depth("1")
        assert r"\addcontentsline{toc}{subsection}{Q1}" not in latex

    def test_explicit_depth1_subsubsection_absent(self) -> None:
        latex = self._latex_for_depth("1")
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" not in latex

    # CONTENTS: (bare/empty) — now depth 2: section + subsection, no subsubsection
    def test_bare_contents_section_present(self) -> None:
        latex = self._latex_for_depth("")
        assert r"\addcontentsline{toc}{section}{Title}" in latex

    def test_bare_contents_subsection_present(self) -> None:
        latex = self._latex_for_depth("")
        assert r"\addcontentsline{toc}{subsection}{Q1}" in latex

    def test_bare_contents_subsubsection_absent(self) -> None:
        latex = self._latex_for_depth("")
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" not in latex

    # keyword "2" — same as bare
    def test_depth2_section_present(self) -> None:
        latex = self._latex_for_depth("2")
        assert r"\addcontentsline{toc}{section}{Title}" in latex

    def test_depth2_subsection_present(self) -> None:
        latex = self._latex_for_depth("2")
        assert r"\addcontentsline{toc}{subsection}{Q1}" in latex

    def test_depth2_subsubsection_absent(self) -> None:
        latex = self._latex_for_depth("2")
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" not in latex

    # depth 3 keyword variants — "3", "full", "all"
    def test_depth3_all_present(self) -> None:
        latex = self._latex_for_depth("3")
        assert r"\addcontentsline{toc}{section}{Title}" in latex
        assert r"\addcontentsline{toc}{subsection}{Q1}" in latex
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" in latex

    def test_full_keyword_all_present(self) -> None:
        latex = self._latex_for_depth("full")
        assert r"\addcontentsline{toc}{section}{Title}" in latex
        assert r"\addcontentsline{toc}{subsection}{Q1}" in latex
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" in latex

    def test_all_keyword_all_present(self) -> None:
        latex = self._latex_for_depth("all")
        assert r"\addcontentsline{toc}{section}{Title}" in latex
        assert r"\addcontentsline{toc}{subsection}{Q1}" in latex
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" in latex


class TestDefaultDepth:
    """Without CONTENTS: in the document, default depth is 3 (emit everything)."""

    def test_no_contents_node_section_addcontentsline_present(self) -> None:
        latex = _latex("=== Title ===\n")
        assert r"\addcontentsline{toc}{section}{Title}" in latex

    def test_no_contents_node_subsection_addcontentsline_present(self) -> None:
        latex = _latex("** Q1 **\n\nx = 1\n")
        assert r"\addcontentsline{toc}{subsection}{Q1}" in latex

    def test_no_contents_node_subsubsection_addcontentsline_present(self) -> None:
        latex = _latex("(a) content\n")
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" in latex


# ---------------------------------------------------------------------------
# toc_parts override
# ---------------------------------------------------------------------------


class TestTocPartsOverride:
    """toc_parts=True raises effective depth to 3, keeping tocdepth consistent.

    Both the addcontentsline emission guards and \\setcounter{tocdepth} derive
    from self._toc_depth, which is bumped to 3 when toc_parts is set.
    """

    _SRC = "CONTENTS: 1\n\n=== Title ===\n\n** Q1 **\n\n(a) content\n"

    def test_toc_parts_subsubsection_present(self) -> None:
        latex = _latex(self._SRC, toc_parts=True)
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" in latex

    def test_toc_parts_subsection_present(self) -> None:
        # Override pulls solutions in too — no orphaned subsubsection entries
        latex = _latex(self._SRC, toc_parts=True)
        assert r"\addcontentsline{toc}{subsection}{Q1}" in latex

    def test_toc_parts_tocdepth_set_to_3(self) -> None:
        # \setcounter{tocdepth}{3} keeps the printed TOC consistent with emission
        latex = _latex(self._SRC, toc_parts=True)
        assert r"\setcounter{tocdepth}{3}" in latex

    def test_no_toc_parts_depth1_tocdepth_is_1(self) -> None:
        # Contrast: without override, CONTENTS: 1 → tocdepth 1
        latex = _latex(self._SRC)
        assert r"\setcounter{tocdepth}{1}" in latex

    def test_no_toc_parts_depth1_only_section_addcontentsline(self) -> None:
        # Contrast: without override, only section entry emitted
        latex = _latex(self._SRC)
        assert r"\addcontentsline{toc}{section}{Title}" in latex
        assert r"\addcontentsline{toc}{subsection}{Q1}" not in latex
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" not in latex


# ---------------------------------------------------------------------------
# Reuse isolation (defect 1)
# ---------------------------------------------------------------------------


class TestReuseIsolation:
    """A reused LaTeXGenerator must not leak _toc_depth across calls.

    The first document sets depth 1 via CONTENTS: 1.  The second document
    has no CONTENTS: directive, so it must revert to the default depth of 3
    — meaning all three addcontentsline levels are emitted.
    """

    _DOC1 = "CONTENTS: 1\n\n=== Title ===\n\n** Q1 **\n\n(a) content\n"
    _DOC2 = "=== Title ===\n\n** Q1 **\n\n(a) content\n"

    def _parse_ast(self, src: str) -> object:
        lexer = Lexer(src)
        tokens = lexer.tokenize()
        return Parser(tokens).parse()

    def test_second_call_subsubsection_present(self) -> None:
        # If depth leaks, this is absent because depth 1 was set by doc1.
        gen = LaTeXGenerator()
        gen.generate_document(self._parse_ast(self._DOC1))  # type: ignore[arg-type]
        latex2 = gen.generate_document(self._parse_ast(self._DOC2))  # type: ignore[arg-type]
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" in latex2

    def test_second_call_subsection_present(self) -> None:
        gen = LaTeXGenerator()
        gen.generate_document(self._parse_ast(self._DOC1))  # type: ignore[arg-type]
        latex2 = gen.generate_document(self._parse_ast(self._DOC2))  # type: ignore[arg-type]
        assert r"\addcontentsline{toc}{subsection}{Q1}" in latex2

    def test_second_call_matches_fresh_generator(self) -> None:
        # The reused generator's second output must equal a fresh generator's output.
        gen_reused = LaTeXGenerator()
        gen_reused.generate_document(self._parse_ast(self._DOC1))  # type: ignore[arg-type]
        latex_reused = gen_reused.generate_document(self._parse_ast(self._DOC2))  # type: ignore[arg-type]

        gen_fresh = LaTeXGenerator()
        latex_fresh = gen_fresh.generate_document(self._parse_ast(self._DOC2))  # type: ignore[arg-type]

        assert latex_reused == latex_fresh


# ---------------------------------------------------------------------------
# Nested CONTENTS: (defect 2)
# ---------------------------------------------------------------------------


class TestNestedContentsDepth:
    """CONTENTS: inside a Section must still set _toc_depth.

    Verifies that the parser nests the Contents node inside Section.items
    (structural fact), and that the generator's recursive pre-scan finds it.
    """

    _SRC = "=== Introduction ===\n\nCONTENTS: 3\n\n** Q1 **\n\n(a) content\n"

    def test_parser_nests_contents_inside_section(self) -> None:
        # Confirm structural assumption: Contents is inside Section.items.
        lexer = Lexer(self._SRC)
        tokens = lexer.tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Document)
        assert len(ast.items) >= 1
        section = ast.items[0]
        assert isinstance(section, Section)
        contents_nodes = [item for item in section.items if isinstance(item, Contents)]
        assert len(contents_nodes) == 1
        assert contents_nodes[0].depth == "3"

    def test_nested_contents_depth3_tocdepth_set(self) -> None:
        latex = _latex(self._SRC)
        assert r"\setcounter{tocdepth}{3}" in latex

    def test_nested_contents_depth3_section_present(self) -> None:
        latex = _latex(self._SRC)
        assert r"\addcontentsline{toc}{section}{Introduction}" in latex

    def test_nested_contents_depth3_subsubsection_present(self) -> None:
        # Absent if depth was silently dropped and defaulted to something else.
        latex = _latex(self._SRC)
        assert r"\addcontentsline{toc}{subsubsection}{(a)}" in latex
