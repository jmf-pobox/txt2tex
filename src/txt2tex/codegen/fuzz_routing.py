"""Fuzz-vs-inline-math routing helpers.

Some AST nodes — algebra, bindings, GROUP/UNGROUP/EXTEND — cannot sit inside
a Z environment because fuzz rejects their syntax.  Abbreviation
emission inspects the right-hand side and switches between an in-Z
form (``\begin{zed}...\\end{zed}``) and a noindent inline-math form
(``\noindent$...$``) accordingly.  This mixin carries the inspector
and the type tuple it uses.

State is module-state by convention; method bodies are byte-identical
to their counterparts in the pre-refactor monolithic ``latex_gen.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import ClassVar, cast

from txt2tex.ast_nodes import (
    AxDef,
    Binding,
    Declaration,
    Divide,
    DocumentItem,
    Expr,
    ExtendAggregate,
    FreeType,
    GenDef,
    GivenType,
    Group,
    GroupAggregate,
    HorizDef,
    Identifier,
    NaturalJoin,
    Project,
    RelationRename,
    Restrict,
    Schema,
    SetComprehension,
    Tuple,
    Ungroup,
)
from txt2tex.codegen._dispatch import CodegenDispatch
from txt2tex.codegen.numeric_superscript import check_no_numeric_superscript


class _FuzzRoutingCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: helpers for routing emission between Z and inline math."""

    _DAT_EXPRESSION_TYPES: ClassVar[tuple[type, ...]] = (
        Restrict,
        Project,
        RelationRename,
        NaturalJoin,
        Divide,
        Binding,
        Group,
        GroupAggregate,
        ExtendAggregate,
        Ungroup,
    )

    def _walk_nested_values(self, value: object) -> Iterator[object]:
        """Yield ``value`` and every value nested beneath it, recursively.

        Field-agnostic: descends into dataclass fields, list/tuple elements,
        and dict values, regardless of which node type or container shape
        holds them.  This is what lets ``_expression_contains_dat_construct``
        and ``_expression_references_names`` see into every corner of the
        tree — a ``Binding.pairs: list[tuple[str, Expr]]``, a
        ``SetComprehension.extra_declarations: list[tuple[str, Expr]]``, or
        any future field shape — without enumerating node types by hand.
        """
        yield value
        if isinstance(value, (list, tuple)):
            items = cast("tuple[object, ...] | list[object]", value)
            for item in items:
                yield from self._walk_nested_values(item)
            return
        if isinstance(value, dict):
            mapping = cast("dict[object, object]", value)
            for nested in mapping.values():
                yield from self._walk_nested_values(nested)
            return
        fields = getattr(value, "__dataclass_fields__", None)
        if fields is None:
            return
        for field_name in fields:
            yield from self._walk_nested_values(getattr(value, field_name))

    def _expression_contains_dat_construct(self, expr: object) -> bool:
        """True if expr's AST tree contains any relational construct.

        Relational constructs (algebra, bindings, GROUP/UNGROUP) cannot sit
        inside a Z environment without fuzz rejecting their syntax.
        This recursive walk lets abbreviation emission switch between an
        in-zed form (pure Z RHS) and a noindent-math form (relational RHS).
        """
        return any(
            isinstance(node, self._DAT_EXPRESSION_TYPES)
            for node in self._walk_nested_values(expr)
        )

    def _expression_references_names(self, expr: object, names: frozenset[str]) -> bool:
        """True if expr's AST tree references any identifier in names.

        Used to propagate RA taint by reference: an abbreviation whose RHS
        mentions a name defined by an earlier RA (relational-algebra)
        abbreviation must also render as display math, since fuzz has never
        seen that name declared.  Walks the full field tree without
        quantifier-scope awareness — the same conservative over-approximation
        ``_expression_contains_dat_construct`` already uses.  Over-tainting a
        shadowed bound variable only pushes one extra line into display math;
        under-tainting would leave a real "not declared" fuzz error.
        """
        return any(
            isinstance(node, Identifier) and node.name in names
            for node in self._walk_nested_values(expr)
        )

    def _collect_fuzz_declared_names(self, item: DocumentItem) -> frozenset[str]:
        """Return names ``item`` declares directly to fuzz's type-checker.

        A name is genuinely known to fuzz when it comes from a ``given``
        type, an axdef/gendef/schema declaration signature, a free-type
        left-hand side, or a horizontal definition's (``Name defs RHS``)
        left-hand side — never from a display-math RA abbreviation, which
        fuzz never parses.  ``_is_ra_tainted`` consults the running union of
        these names (``self._fuzz_declared_names``) so a name declared here
        can never be tainted by an RA reference alone.  This is the "axdef
        bridge" pattern documented in ``FUZZ_VS_STD_LATEX.md``: declare the
        name's type in an axdef (or a horizontal definition), then
        reference it freely from RA notes.
        """
        if isinstance(item, GivenType):
            return frozenset(item.names)
        if isinstance(item, FreeType):
            return frozenset({item.name})
        if isinstance(item, HorizDef):
            return frozenset({item.name})
        if isinstance(item, (AxDef, GenDef, Schema)):
            return frozenset(
                decl.variable
                for decl in item.declarations
                if isinstance(decl, Declaration)
            )
        return frozenset()

    def _is_ra_tainted(self, expr: Expr) -> bool:
        """True if expr belongs outside the fuzz zed block.

        An expression is RA-tainted (display-math only) when it either
        contains a literal relational-algebra construct, or references a
        name that an earlier RA abbreviation defined and that fuzz has
        not otherwise seen declared (via ``given``, axdef/gendef/schema
        signature, or free-type).  Fuzz requires declare-before-use, so
        by the time an abbreviation is generated, ``self._ra_tainted_names``
        already holds every such RA name defined earlier in the document,
        minus any name the "axdef bridge" pattern has separately declared.
        """
        tainted_names = frozenset(self._ra_tainted_names) - frozenset(
            self._fuzz_declared_names
        )
        return self._expression_contains_dat_construct(
            expr
        ) or self._expression_references_names(expr, tainted_names)

    def _binding_to_tuple_expr(self, binding: Binding) -> Expr:
        """Convert a binding to the equivalent tuple expression for fuzz.

        Single-field: bare expression. Multi-field: tuple.
        """
        if len(binding.pairs) <= 1:
            if not binding.pairs:
                # Empty binding — return an empty-set placeholder
                return Identifier(
                    name="\\emptyset", line=binding.line, column=binding.column
                )
            return binding.pairs[0][1]
        return Tuple(
            elements=[v for _, v in binding.pairs],
            line=binding.line,
            column=binding.column,
        )

    def _replace_binding_with_tuple(self, node: SetComprehension) -> SetComprehension:
        """Return a fuzz-safe copy of the set comprehension.

        If the characteristic expression is a Binding, replace with
        the equivalent tuple so fuzz can validate the types.
        """
        if not isinstance(node.expression, Binding):
            return node
        return SetComprehension(
            variables=node.variables,
            domain=node.domain,
            predicate=node.predicate,
            expression=self._binding_to_tuple_expr(node.expression),
            extra_declarations=node.extra_declarations,
            line_break_after_pipe=node.line_break_after_pipe,
            line_break_after_bullet=node.line_break_after_bullet,
            line=node.line,
            column=node.column,
        )

    def _emit_hidden_abbreviation(self, name_latex: str, expr: Expr) -> list[str]:
        r"""Emit a hidden fuzz-validation abbreviation inside \\setbox0=\\vbox{%...}.

        The box is discarded at typeset time but fuzz reads and validates it.
        Sets ``_in_hidden_fuzz_block`` so nested generators suppress
        \begin{array} wrapping that fuzz would reject.
        """
        # This is the shared fuzz-checked-box emission point for every
        # SetComprehension (standalone top-level, and the binding-to-tuple
        # dual-emit for an RA abbreviation): a numeric `^` base heading in
        # here would fuzz-misparse as relational iteration (jms ruling,
        # fix/tests-bugs-hygiene) -- reject with a source-line error before
        # rendering rather than let fuzz's cryptic `iter k base` surface.
        if isinstance(expr, SetComprehension):
            check_no_numeric_superscript(expr, {})

        prev_z = self._in_z_paragraph
        prev_hidden = self._in_hidden_fuzz_block
        self._in_z_paragraph = True
        self._in_hidden_fuzz_block = True
        try:
            expr_latex = self.generate_expr(expr)
        finally:
            self._in_z_paragraph = prev_z
            self._in_hidden_fuzz_block = prev_hidden
        return [
            r"\setbox0=\vbox{%",
            r"\begin{zed}",
            f"{name_latex} == {expr_latex}",
            r"\end{zed}%",
            "}",
        ]
