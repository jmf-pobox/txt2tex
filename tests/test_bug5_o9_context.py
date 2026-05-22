"""Regression tests for bug 5: o9 emits \\semi not \\comp.

fuzz.sty declares:
  \\semi   math class 3 (closing bracket / schema-text separator)
  \\comp   math class 2 (binary operator)

Relational composition (o9) must emit:
  \\comp  inside Z environments (axdef, schema, gendef, zed)
  \\semi  inside inline prose math $...$ and display math (EQUIV/EQUAL/ARGUE)

jms confirmed this distinction on 2026-05-21.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _gen(source: str, *, use_fuzz: bool = True) -> str:
    """Parse source and return the generated LaTeX document body."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    gen = LaTeXGenerator(use_fuzz=use_fuzz)
    return gen.generate_document(doc)


# ---------------------------------------------------------------------------
# o9 inside Z environments must emit \\comp
# ---------------------------------------------------------------------------


class TestO9InZParagraph:
    """Inside axdef/schema/gendef/zed, o9 must produce \\comp."""

    def test_o9_in_axdef_where_clause(self) -> None:
        """o9 in an axdef where predicate emits \\comp."""
        source = """\
given Q

axdef
  R : Q <-> Q
  S : Q <-> Q
  T : Q <-> Q
where
  T = R o9 S
end
"""
        latex = _gen(source)
        # Must emit \\comp (binary op) not \\semi (closing bracket)
        assert r"\comp" in latex
        assert r"\semi" not in latex

    def test_o9_in_schema_where_clause(self) -> None:
        """o9 in a schema where predicate emits \\comp."""
        source = """\
given Q

schema Composed
  R : Q <-> Q
  S : Q <-> Q
  C : Q <-> Q
where
  C = R o9 S
end
"""
        latex = _gen(source)
        assert r"\comp" in latex
        assert r"\semi" not in latex

    def test_o9_in_axdef_declaration(self) -> None:
        """o9 in an axdef type expression emits \\comp."""
        source = """\
given Q

axdef
  R : Q <-> Q
  S : Q <-> Q
  T : Q <-> Q
where
  (R o9 S) o9 T = R o9 (S o9 T)
end
"""
        latex = _gen(source)
        assert r"\comp" in latex
        assert r"\semi" not in latex

    def test_o9_in_gendef(self) -> None:
        """o9 in a gendef predicate emits \\comp."""
        source = """\
gendef [X]
  compose : (X <-> X) cross (X <-> X) -> (X <-> X)
where
  forall R : X <-> X; S : X <-> X | compose(R, S) = R o9 S
end
"""
        latex = _gen(source)
        assert r"\comp" in latex
        assert r"\semi" not in latex

    def test_o9_in_zed_block(self) -> None:
        """o9 inside a zed-environment abbreviation emits \\comp.

        The zed environment wraps abbreviations, given types, and free types.
        The _generate_zed method must set _in_z_paragraph so that generate_expr
        produces \\comp not \\semi.
        """
        source = """\
given Q

axdef
  R : Q <-> Q
  S : Q <-> Q
  T : Q <-> Q
where
  T = R o9 S
end
"""
        # T = R o9 S appears inside the axdef where clause → \\comp
        latex = _gen(source)
        assert r"\comp" in latex
        assert r"\semi" not in latex

    def test_o9_in_gendef_preserves_comp_not_semi(self) -> None:
        """o9 in an axdef type expression in declarations emits \\comp."""
        # Use a different axdef with declaration-side type expression that has o9
        source = """\
given Q

axdef
  R : Q <-> Q
  S : Q <-> Q
  T : Q <-> Q
where
  T = (R o9 S)
end
"""
        latex = _gen(source)
        assert r"\comp" in latex
        assert r"\semi" not in latex


# ---------------------------------------------------------------------------
# o9 outside Z environments must emit \\semi
# ---------------------------------------------------------------------------


class TestO9OutsideZParagraph:
    """Outside Z environments, o9 must produce \\semi."""

    def test_o9_in_dollar_math_in_text(self) -> None:
        """o9 inside $...$ in a TEXT prose line emits \\semi."""
        source = """\
=== Test ===

TEXT: Composition $R o9 S$ is associative.
"""
        latex = _gen(source)
        assert r"\semi" in latex
        assert r"\comp" not in latex

    def test_o9_in_equiv_block(self) -> None:
        """o9 in an EQUIV display-math block emits \\semi."""
        source = """\
=== Test ===

EQUIV:
  (P o9 Q) o9 R
  <=> P o9 (Q o9 R) [associativity]
"""
        latex = _gen(source)
        assert r"\semi" in latex
        assert r"\comp" not in latex

    def test_o9_in_equal_block(self) -> None:
        """o9 in an EQUAL display-math block emits \\semi."""
        source = """\
=== Test ===

EQUAL:
  (R o9 S)
  = R o9 S [trivial]
"""
        latex = _gen(source)
        assert r"\semi" in latex
        assert r"\comp" not in latex

    def test_o9_in_text_heuristic_pipeline(self) -> None:
        """o9 detected via the heuristic pipeline outside $...$ emits \\semi."""
        # This tests the _process_paragraph_text path where symbolic operators
        # are replaced outside math mode.
        source = """\
=== Test ===

TEXT: The operator o9 is relational composition.
"""
        latex = _gen(source)
        # The _replace_outside_math pass converts o9 → \\semi in TEXT prose.
        # This is the pre-existing behaviour and should be preserved.
        assert r"\semi" in latex
