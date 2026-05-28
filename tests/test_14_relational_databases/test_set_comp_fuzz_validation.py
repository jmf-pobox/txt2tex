"""Tests for dual-emit fuzz validation of set comprehensions.

Two orthogonal transforms:
1. Synthetic abbreviation: standalone set comprehensions get a hidden
   \\setbox0=\\vbox{\\begin{zed}zS_N == ...\\end{zed}} for fuzz validation.
2. Binding-to-tuple: binding characteristic expressions become tuples
   in the hidden fuzz copy.

Four cases:
A. Standalone set comp, no binding → synthetic abbrev, same expression
B. Standalone set comp, binding → synthetic abbrev + binding→tuple
C. Abbreviation with binding → dual-emit: hidden tuple, visible binding
D. Abbreviation without binding → no change (already fuzz-validated)
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

_HEADER = "=== Test ===\n\n"


def _generate(src: str, *, use_fuzz: bool = True) -> str:
    """Parse src and generate full LaTeX document.

    Wraps bare expressions in a section header so they parse as
    Document items (not bare Expr), which is the path that triggers
    generate_document_item and the dual-emit logic.
    """
    if not src.startswith("===") and not src.startswith("given"):
        src = _HEADER + src
    ast = Parser(Lexer(src).tokenize()).parse()
    gen = LaTeXGenerator(use_fuzz=use_fuzz)
    assert isinstance(ast, Document)
    return gen.generate_document(ast)


# ===================================================================
# Case A: standalone set comprehension, no binding
# ===================================================================


class TestStandaloneSetCompNoBinding:
    """Standalone set comprehensions without bindings get a hidden
    synthetic abbreviation for fuzz validation."""

    def test_hidden_abbreviation_emitted(self) -> None:
        """{ x : N | x > 0 } → output contains hidden \\setbox0 block."""
        latex = _generate("{ x : N | x > 0 }")
        assert r"\setbox0=\vbox{%" in latex
        assert r"\begin{zed}" in latex

    def test_synthetic_name_in_hidden_copy(self) -> None:
        """Hidden copy uses a synthetic name like zS_1."""
        latex = _generate("{ x : N | x > 0 }")
        assert "zS_" in latex

    def test_visible_copy_is_inline_math(self) -> None:
        """Visible copy remains as \\noindent$...$."""
        latex = _generate("{ x : N | x > 0 }")
        assert r"\noindent" in latex
        assert "$" in latex

    def test_fuzz_disabled_no_hidden_copy(self) -> None:
        """With use_fuzz=False, no hidden copy is emitted."""
        latex = _generate("{ x : N | x > 0 }", use_fuzz=False)
        assert r"\setbox0" not in latex

    def test_counter_increments(self) -> None:
        """Two standalone set comps get zS_1 and zS_2."""
        src = "{ x : N | x > 0 }\n{ y : N | y > 1 }"
        latex = _generate(src)
        assert "zS_1" in latex
        assert "zS_2" in latex


# ===================================================================
# Case B: standalone set comprehension with binding
# ===================================================================


class TestStandaloneSetCompWithBinding:
    """Standalone set comprehensions with binding characteristic
    expressions get a hidden copy with the binding converted to a
    tuple."""

    def test_hidden_copy_has_no_binding(self) -> None:
        """Hidden copy converts binding to tuple — no \\lblot."""
        src = "{ m : Members | m.username = m.username . {| name == m.username |} }"
        latex = _generate(src)
        # Find the \setbox0 block
        setbox_start = latex.find(r"\setbox0")
        assert setbox_start >= 0
        vbox_close = latex.find("\n}\n", setbox_start)
        hidden_block = latex[setbox_start:vbox_close]
        assert r"\lblot" not in hidden_block

    def test_visible_copy_has_binding(self) -> None:
        """Visible copy preserves the binding."""
        src = "{ m : Members | m.username = m.username . {| name == m.username |} }"
        latex = _generate(src)
        # The visible part (after the hidden block) should have \lblot
        setbox_start = latex.find(r"\setbox0")
        assert setbox_start >= 0
        vbox_close = latex.find("\n}\n", setbox_start)
        visible_part = latex[vbox_close:]
        assert r"\lblot" in visible_part

    def test_multi_field_binding_becomes_tuple(self) -> None:
        """Multi-field binding converts to tuple in hidden copy."""
        src = (
            "{ s : Ship; c : Class | s.class = c.class . "
            "{| name == s.name, disp == c.displacement |} }"
        )
        latex = _generate(src)
        setbox_start = latex.find(r"\setbox0")
        assert setbox_start >= 0
        vbox_close = latex.find("\n}\n", setbox_start)
        hidden_block = latex[setbox_start:vbox_close]
        assert r"\lblot" not in hidden_block
        # Hidden block should have the tuple components without binding syntax
        assert "s.name" in hidden_block or "name" in hidden_block


# ===================================================================
# Case C: abbreviation with binding characteristic expression
# ===================================================================


class TestAbbreviationWithBinding:
    """Abbreviations whose RHS is a set comprehension with a binding
    characteristic expression dual-emit: hidden copy with tuple,
    visible copy with binding."""

    def test_dual_emit_structure(self) -> None:
        """S == { m : Members | pred . {| ... |} } emits both hidden
        and visible copies."""
        src = (
            "given UserType\n"
            "schema Members\n  username : UserType\nend\n\n"
            "S == { m : Members | m.username = m.username . "
            "{| name == m.username |} }"
        )
        latex = _generate(src)
        assert r"\setbox0=\vbox{%" in latex
        assert r"\noindent" in latex

    def test_hidden_copy_has_tuple_not_binding(self) -> None:
        """Hidden copy converts binding to tuple."""
        src = (
            "given UserType\n"
            "schema Members\n  username : UserType\nend\n\n"
            "S == { m : Members | m.username = m.username . "
            "{| name == m.username |} }"
        )
        latex = _generate(src)
        setbox_start = latex.find(r"\setbox0")
        assert setbox_start >= 0
        vbox_close = latex.find("\n}\n", setbox_start)
        hidden_block = latex[setbox_start:vbox_close]
        assert r"\lblot" not in hidden_block
        assert "S ==" in hidden_block

    def test_visible_copy_has_binding(self) -> None:
        """Visible copy preserves the binding syntax."""
        src = (
            "given UserType\n"
            "schema Members\n  username : UserType\nend\n\n"
            "S == { m : Members | m.username = m.username . "
            "{| name == m.username |} }"
        )
        latex = _generate(src)
        setbox_start = latex.find(r"\setbox0")
        vbox_close = latex.find("\n}\n", setbox_start)
        visible_part = latex[vbox_close:]
        assert r"\lblot" in visible_part
        assert "S ==" in visible_part

    def test_abbreviation_name_in_both_copies(self) -> None:
        """The abbreviation name appears in both hidden and visible."""
        src = (
            "given UserType\n"
            "schema Members\n  username : UserType\nend\n\n"
            "S == { m : Members | m.username = m.username . "
            "{| name == m.username |} }"
        )
        latex = _generate(src)
        setbox_start = latex.find(r"\setbox0")
        vbox_close = latex.find("\n}\n", setbox_start)
        hidden_block = latex[setbox_start:vbox_close]
        visible_part = latex[vbox_close:]
        assert "S ==" in hidden_block
        assert "S ==" in visible_part


# ===================================================================
# Case D: abbreviation without binding — no change
# ===================================================================


class TestAbbreviationWithoutBinding:
    """Abbreviations without binding characteristic expressions are
    unchanged — no dual-emit needed."""

    def test_pure_z_abbreviation_no_setbox(self) -> None:
        """Pairs == N cross N → single \\begin{zed}, no \\setbox0."""
        latex = _generate("Pairs == N cross N")
        assert r"\setbox0" not in latex
        assert r"\begin{zed}" in latex

    def test_algebra_abbreviation_no_setbox(self) -> None:
        """R == sigma[p](S) → \\noindent$...$, no \\setbox0."""
        src = "given T\nschema S\n  x : T\nend\n\nR == sigma[x = x](S)"
        latex = _generate(src)
        assert r"\setbox0" not in latex
        assert r"\noindent" in latex
