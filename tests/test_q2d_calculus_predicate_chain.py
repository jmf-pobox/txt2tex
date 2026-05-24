"""Parser-level tests for multi-typed Z comprehension predicate chains (Q2(d) bug).

The bug: when a set comprehension or quantifier has multiple semicolon-separated
declarations AND the predicate is a conjunction of tuple-projection equalities
(e.g., ``s.class = c.class land s.name = c.name``), the field-projection
disambiguation heuristic inside ``_parse_postfix`` incorrectly treats ``.field``
as a bullet separator.  Root cause: ``peek_ahead(2)`` returns an IDENTIFIER token
(the field name) which is not in ``safe_followers``, so the parser breaks out
without consuming ``.field``, leaving unparsed tokens and either raising
``ParserError`` (set comprehensions) or silently producing a truncated AST
(nested-quantifier path).

Stage 1 of TDD: make the bug visible via failing tests committed to the repo.
Passing tests have no mark; failing tests are marked ``xfail(strict=True)`` so
that the suite stays green while the bug exists and turns red (XPASS → error)
the moment the fix lands.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    Binding,
    Document,
    Expr,
    Identifier,
    Quantifier,
    SetComprehension,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse(src: str) -> Expr:
    """Lex and parse src; return the top-level AST node.

    For single-expression inputs the parser returns the node directly.
    When it wraps in a Document (multi-item source), return items[0].
    """
    tokens = Lexer(src).tokenize()
    result = Parser(tokens).parse()
    if isinstance(result, Document):
        return result.items[0]  # type: ignore[return-value]
    return result


# ---------------------------------------------------------------------------
# TestMultiDeclPredicateChain
# ---------------------------------------------------------------------------


class TestMultiDeclPredicateChain:
    """Parser tests for multi-declaration comprehension/quantifier predicate chains."""

    # -----------------------------------------------------------------------
    # Test 1 — CONTROL: single-var comprehension with field-projection predicate
    # -----------------------------------------------------------------------

    def test_single_var_control_passes(self) -> None:
        """Single-decl set comprehension with projection predicate and binding body.

        This is the baseline: ``{ s : Ship | s.name = 'X' . {| name == s.name |} }``
        must parse without error and produce a SetComprehension with:
        - variables = ['s']
        - extra_declarations = None
        - predicate = BinaryOp('=', ...)
        - expression = Binding(...)
        """
        src = "{ s : Ship | s.name = 'X' . {| name == s.name |} }"
        node = _parse(src)
        assert isinstance(node, SetComprehension)
        assert node.variables == ["s"]
        assert node.extra_declarations is None
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == "="
        assert isinstance(node.expression, Binding)

    # -----------------------------------------------------------------------
    # Test 2 — multi-decl, predicate is a single equality (no conjunction)
    # -----------------------------------------------------------------------

    def test_multi_decl_no_conjunction_predicate(self) -> None:
        """Multi-decl comprehension with a simple (non-conjunction) predicate.

        ``{ s : Ship; c : Class | s.class = c.class . {| name == s.name |} }``

        The parser already handles multi-decl via ``extra_declarations``.  A
        single equality predicate does not trigger the disambiguation bug.

        Expected AST:
        - variables = ['s']
        - extra_declarations = [('c', Identifier('Class'))]
        - predicate = BinaryOp('=', TupleProjection, TupleProjection)
        - expression = Binding(...)
        """
        src = "{ s : Ship; c : Class | s.class = c.class . {| name == s.name |} }"
        node = _parse(src)
        assert isinstance(node, SetComprehension)
        assert node.variables == ["s"]
        assert node.extra_declarations is not None
        assert len(node.extra_declarations) == 1
        extra_name, extra_domain = node.extra_declarations[0]
        assert extra_name == "c"
        assert isinstance(extra_domain, Identifier)
        assert extra_domain.name == "Class"
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == "="
        assert isinstance(node.expression, Binding)

    # -----------------------------------------------------------------------
    # Test 3 — multi-decl, predicate is two-conjunct projection equality chain
    # -----------------------------------------------------------------------

    def test_multi_decl_two_conjuncts_projections(self) -> None:
        """Multi-decl comprehension with two-conjunct projection predicate.

        ``{ s : Ship; c : Class | s.class = c.class land s.name = c.name
            . {| name == s.name |} }``

        Expected AST (once fixed):
        - variables = ['s']
        - extra_declarations = [('c', Identifier('Class'))]
        - predicate = BinaryOp('land',
            BinaryOp('=', TupleProjection(s, 'class'), TupleProjection(c, 'class')),
            BinaryOp('=', TupleProjection(s, 'name'), TupleProjection(c, 'name')))
        - expression = Binding(...)
        """
        src = (
            "{ s : Ship; c : Class | s.class = c.class land s.name = c.name"
            " . {| name == s.name |} }"
        )
        node = _parse(src)
        assert isinstance(node, SetComprehension)
        assert node.variables == ["s"]
        assert node.extra_declarations is not None
        assert len(node.extra_declarations) == 1
        assert node.extra_declarations[0][0] == "c"
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == "land"
        left_conj = node.predicate.left
        right_conj = node.predicate.right
        assert isinstance(left_conj, BinaryOp)
        assert left_conj.operator == "="
        assert isinstance(right_conj, BinaryOp)
        assert right_conj.operator == "="
        assert isinstance(node.expression, Binding)

    # -----------------------------------------------------------------------
    # Test 4 — canonical Q2(d) bug: three decls, three conjuncts
    # -----------------------------------------------------------------------

    def test_q2d_three_decl_three_conjuncts(self) -> None:
        """Canonical ex1 Q2(d) input: three declarations, three-conjunct predicate.

        ``{ s : Ship; c : Class; o : Outcome
            | s.class = c.class land o.ship = s.name land o.battle = 'Guadalcanal'
            . {| name == s.name, displacement == c.displacement,
                 numGuns == c.numGuns |} }``

        Expected AST (once fixed):
        - variables = ['s']
        - extra_declarations = [('c', Identifier('Class')),
          ('o', Identifier('Outcome'))]
        - predicate = BinaryOp('land', BinaryOp('land', ...), ...)  (left-assoc)
        - expression = Binding(...)
        """
        src = (
            "{ s : Ship; c : Class; o : Outcome"
            " | s.class = c.class land o.ship = s.name"
            " land o.battle = 'Guadalcanal'"
            " . {| name == s.name, displacement == c.displacement,"
            " numGuns == c.numGuns |} }"
        )
        node = _parse(src)
        assert isinstance(node, SetComprehension)
        assert node.variables == ["s"]
        assert node.extra_declarations is not None
        assert len(node.extra_declarations) == 2
        assert node.extra_declarations[0][0] == "c"
        assert node.extra_declarations[1][0] == "o"
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == "land"
        # Outermost land: left is (s.class=c.class land o.ship=s.name),
        # right is o.battle=...
        assert isinstance(node.predicate.left, BinaryOp)
        assert node.predicate.left.operator == "land"
        assert isinstance(node.predicate.right, BinaryOp)
        assert node.predicate.right.operator == "="
        assert isinstance(node.expression, Binding)

    # -----------------------------------------------------------------------
    # Test 5 — forall multi-decl, conjunction predicate, bullet body
    # -----------------------------------------------------------------------

    def test_forall_multi_decl_conjunction(self) -> None:
        """forall with multi-decl and conjunction predicate, txt2tex '.' bullet.

        ``forall s : Ship; c : Class | s.class = c.class land s.name = c.name . true``

        Expected AST (once fixed):
        - Quantifier('forall', ['s'], Ship,
            body=Quantifier('forall', ['c'], Class,
              body=BinaryOp('land', BinaryOp('=', ...), BinaryOp('=', ...)),
              expression=Identifier('true')))
        """
        src = (
            "forall s : Ship; c : Class | s.class = c.class land s.name = c.name . true"
        )
        node = _parse(src)
        assert isinstance(node, Quantifier)
        assert node.quantifier == "forall"
        assert node.variables == ["s"]
        assert isinstance(node.domain, Identifier)
        assert node.domain.name == "Ship"
        inner = node.body
        assert isinstance(inner, Quantifier)
        assert inner.quantifier == "forall"
        assert inner.variables == ["c"]
        assert isinstance(inner.body, BinaryOp)
        assert inner.body.operator == "land"

    # -----------------------------------------------------------------------
    # Test 6 — exists multi-decl, conjunction predicate (no body separator)
    # -----------------------------------------------------------------------

    def test_exists_multi_decl_conjunction(self) -> None:
        """exists with multi-decl and conjunction predicate.

        ``exists s : Ship; c : Class | s.class = c.class land s.name = c.name``

        Expected AST (once fixed):
        - Quantifier('exists', ['s'], Ship,
            body=Quantifier('exists', ['c'], Class,
              body=BinaryOp('land',
                BinaryOp('=', TupleProjection(s,'class'), TupleProjection(c,'class')),
                BinaryOp('=', TupleProjection(s,'name'), TupleProjection(c,'name')))))
        """
        src = "exists s : Ship; c : Class | s.class = c.class land s.name = c.name"
        node = _parse(src)
        assert isinstance(node, Quantifier)
        assert node.quantifier == "exists"
        assert node.variables == ["s"]
        assert isinstance(node.domain, Identifier)
        assert node.domain.name == "Ship"
        inner = node.body
        assert isinstance(inner, Quantifier)
        assert inner.quantifier == "exists"
        assert inner.variables == ["c"]
        # The innermost body must be the full conjunction, not truncated.
        assert isinstance(inner.body, BinaryOp)
        assert inner.body.operator == "land"
        assert isinstance(inner.body.left, BinaryOp)
        assert inner.body.left.operator == "="
        assert isinstance(inner.body.right, BinaryOp)
        assert inner.body.right.operator == "="

    # -----------------------------------------------------------------------
    # Test 7 — multi-decl, non-projection conjunction (no field access)
    # -----------------------------------------------------------------------

    def test_multi_decl_non_projection_conjunction(self) -> None:
        """Multi-decl comprehension whose predicate has no field projections.

        ``{ s : N; c : N | s < 10 land c < 10 . s + c }``

        The bug only manifests when the predicate contains ``.field`` projections.
        Plain arithmetic comparisons parse correctly with multi-decl.

        Expected AST:
        - variables = ['s']
        - extra_declarations = [('c', Identifier('N'))]
        - predicate = BinaryOp('land', BinaryOp('<', ...), BinaryOp('<', ...))
        - expression = BinaryOp('+', ...)
        """
        src = "{ s : N; c : N | s < 10 land c < 10 . s + c }"
        node = _parse(src)
        assert isinstance(node, SetComprehension)
        assert node.variables == ["s"]
        assert node.extra_declarations is not None
        assert len(node.extra_declarations) == 1
        assert node.extra_declarations[0][0] == "c"
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == "land"
        assert isinstance(node.predicate.left, BinaryOp)
        assert node.predicate.left.operator == "<"
        assert isinstance(node.predicate.right, BinaryOp)
        assert node.predicate.right.operator == "<"
        assert isinstance(node.expression, BinaryOp)
        assert node.expression.operator == "+"

    # -----------------------------------------------------------------------
    # Test 8 — single-var, projection conjunction (no multi-decl)
    # -----------------------------------------------------------------------

    def test_single_var_projection_conjunction(self) -> None:
        """Single-decl comprehension with a two-conjunct projection predicate.

        ``{ s : Ship | s.name = 'X' land s.class = 'Y' . {| name == s.name |} }``

        The bug requires multi-decl: with a single declaration the
        disambiguation heuristic fires differently.  This test confirms
        single-decl + conjunction + projections already works.

        Expected AST:
        - variables = ['s']
        - extra_declarations = None
        - predicate = BinaryOp('land',
            BinaryOp('=', TupleProjection(s, 'name'), StringLit('X')),
            BinaryOp('=', TupleProjection(s, 'class'), StringLit('Y')))
        - expression = Binding(...)
        """
        src = "{ s : Ship | s.name = 'X' land s.class = 'Y' . {| name == s.name |} }"
        node = _parse(src)
        assert isinstance(node, SetComprehension)
        assert node.variables == ["s"]
        assert node.extra_declarations is None
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == "land"
        assert isinstance(node.predicate.left, BinaryOp)
        assert node.predicate.left.operator == "="
        assert isinstance(node.predicate.right, BinaryOp)
        assert node.predicate.right.operator == "="
        assert isinstance(node.expression, Binding)

    # -----------------------------------------------------------------------
    # Test 9 — mu multi-decl with conjunction predicate and projection body
    # -----------------------------------------------------------------------

    def test_mu_multi_decl_projection_conjunction(self) -> None:
        """Definite-description (mu) with multi-decl and conjunction predicate.

        Z RM §3.11 form:
        ``mu s : Ship; c : Class | s.class = c.class land s.name = c.name . s``

        Expected AST (once fixed):
        - Quantifier('mu', ['s'], Ship,
            body=Quantifier('mu', ['c'], Class,
              body=BinaryOp('land',
                BinaryOp('=', TupleProjection(s,'class'), TupleProjection(c,'class')),
                BinaryOp('=', TupleProjection(s,'name'), TupleProjection(c,'name'))),
              expression=Identifier('s')))
        """
        src = "mu s : Ship; c : Class | s.class = c.class land s.name = c.name . s"
        node = _parse(src)
        assert isinstance(node, Quantifier)
        assert node.quantifier == "mu"
        assert node.variables == ["s"]
        assert isinstance(node.domain, Identifier)
        assert node.domain.name == "Ship"
        inner = node.body
        assert isinstance(inner, Quantifier)
        assert inner.quantifier == "mu"
        assert inner.variables == ["c"]
        assert isinstance(inner.body, BinaryOp)
        assert inner.body.operator == "land"
        assert isinstance(inner.body.left, BinaryOp)
        assert inner.body.left.operator == "="
        assert isinstance(inner.body.right, BinaryOp)
        assert inner.body.right.operator == "="
        assert isinstance(inner.expression, Identifier)
        assert inner.expression.name == "s"

    # -----------------------------------------------------------------------
    # Test 10 — lambda multi-decl with conjunction predicate and projection body
    # -----------------------------------------------------------------------

    def test_lambda_multi_decl_projection_conjunction(self) -> None:
        """Lambda with multi-decl and conjunction predicate (Z RM §3.12).

        ``lambda s : Ship; c : Class | s.class = c.class land s.name = c.name . s.name``

        Expected AST (once fixed):
        - Quantifier('lambda', ['s'], Ship,
            body=Quantifier('lambda', ['c'], Class,
              body=BinaryOp('land',
                BinaryOp('=', TupleProjection(s,'class'), TupleProjection(c,'class')),
                BinaryOp('=', TupleProjection(s,'name'), TupleProjection(c,'name'))),
              expression=TupleProjection(s,'name')))
        """
        src = (
            "lambda s : Ship; c : Class"
            " | s.class = c.class land s.name = c.name . s.name"
        )
        node = _parse(src)
        assert isinstance(node, Quantifier)
        assert node.quantifier == "lambda"
        assert node.variables == ["s"]
        assert isinstance(node.domain, Identifier)
        assert node.domain.name == "Ship"
        inner = node.body
        assert isinstance(inner, Quantifier)
        assert inner.quantifier == "lambda"
        assert inner.variables == ["c"]
        assert isinstance(inner.body, BinaryOp)
        assert inner.body.operator == "land"

    # -----------------------------------------------------------------------
    # Test 11 — comprehension with no characteristic expression (Z RM §3.9)
    # -----------------------------------------------------------------------

    def test_comprehension_no_characteristic_expression(self) -> None:
        """Set comprehension without characteristic expression (signature default).

        Z RM §3.9 form:
        ``{ s : Ship; c : Class | s.class = c.class land s.name = c.name }``

        No '.' separator — the characteristic tuple defaults to the full signature.

        Expected AST (once fixed):
        - variables = ['s']
        - extra_declarations = [('c', Identifier('Class'))]
        - predicate = BinaryOp('land',
            BinaryOp('=', TupleProjection(s,'class'), TupleProjection(c,'class')),
            BinaryOp('=', TupleProjection(s,'name'), TupleProjection(c,'name')))
        - expression = None
        """
        src = "{ s : Ship; c : Class | s.class = c.class land s.name = c.name }"
        node = _parse(src)
        assert isinstance(node, SetComprehension)
        assert node.variables == ["s"]
        assert node.extra_declarations is not None
        assert len(node.extra_declarations) == 1
        assert node.extra_declarations[0][0] == "c"
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == "land"
        assert isinstance(node.predicate.left, BinaryOp)
        assert node.predicate.left.operator == "="
        assert isinstance(node.predicate.right, BinaryOp)
        assert node.predicate.right.operator == "="
        assert node.expression is None

    # -----------------------------------------------------------------------
    # Test 12 — RHS-first projection: direction independence
    # -----------------------------------------------------------------------

    def test_rhs_first_projection_order(self) -> None:
        """Comprehension with RHS-first projections to confirm direction independence.

        ``{ s : Ship; c : Class | c.class = s.class land c.name = s.name
            . {| name == s.name |} }``

        Expected AST (once fixed):
        - variables = ['s']
        - extra_declarations = [('c', Identifier('Class'))]
        - predicate = BinaryOp('land',
            BinaryOp('=', TupleProjection(c,'class'), TupleProjection(s,'class')),
            BinaryOp('=', TupleProjection(c,'name'), TupleProjection(s,'name')))
        - expression = Binding(...)
        """
        src = (
            "{ s : Ship; c : Class"
            " | c.class = s.class land c.name = s.name . {| name == s.name |} }"
        )
        node = _parse(src)
        assert isinstance(node, SetComprehension)
        assert node.variables == ["s"]
        assert node.extra_declarations is not None
        assert len(node.extra_declarations) == 1
        assert node.extra_declarations[0][0] == "c"
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == "land"
        assert isinstance(node.predicate.left, BinaryOp)
        assert node.predicate.left.operator == "="
        assert isinstance(node.predicate.right, BinaryOp)
        assert node.predicate.right.operator == "="
        assert isinstance(node.expression, Binding)

    # -----------------------------------------------------------------------
    # Test 13 — three decls, second-var projection on conjunction RHS
    # -----------------------------------------------------------------------

    def test_three_decl_second_var_projection_first(self) -> None:
        """Three-decl comprehension: second-decl projection fails in conjunction.

        ``{ s : Ship; c : Class; o : Outcome
            | c.class = s.class land o.ship = s.name . {| name == s.name |} }``

        Expected AST (once fixed):
        - variables = ['s']
        - extra_declarations = [('c', Identifier('Class')),
          ('o', Identifier('Outcome'))]
        - predicate = BinaryOp('land',
            BinaryOp('=', TupleProjection(c,'class'), TupleProjection(s,'class')),
            BinaryOp('=', TupleProjection(o,'ship'), TupleProjection(s,'name')))
        - expression = Binding(...)
        """
        src = (
            "{ s : Ship; c : Class; o : Outcome"
            " | c.class = s.class land o.ship = s.name . {| name == s.name |} }"
        )
        node = _parse(src)
        assert isinstance(node, SetComprehension)
        assert node.variables == ["s"]
        assert node.extra_declarations is not None
        assert len(node.extra_declarations) == 2
        assert node.extra_declarations[0][0] == "c"
        assert node.extra_declarations[1][0] == "o"
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == "land"
        assert isinstance(node.predicate.left, BinaryOp)
        assert node.predicate.left.operator == "="
        assert isinstance(node.predicate.right, BinaryOp)
        assert node.predicate.right.operator == "="
        assert isinstance(node.expression, Binding)


# ---------------------------------------------------------------------------
# TestMultiDeclLambdaGenerator — generator-level tests (Spivey canonical form)
# ---------------------------------------------------------------------------


def _gen_fuzz(src: str, *, nested: bool = False) -> str:
    """Parse src and generate LaTeX with use_fuzz=True.

    When nested=True, pass a dummy parent so the parenthesization rule fires.
    """
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    if isinstance(ast, Document):
        node: Expr = ast.items[0]  # type: ignore[assignment]
    else:
        node = ast
    gen = LaTeXGenerator(use_fuzz=True)
    parent: Expr | None = Identifier(name="_", line=0, column=0) if nested else None
    return gen.generate_expr(node, parent=parent)


class TestMultiDeclLambdaGenerator:
    """Generator tests: multi-decl lambda emits Spivey-canonical single-token form."""

    # -----------------------------------------------------------------------
    # Test 14 — two-decl lambda, top-level (no parens at top level)
    # -----------------------------------------------------------------------

    def test_two_decl_lambda_top_level(self) -> None:
        """Two-decl lambda at top level is always wrapped in parens in fuzz mode.

        Fuzz requires ``(\\lambda ...)`` unconditionally — not only when nested.
        The ``parent is not None`` guard has been removed; wrapping is now
        unconditional when ``use_fuzz=True``.

        ``lambda s : Ship; c : Class | s.class = c.class . s.class``
        should produce:
        ``(\\lambda s : Ship; c : Class | s.class = c.class @ s.class)``
        """
        result = _gen_fuzz(
            "lambda s : Ship; c : Class | s.class = c.class . s.class",
            nested=False,
        )
        assert result == r"(\lambda s : Ship; c : Class | s.class = c.class @ s.class)"

    # -----------------------------------------------------------------------
    # Test 15 — two-decl lambda, nested (parens in fuzz mode)
    # -----------------------------------------------------------------------

    def test_two_decl_lambda_nested_parens(self) -> None:
        """Two-decl lambda inside an expression is wrapped in parentheses.

        Expected:
        ``(\\lambda s : Ship; c : Class | s.class = c.class @ s.class)``
        """
        result = _gen_fuzz(
            "lambda s : Ship; c : Class | s.class = c.class . s.class",
            nested=True,
        )
        assert result == r"(\lambda s : Ship; c : Class | s.class = c.class @ s.class)"

    # -----------------------------------------------------------------------
    # Test 16 — three-decl lambda (arbitrary depth walker)
    # -----------------------------------------------------------------------

    def test_three_decl_lambda(self) -> None:
        """Three-decl lambda: walker handles arbitrary nesting depth.

        ``lambda s : Ship; c : Class; n : N | s.class = c.class . s.class``
        should produce:
        ``(\\lambda s : Ship; c : Class; n : \\nat | s.class = c.class @ s.class)``
        """
        result = _gen_fuzz(
            "lambda s : Ship; c : Class; n : N | s.class = c.class . s.class",
            nested=True,
        )
        assert (
            result
            == r"(\lambda s : Ship; c : Class; n : \nat | s.class = c.class @ s.class)"
        )

    # -----------------------------------------------------------------------
    # Test 17 — conjunction predicate passes through unchanged
    # -----------------------------------------------------------------------

    def test_two_decl_lambda_conjunction_predicate(self) -> None:
        """Conjunction predicate emitted verbatim after the single | separator.

        ``lambda s : Ship; c : Class | s.class = c.class land s.name = c.name . s.name``
        """
        result = _gen_fuzz(
            "lambda s : Ship; c : Class"
            " | s.class = c.class land s.name = c.name . s.name",
            nested=True,
        )
        assert "\\lambda s : Ship; c : Class |" in result
        assert "\\land" in result
        assert result.startswith("(")
        assert result.endswith(")")

    # -----------------------------------------------------------------------
    # Test 18 — single-decl with pipe still works (Quantifier("lambda") path)
    # -----------------------------------------------------------------------

    def test_single_decl_lambda_with_pipe(self) -> None:
        """Single-decl lambda with pipe: routes through _generate_lambda_quantifier.

        ``lambda s : Ship | s.name = 'X' . s.name``
        should produce single binding, no spurious nesting.
        """
        result = _gen_fuzz(
            "lambda s : Ship | s.name = 'X' . s.name",
            nested=True,
        )
        assert result.startswith("(\\lambda s : Ship |")
        assert "@" in result
