"""Tests for rejecting numeric `^` heading into a fuzz-checked Z box.

Z's `_^_` is relational iteration (Z RM §4.11); there is no numeric
exponentiation operator in the toolkit.  `x^2` where `x : N` makes fuzz
misparse the expression as `iter 2 x` and reject it with a cryptic type
error.  These tests pin the source-line rejection this issue (#99
follow-on) adds: a *provably* numeric `Superscript` base heading into a
fuzz-checked box raises `NumericSuperscriptError` before fuzz ever sees
the LaTeX, while a relation-typed base (`r^2` where `r : S <-> S`,
genuine iteration) is left untouched.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import Document
from txt2tex.codegen.numeric_superscript import NumericSuperscriptError
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _fragment(src: str, *, use_fuzz: bool = True) -> str:
    """Generate a LaTeX fragment (no preamble) from source."""
    ast = Parser(Lexer(src).tokenize()).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=use_fuzz).generate_fragment(ast)


# ---------------------------------------------------------------------------
# Standalone set comprehension -- the #99 failure case
# ---------------------------------------------------------------------------


class TestStandaloneComprehensionSquare:
    """`{ x : N | x > 0 . x^2 }` -- numeric base, quadratic."""

    SRC = "{ x : N | x > 0 . x^2 }\n"

    def test_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment(self.SRC)

    def test_names_the_expression(self) -> None:
        with pytest.raises(NumericSuperscriptError, match=r"x\^2"):
            _fragment(self.SRC)

    def test_names_the_fuzz_reading(self) -> None:
        with pytest.raises(NumericSuperscriptError, match="iter 2 x"):
            _fragment(self.SRC)

    def test_suggests_the_product(self) -> None:
        with pytest.raises(NumericSuperscriptError) as exc_info:
            _fragment(self.SRC)
        assert "x * x" in str(exc_info.value)


class TestStandaloneComprehensionCube:
    """`{ x : N | x > 0 . x^3 }` -- cubic suggests a three-fold product."""

    SRC = "{ x : N | x > 0 . x^3 }\n"

    def test_suggests_the_product(self) -> None:
        with pytest.raises(NumericSuperscriptError) as exc_info:
            _fragment(self.SRC)
        assert "x * x * x" in str(exc_info.value)


class TestNestedTower:
    """`{ z : Z | z mod 2 = 0 . (z^2)^3 }` -- structured, not flattened.

    The suggestion preserves the exponent-of-exponent grouping: expand
    the innermost level first (`z^2` -> `z * z`), then repeat that
    parenthesized group for the outer exponent -- `(z * z) * (z * z) *
    (z * z)`, not the flattened `z * z * z * z * z * z`.
    """

    SRC = "{ z : Z | z mod 2 = 0 . (z^2)^3 }\n"

    def test_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment(self.SRC)

    def test_suggests_the_structured_product(self) -> None:
        with pytest.raises(NumericSuperscriptError) as exc_info:
            _fragment(self.SRC)
        assert "(z * z) * (z * z) * (z * z)" in str(exc_info.value)
        assert "z * z * z * z * z * z" not in str(exc_info.value)


class TestExponentZero:
    """`x^0` -- jms Q2: k == 0 suggests the identity `1`, not an empty product."""

    def test_suggests_one(self) -> None:
        with pytest.raises(NumericSuperscriptError) as exc_info:
            _fragment("{ x : N | true . x^0 }\n")
        assert "Rewrite as '1'" in str(exc_info.value)


class TestExponentOne:
    """`x^1` -- jms Q2: k == 1 suggests the base itself, not `x * x`."""

    def test_suggests_the_base(self) -> None:
        with pytest.raises(NumericSuperscriptError) as exc_info:
            _fragment("{ x : N | true . x^1 }\n")
        assert "Rewrite as 'x'" in str(exc_info.value)


class TestArithmeticBase:
    """A `+`/`-`/`*`/`mod`-built base is manifestly `\\num` regardless of scope."""

    @pytest.mark.parametrize(
        "src",
        [
            "{ n : N | true . (n + 1)^2 }\n",
            "{ n : N | true . (n - 1)^2 }\n",
            "{ n : N | true . (n * 2)^2 }\n",
            "{ n : N | true . (n mod 2)^2 }\n",
        ],
    )
    def test_raises(self, src: str) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment(src)


class TestCardinalityBase:
    """`#S` (cardinality) always has result type `\\num`."""

    def test_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment("{ s : P N | true . (#s)^2 }\n")


class TestMinMaxBase:
    """`min(S)`/`max(S)` always have result type `\\num`."""

    def test_min_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment("{ s : P N | true . (min(s))^2 }\n")

    def test_max_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment("{ s : P N | true . (max(s))^2 }\n")


class TestNestedQuantifierScope:
    """A `Superscript` inside a nested binder classifies against that binder."""

    def test_forall_bound_variable_flagged(self) -> None:
        src = "{ x : N | (forall y : N | y^2 >= 0) . x }\n"
        with pytest.raises(NumericSuperscriptError, match=r"y\^2"):
            _fragment(src)

    def test_lambda_bound_variable_flagged(self) -> None:
        src = "{ x : N | true . (lambda y : N . y^2)(x) }\n"
        with pytest.raises(NumericSuperscriptError, match=r"y\^2"):
            _fragment(src)


class TestSymbolicExponent:
    """`{ x : N | true . x^n }` -- no product exists; suggest NOFUZZ/--zed only."""

    SRC = "{ x : N | true . x^n }\n"

    def test_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment(self.SRC)

    def test_no_rewrite_suggested(self) -> None:
        with pytest.raises(NumericSuperscriptError) as exc_info:
            _fragment(self.SRC)
        assert "Rewrite as" not in str(exc_info.value)

    def test_suggests_nofuzz_or_zed(self) -> None:
        with pytest.raises(NumericSuperscriptError) as exc_info:
            _fragment(self.SRC)
        msg = str(exc_info.value)
        assert "NOFUZZ" in msg
        assert "--zed" in msg


# ---------------------------------------------------------------------------
# Regression: relation-typed base is genuine iteration, never flagged
# ---------------------------------------------------------------------------


class TestRelationalBaseNeverFlagged:
    """`r^2` where `r : S <-> S` is `iter 2 r` -- must keep type-checking."""

    def test_abbreviation_rhs_not_flagged(self) -> None:
        src = "given S\naxdef\n  r : S <-> S\nend\n\nrr == r^2\n"
        _fragment(src)  # must not raise

    def test_comprehension_base_not_flagged(self) -> None:
        src = "given S\n\n{ p : S <-> S | true . p^2 }\n"
        _fragment(src)  # must not raise


class TestGivenSetElementNotFlagged:
    """An element of a given set has no numeric domain -- never flagged."""

    def test_not_flagged(self) -> None:
        src = "given S\n\n{ x : S | true . x^2 }\n"
        _fragment(src)  # must not raise


class TestUnprovableFreeNameNotFlagged:
    """A name with no locally visible declaration is left for fuzz to judge."""

    def test_not_flagged(self) -> None:
        src = "{ x : N | true . y^2 }\n"
        _fragment(src)  # must not raise -- y is not locally declared


# ---------------------------------------------------------------------------
# --zed mode: no fuzz-checking, no rejection
# ---------------------------------------------------------------------------


class TestZedModeUnaffected:
    def test_numeric_power_renders(self) -> None:
        out = _fragment("{ x : N | x > 0 . x^2 }\n", use_fuzz=False)
        assert r"\bsup" in out


# ---------------------------------------------------------------------------
# Consistency: axdef, schema, gendef, abbreviation
# ---------------------------------------------------------------------------


class TestAxdefPredicate:
    SRC = "axdef\n  x : N\nwhere\n  x^2 > 0\nend\n"

    def test_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment(self.SRC)


class TestSchemaPredicate:
    SRC = "schema Sq\n  x : N\nwhere\n  x^2 > 0\nend\n"

    def test_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment(self.SRC)


class TestGendefPredicate:
    SRC = "gendef [X]\n  x : N\nwhere\n  x^2 > 0\nend\n"

    def test_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment(self.SRC)


class TestAbbreviationNumericLiteral:
    """`Y == 2^3` -- a `Number` base is always numeric, scope or not."""

    SRC = "Y == 2^3\n"

    def test_raises(self) -> None:
        with pytest.raises(NumericSuperscriptError):
            _fragment(self.SRC)


class TestNofuzzWaiverSkipsTheCheck:
    """A NOFUZZ box is explicitly excluded from fuzz-checking; must not raise."""

    SRC = (
        "NOFUZZ: fuzz reads ^ as relational iteration\n"
        "axdef\n  x : N\nwhere\n  x^2 > 0\nend\n"
    )

    def test_not_flagged(self) -> None:
        _fragment(self.SRC)  # must not raise
