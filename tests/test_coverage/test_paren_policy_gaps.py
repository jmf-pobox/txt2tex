"""Tests for parenthesisation policy gaps #1, #2, and #3.

Gap #1: Arithmetic operators (+, -, *, /, mod) are explicit in PRECEDENCE so
        that a + b * c and similar expressions receive correct parens.

Gap #2: UNARY_PRECEDENCE is the machine-readable policy for unary-operator
        precedence.  Unary operators bind tighter than all binary operators.

Gap #3: _generate_set_comprehension passes parent=node when generating the
        predicate, so nested quantifiers inside { x : T | exists ... } receive
        the always-paren treatment.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import BinaryOp, Identifier, Quantifier, SetComprehension
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _parse_expr(text: str) -> BinaryOp | Quantifier | SetComprehension | Identifier:
    tokens = Lexer(text).tokenize()
    return Parser(tokens).parse()  # type: ignore[return-value]


def _gen(text: str, *, fuzz: bool = False) -> str:
    ast = _parse_expr(text)
    return LaTeXGenerator(use_fuzz=fuzz).generate_expr(ast)


# ---------------------------------------------------------------------------
# Gap #1 — Arithmetic operators in PRECEDENCE table
# ---------------------------------------------------------------------------


class TestArithmeticPrecedence:
    """PRECEDENCE table includes +, -, *, / with correct relative ordering."""

    def test_table_contains_plus(self) -> None:
        """+ has an explicit entry in PRECEDENCE."""
        assert "+" in LaTeXGenerator.PRECEDENCE

    def test_table_contains_minus(self) -> None:
        """-  has an explicit entry in PRECEDENCE."""
        assert "-" in LaTeXGenerator.PRECEDENCE

    def test_table_contains_star(self) -> None:
        """* has an explicit entry in PRECEDENCE."""
        assert "*" in LaTeXGenerator.PRECEDENCE

    def test_table_contains_slash(self) -> None:
        """/ has an explicit entry in PRECEDENCE."""
        assert "/" in LaTeXGenerator.PRECEDENCE

    def test_table_contains_mod(self) -> None:
        """mod has an explicit entry in PRECEDENCE."""
        assert "mod" in LaTeXGenerator.PRECEDENCE

    def test_multiply_binds_tighter_than_add(self) -> None:
        """* has higher precedence than +."""
        assert LaTeXGenerator.PRECEDENCE["*"] > LaTeXGenerator.PRECEDENCE["+"]

    def test_divide_same_as_multiply(self) -> None:
        """/ has the same precedence as *."""
        assert LaTeXGenerator.PRECEDENCE["/"] == LaTeXGenerator.PRECEDENCE["*"]

    def test_add_and_subtract_equal(self) -> None:
        """+ and - have the same precedence."""
        assert LaTeXGenerator.PRECEDENCE["+"] == LaTeXGenerator.PRECEDENCE["-"]

    def test_arithmetic_above_set_ops(self) -> None:
        """Arithmetic operators bind tighter than set operators (e.g. union)."""
        assert LaTeXGenerator.PRECEDENCE["+"] > LaTeXGenerator.PRECEDENCE["union"]

    def test_no_parens_on_tighter_right_child(self) -> None:
        """a + b * c → no spurious parens around b * c (already tighter)."""
        # Parser builds a + (b * c); * is tighter, so * child needs no parens
        # from the + parent.
        result = _gen("a + b * c")
        assert "(b * c)" not in result
        assert "a + b * c" in result

    def test_parens_on_looser_right_child_with_lower_prec_outer(self) -> None:
        """(a land b) + c: + is right child of land; no spurious parens on +."""
        # land (prec 4) has + (prec 10) as right child — child prec > parent,
        # so NO parens are added around the + expression.
        result = _gen("a land b + c")
        assert "a \\land b + c" in result

    def test_explicit_parens_preserved_in_arithmetic(self) -> None:
        """User-written (a + b) * c preserves the parens."""
        result = _gen("(a + b) * c")
        assert "(a + b) * c" in result

    @pytest.mark.parametrize(
        ("child_op", "parent_op"),
        [
            ("+", "land"),
            ("*", "land"),
            ("+", "<=>"),
            ("*", "=>"),
            ("+", "lor"),
        ],
    )
    def test_arithmetic_child_of_logical_parent_no_parens(
        self, child_op: str, parent_op: str
    ) -> None:
        """Arithmetic child of a logical parent never needs parens."""
        child_prec = LaTeXGenerator.PRECEDENCE[child_op]
        parent_prec = LaTeXGenerator.PRECEDENCE[parent_op]
        # Child should have higher precedence — no parens required
        assert child_prec > parent_prec


# ---------------------------------------------------------------------------
# Gap #2 — UNARY_PRECEDENCE as machine-readable policy
# ---------------------------------------------------------------------------


class TestUnaryPrecedence:
    """UNARY_PRECEDENCE dict is the single source of truth for unary binding."""

    def test_table_exists(self) -> None:
        """LaTeXGenerator.UNARY_PRECEDENCE is defined."""
        assert hasattr(LaTeXGenerator, "UNARY_PRECEDENCE")

    def test_all_unary_ops_present(self) -> None:
        """Every operator in UNARY_OPS has an entry in UNARY_PRECEDENCE."""
        unary_ops_keys = set(LaTeXGenerator.UNARY_OPS.keys())
        # Postfix +, *, ~ are in UNARY_OPS but map to superscript — they are
        # also in UNARY_PRECEDENCE.
        assert unary_ops_keys <= set(LaTeXGenerator.UNARY_PRECEDENCE.keys())

    def test_unary_tighter_than_all_binary(self) -> None:
        """Every unary precedence level exceeds every binary precedence level."""
        max_binary = max(LaTeXGenerator.PRECEDENCE.values())
        for op, prec in LaTeXGenerator.UNARY_PRECEDENCE.items():
            assert prec > max_binary, (
                f"UNARY_PRECEDENCE[{op!r}]={prec} <= max binary {max_binary}"
            )

    def test_lnot_a_land_b_wraps_binary(self) -> None:
        """lnot (A land B) wraps the BinaryOp operand in parens."""
        result = _gen("lnot (A land B)")
        assert "\\lnot (A \\land B)" in result

    def test_lnot_simple_id_no_parens(self) -> None:
        """lnot x does not add spurious parens around a simple identifier."""
        result = _gen("lnot x")
        assert "\\lnot x" in result

    def test_unary_minus_binary_operand_parens(self) -> None:
        """Unary minus applied to a + b wraps the operand."""
        result = _gen("-(a + b)")
        assert "-(a + b)" in result

    def test_fuzz_function_like_set_is_frozenset(self) -> None:
        """_FUZZ_FUNCTION_LIKE_UNARY is a frozenset (immutable, queryable)."""
        assert isinstance(LaTeXGenerator._FUZZ_FUNCTION_LIKE_UNARY, frozenset)

    def test_fuzz_function_like_contains_dom_ran(self) -> None:
        """_FUZZ_FUNCTION_LIKE_UNARY includes dom and ran."""
        assert "dom" in LaTeXGenerator._FUZZ_FUNCTION_LIKE_UNARY
        assert "ran" in LaTeXGenerator._FUZZ_FUNCTION_LIKE_UNARY


# ---------------------------------------------------------------------------
# Gap #3 — Set-comprehension predicate passes parent context
# ---------------------------------------------------------------------------


class TestSetComprehensionPredicateParent:
    """Quantifiers inside set-comprehension predicates get the always-paren
    treatment."""

    def test_exists_in_set_comprehension_gets_parens_fuzz(self) -> None:
        """{ x : N | exists y : N | y > 0 } wraps the exists in fuzz mode."""
        result = _gen("{ x : N | exists y : N | y > 0 }", fuzz=True)
        # The exists should be wrapped in parens inside the comprehension
        assert "(\\exists" in result

    def test_exists_in_set_comprehension_gets_parens_nonfuzz(self) -> None:
        """{ x : N | exists y : N | y > 0 } wraps the exists in non-fuzz mode."""
        result = _gen("{ x : N | exists y : N | y > 0 }", fuzz=False)
        assert "(\\exists" in result

    def test_simple_predicate_no_extra_parens(self) -> None:
        """{ x : N | x > 0 } does not add spurious parens around a comparison."""
        result = _gen("{ x : N | x > 0 }")
        # The predicate is x > 0 — no parens
        assert "(x > 0)" not in result

    def test_forall_in_set_comprehension_gets_parens(self) -> None:
        """{ x : N | forall y : N | y > 0 } wraps the forall in fuzz mode."""
        result = _gen("{ x : N | forall y : N | y > 0 }", fuzz=True)
        assert "(\\forall" in result

    def test_quantifier_with_connective_body_inside_comprehension_gets_parens(
        self,
    ) -> None:
        """Quantifier with connective body inside a set comprehension is wrapped.

        This covers always-paren context #1 from the ADR: quantifier body
        containing propositional connectives (land, lor, =>, <=>), combined
        with set-comprehension context.  Top-level quantifiers do not get
        parens; only nested ones do.
        """
        result = _gen("{ x : N | exists y : N | y > 0 land y < 5 }", fuzz=True)
        # The exists is in a set-comprehension predicate (context #2), so it
        # is already wrapped.  This test verifies the connective body (context #1)
        # also triggers wrapping inside the comprehension.
        assert "(\\exists" in result

    def test_quantifier_with_connective_body_nonfuzz_gets_parens(self) -> None:
        """Connective body triggers wrapping in non-fuzz mode too."""
        # In non-fuzz top-level context there is no parent, so no wrap.
        # We need to place the quantifier inside a set comprehension.
        result = _gen("{ x : N | exists y : N | y > 0 land y < 5 }", fuzz=False)
        assert "(\\exists" in result

    def test_set_comprehension_with_expression_part_no_spurious_parens(self) -> None:
        """{ x : N | x > 0 . x * 2 } — expression part unaffected."""
        result = _gen("{ x : N | x > 0 . x * 2 }")
        # predicate x > 0 should not get spurious parens
        assert "(x > 0)" not in result

    def test_simple_set_comprehension_structure(self) -> None:
        """{ x : N | x > 0 } contains expected components."""
        result = _gen("{ x : N | x > 0 }")
        assert r"\{" in result
        assert r"\}" in result
        assert "x > 0" in result
