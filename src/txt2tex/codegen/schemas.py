"""Codegen handlers for schema constructs.

Covers: Schema, HorizDef, schema text (`[decl | pred]`), schema-calculus
operators (rename, compose, pipe, hide, project), and the
``_emit_schema_inclusion`` declaration helper.

This mixin is composed into :class:`LaTeXGenerator` via multiple
inheritance.  Methods are byte-identical to their counterparts in the
pre-refactor monolithic ``latex_gen.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Declaration,
    Expr,
    HorizDef,
    Identifier,
    Schema,
    SchemaCompose,
    SchemaHide,
    SchemaInclusion,
    SchemaPipe,
    SchemaProject,
    SchemaRename,
    SchemaText,
)
from txt2tex.codegen._dispatch import CodegenDispatch, expr_register, item_register


class _SchemasCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for schema constructs."""

    @expr_register.register(SchemaText)
    def _generate_schema_text_expr(
        self, node: SchemaText, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for an inline schema text used as an Expr.

        Delegates to ``_generate_schema_text`` which returns the bracket form.
        """
        return self._generate_schema_text(node)

    @expr_register.register(SchemaRename)
    def _generate_schema_rename(
        self, node: SchemaRename, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for schema renaming (Z RM §3.11).

        Renders ``S[new/old, ...]`` in math mode.  Per Z RM §3.11 the new
        name appears first, the old name second.  The brackets and ``/``
        separators are literal LaTeX — no special macro is needed.

        Examples:
        - S[a/b]      → S[a/b]   (a is new name, b is old name)
        - S[a/b, c/d] → S[a/b, c/d]
        - S'[a/b]     → S'[a/b]
        """
        schema_latex = self.generate_expr(node.schema)
        pairs_latex = ", ".join(
            f"{new_name}/{old_name}" for new_name, old_name in node.pairs
        )
        return f"{schema_latex}[{pairs_latex}]"

    @expr_register.register(SchemaCompose)
    def _generate_schema_compose(
        self, node: SchemaCompose, parent: Expr | None = None
    ) -> str:
        r"""Generate LaTeX for schema composition (Z RM §3.11).

        Renders ``S ; T`` as ``S \semi T``.
        The ``\semi`` macro is defined in fuzz.sty (line 295) and zed-cm.sty
        (line 493).  No preamble change is needed.

        Examples:
        - OpA ; OpB  → OpA \semi OpB
        """
        left_latex = self.generate_expr(node.left)
        right_latex = self.generate_expr(node.right)
        return f"{left_latex} \\semi {right_latex}"

    @expr_register.register(SchemaPipe)
    def _generate_schema_pipe(
        self, node: SchemaPipe, parent: Expr | None = None
    ) -> str:
        r"""Generate LaTeX for schema piping (Z RM §3.11).

        Renders ``S >> T`` as ``S \pipe T``.
        The ``\pipe`` macro is defined in fuzz.sty (line 296) and zed-cm.sty
        (line 494).

        Examples:
        - Send >> Receive  → Send \pipe Receive
        """
        left_latex = self.generate_expr(node.left)
        right_latex = self.generate_expr(node.right)
        return f"{left_latex} \\pipe {right_latex}"

    @expr_register.register(SchemaHide)
    def _generate_schema_hide(
        self, node: SchemaHide, parent: Expr | None = None
    ) -> str:
        r"""Generate LaTeX for schema hiding (Z RM §3.11).

        Renders ``S hide (x, y)`` as ``S \hide (x, y)``.
        The ``\hide`` macro is defined in fuzz.sty (line 300) and zed-cm.sty
        (line 497).

        Examples:
        - S hide (x)      → S \hide (x)
        - S hide (x, y)   → S \hide (x, y)
        """
        schema_latex = self.generate_expr(node.schema)
        names_latex = ", ".join(node.names)
        return f"{schema_latex} \\hide ({names_latex})"

    @expr_register.register(SchemaProject)
    def _generate_schema_project(
        self, node: SchemaProject, parent: Expr | None = None
    ) -> str:
        r"""Generate LaTeX for schema projection (Z RM §3.11).

        Renders ``S project T`` as ``S \project T``.
        The ``\project`` macro is defined in fuzz.sty (line 302) and
        zed-cm.sty (line 499).

        Examples:
        - S project T  → S \project T
        """
        left_latex = self.generate_expr(node.left)
        right_latex = self.generate_expr(node.right)
        return f"{left_latex} \\project {right_latex}"

    def _emit_schema_inclusion(self, incl: SchemaInclusion) -> str:
        """Return the LaTeX fragment for one schema-inclusion declaration line.

        Forms emitted:
        - decoration=None:    ``Name``          (bare inclusion)
        - decoration="delta": ``\\Delta Name``  (state-and-operation)
        - decoration="xi":    ``\\Xi Name``     (read-only operation)

        Generic instantiation arguments are appended in brackets when present,
        e.g. ``\\Delta Stack[\\nat]``.  The caller appends ``\\\\`` when the
        item is not the last in the declaration list; this method returns only
        the content fragment.
        """
        name_latex = self._generate_identifier(
            Identifier(line=incl.line, column=incl.column, name=incl.name)
        )
        if incl.generics:
            generic_str = ", ".join(self.generate_expr(g) for g in incl.generics)
            name_latex = f"{name_latex}[{generic_str}]"
        if incl.decoration == "delta":
            return rf"\Delta {name_latex}"
        if incl.decoration == "xi":
            return rf"\Xi {name_latex}"
        return name_latex

    @item_register.register(Schema)
    def _generate_schema(self, node: Schema) -> list[str]:
        """Generate LaTeX for schema definition.

        Supports optional generic parameters and anonymous schemas (name=None).
        Multiple declarations appear on separate lines with line breaks.

        Processes schema names through _generate_identifier() for compound
        identifiers like S+, S*, S~ (partial support, GitHub #3 still open).
        """
        lines: list[str] = []

        # Determine schema name (empty string for anonymous)
        # Process name through _generate_identifier() for compound identifiers
        # (S+, S*, S~).
        if node.name is not None:
            schema_name = self._generate_identifier(
                Identifier(line=0, column=0, name=node.name),
            )
        else:
            schema_name = ""

        # Context for overflow warnings
        schema_context = f"schema {schema_name}" if schema_name else "anonymous schema"

        # Add generic parameters if present
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            lines.append(f"\\begin{{schema}}{{{schema_name}}}[{params_str}]")
        else:
            lines.append(r"\begin{schema}{" + schema_name + "}")

        # All expression generation inside this block uses Z-paragraph context.
        prev_z = self._in_z_paragraph
        self._in_z_paragraph = True
        try:
            # Generate declarations on separate lines
            if node.declarations:
                for i, decl in enumerate(node.declarations):
                    if isinstance(decl, SchemaInclusion):
                        decl_line = self._emit_schema_inclusion(decl)
                    else:
                        # Process variable through identifier logic
                        var_latex = self._generate_identifier(
                            Identifier(line=0, column=0, name=decl.variable)
                        )
                        type_latex = self.generate_expr(decl.type_expr)
                        # Post-process: add parentheses for nested special functions
                        # Critical for fuzz: P (P Z) must be \power (\power Z)
                        # not \power \power Z which causes validation errors
                        special_ops = [
                            r"\power \power",
                            r"\power \finset",
                            r"\finset \power",
                            r"\seq \seq",
                            r"\iseq \iseq",
                            r"\bag \bag",
                        ]
                        for pattern in special_ops:
                            if pattern in type_latex:
                                # Find second operator and wrap from there
                                parts = type_latex.split(pattern, 1)
                                if len(parts) == 2:
                                    second_part = pattern.split()[-1] + " " + parts[1]
                                    type_latex = (
                                        parts[0]
                                        + pattern.split()[0]
                                        + f" ({second_part})"
                                    )
                                    break

                        # Build full declaration line for overflow check
                        decl_line = f"{var_latex} : {type_latex}"
                        self._check_overflow(
                            decl_line,
                            decl.type_expr.line,
                            f"{schema_context} declaration",
                            f"{decl.variable} : ...",
                        )

                    # Add line break after each declaration except the last
                    if i < len(node.declarations) - 1:
                        lines.append(f"{decl_line} \\\\")
                    else:
                        lines.append(decl_line)

            # Generate where clause if predicate groups exist
            if node.predicates and any(group for group in node.predicates):
                lines.append(r"\where")

                # Iterate through predicate groups (separated by blank lines)
                for group_idx, group in enumerate(node.predicates):
                    # Generate predicates in current group
                    for pred_idx, pred in enumerate(group):
                        # Pass parent=None for smart parenthesization
                        pred_latex = self.generate_expr(pred, parent=None)

                        # Auto-wrap long predicates; fall back to warning
                        self._check_overflow(
                            pred_latex,
                            pred.line,
                            f"{schema_context} where clause",
                        )

                        # Use \\ as separator within group
                        if pred_idx < len(group) - 1:
                            lines.append(f"{pred_latex} \\\\")
                        else:
                            lines.append(pred_latex)

                    # Add \also between groups (not after last group)
                    if group_idx < len(node.predicates) - 1:
                        lines.append(r"\also")
        finally:
            self._in_z_paragraph = prev_z

        lines.append(r"\end{schema}")

        # Emit a fuzz-compatible PK annotation after the schema box.
        # \underline{} is rejected by fuzz inside schema declaration positions,
        # so we record the primary-key set as a plain math statement outside
        # the box: \noindent$\mathrm{PK}(\mathrm{Name}) = \{attr1, attr2\}$
        # fuzz ignores content outside Z environments; pdflatex renders it.
        if node.name is not None:
            pk_attrs = [
                decl.variable
                for decl in node.declarations
                if isinstance(decl, Declaration) and decl.is_primary_key
            ]
            if pk_attrs:
                attrs_str = ", ".join(pk_attrs)
                lines.append(
                    rf"\noindent$\mathrm{{PK}}(\mathrm{{{schema_name}}})"
                    rf" = \{{{attrs_str}\}}$"
                )
                # Blank line + \smallskip so the next paragraph (often another
                # schema) gets visible breathing room from the PK annotation.
                lines.append("")
                lines.append(r"\smallskip")

        lines.append("")

        return lines

    def _generate_schema_text(self, node: SchemaText) -> str:
        r"""Return the LaTeX fragment for an inline schema text body.

        Emits: ``[ decl1; decl2 | pred1 \land pred2 ]``

        Declaration separator is ``;`` (Z RM §3.6).  Predicates are joined
        with ``\land``.  When there are no predicates the form is
        ``[ decl1; decl2 ]``.
        """
        # Build declaration fragment
        decl_parts: list[str] = []
        for decl in node.declarations:
            if isinstance(decl, SchemaInclusion):
                decl_parts.append(self._emit_schema_inclusion(decl))
            else:
                var_latex = self._generate_identifier(
                    Identifier(line=0, column=0, name=decl.variable)
                )
                type_latex = self.generate_expr(decl.type_expr)
                decl_parts.append(f"{var_latex} : {type_latex}")

        decl_str = "; ".join(decl_parts)

        # Build predicate fragment — flat list, joined with \land
        all_preds: list[str] = [
            self.generate_expr(pred, parent=None) for pred in node.predicates
        ]

        if not all_preds:
            return f"[ {decl_str} ]"

        pred_str = r" \land ".join(all_preds)
        return f"[ {decl_str} | {pred_str} ]"

    @item_register.register(HorizDef)
    def _generate_horiz_def(self, node: HorizDef) -> list[str]:
        r"""Generate LaTeX for a horizontal schema definition.

        Emits::

            \begin{zed}
            Name \defs RHS
            \end{zed}

        or, when generics are present::

            \begin{zed}
            Name[X, Y] \defs RHS
            \end{zed}

        The ``\defs`` macro is defined in fuzz.sty (line 280) as
        ``\widehat=`` — no preamble addition needed.
        """
        lines: list[str] = []

        # Build LHS: definition slot inside \begin{zed}.
        name_latex = self._generate_identifier(
            Identifier(line=node.line, column=node.column, name=node.name),
        )
        if node.generics:
            params_str = ", ".join(node.generics)
            lhs = f"{name_latex}[{params_str}]"
        else:
            lhs = name_latex

        # Build RHS
        if isinstance(node.body, SchemaText):
            rhs = self._generate_schema_text(node.body)
        elif isinstance(node.body, SchemaInclusion):
            rhs = self._emit_schema_inclusion(node.body)
        else:
            rhs = self.generate_expr(node.body)

        lines.append("\\begin{zed}")
        lines.append(f"{lhs} \\defs {rhs}")
        lines.append("\\end{zed}")
        lines.append("")
        return lines
