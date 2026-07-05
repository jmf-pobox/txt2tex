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
from txt2tex.codegen.paragraphs import NoFuzzLintItem, NoFuzzUnsupportedError


class _SchemasCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for schema constructs."""

    # Populated on LaTeXGenerator (see latex_gen.py __init__/_resolve_toc_depth);
    # declared here so mypy/pyright resolve self.nofuzz_lint_items in this file.
    nofuzz_lint_items: list[NoFuzzLintItem]

    @expr_register.register(SchemaText)
    def _generate_schema_text_expr(
        self, node: SchemaText, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for an inline schema text used as an Expr.

        Delegates to ``_generate_schema_text`` which returns the bracket
        form.  This handler is unreachable through the current grammar (see
        ``TestSchemaTextAsInlineExprRoutesToDisplayMath`` in
        ``tests/test_ra_in_zed_rejected.py``).  Passes ``block_kind=None``:
        a ``SchemaText`` reached as an ``Expr`` operand is always inline /
        display-math content, never a boxed Z paragraph, so RA taint here is
        a routing decision the taint system already made, not a rejection.
        """
        return self._generate_schema_text(node, None)

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

    def _emit_schema_inclusion(
        self, incl: SchemaInclusion, block_kind: str | None
    ) -> str:
        """Return the LaTeX fragment for one schema-inclusion declaration line.

        Forms emitted:
        - decoration=None:    ``Name``          (bare inclusion)
        - decoration="delta": ``\\Delta Name``  (state-and-operation)
        - decoration="xi":    ``\\Xi Name``     (read-only operation)

        Generic instantiation arguments are appended in brackets when present,
        e.g. ``\\Delta Stack[\\nat]``.  The caller appends ``\\\\`` when the
        item is not the last in the declaration list; this method returns only
        the content fragment.

        Every boxed caller renders this fragment straight into a boxed Z
        environment (``axdef``, ``gendef``, ``schema``, or ``zed``), so a
        relational-algebra generic argument -- e.g. ``Delta Stack[S join U]``
        -- is rejected here via ``_reject_ra_in_box`` rather than left to
        emit invalid ``\\mathrm{...}`` LaTeX inside the box.  ``block_kind``
        names the caller's box for an accurate error message; ``None`` marks
        an inline / display-math caller, where ``_reject_ra_in_box`` is a
        no-op and RA taint is left for the taint system to route.
        """
        name_latex = self._generate_identifier(
            Identifier(line=incl.line, column=incl.column, name=incl.name)
        )
        if incl.decoration == "delta":
            name_latex = rf"\Delta {name_latex}"
        elif incl.decoration == "xi":
            name_latex = rf"\Xi {name_latex}"

        if not incl.generics:
            return name_latex

        generic_latex_parts = [self.generate_expr(g) for g in incl.generics]
        full_latex = f"{name_latex}[{', '.join(generic_latex_parts)}]"
        for generic in incl.generics:
            self._reject_ra_in_box(generic, generic.line, full_latex, block_kind)
        return full_latex

    @item_register.register(Schema)
    def _generate_schema(self, node: Schema) -> list[str]:
        """Generate LaTeX for schema definition.

        Supports optional generic parameters and anonymous schemas (name=None).
        Multiple declarations appear on separate lines with line breaks.

        For schemas with pk-marked fields, uses dual-emit: a fuzz-checked copy
        inside ``\\setbox0=\\vbox{%…}`` (invisible to LaTeX output) and a
        rendered copy using the ``schemapk`` environment with
        ``\\underline{field}`` for each primary-key attribute.  A
        ``nofuzz_reason`` schema skips that dual-emit entirely -- fuzz never
        sees a ``schemanofuzz`` box, so there is no reason to keep an
        invisible checked copy around -- and renders once, with PK
        underlining if marked, staging a throwaway plain-``schema`` probe
        (see ``NoFuzzLintItem``) for the CLI's reject-if-clean lint.

        Processes schema names through _generate_identifier() for compound
        identifiers like S+, S*, S~ (partial support, GitHub #3 still open).
        """
        lines: list[str] = []
        # Source-level kind for user-facing diagnostics; the emitted LaTeX
        # environment (schema vs schemanofuzz) is chosen separately below.
        block_kind = "schema"

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
        schema_context = (
            f"{block_kind} {schema_name}" if schema_name else f"anonymous {block_kind}"
        )

        # Detect PK fields early so we know whether dual-emit is needed.
        pk_vars: set[str] = set()
        if node.name is not None:
            pk_vars = {
                decl.variable
                for decl in node.declarations
                if isinstance(decl, Declaration) and decl.is_primary_key
            }

        # Build the begin line (reused for both copies when dual-emit).
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            begin_schema = f"\\begin{{schema}}{{{schema_name}}}[{params_str}]"
            begin_schemapk = f"\\begin{{schemapk}}{{{schema_name}}}[{params_str}]"
        else:
            begin_schema = r"\begin{schema}{" + schema_name + "}"
            begin_schemapk = r"\begin{schemapk}{" + schema_name + "}"

        # Build declaration and where-clause body lines (shared between copies).
        # Returns (plain_lines, pk_lines) where pk_lines has \underline on PK vars.
        prev_z = self._in_z_paragraph
        self._in_z_paragraph = True
        plain_body: list[str] = []
        pk_body: list[str] = []
        try:
            # Generate declarations on separate lines
            if node.declarations:
                for i, decl in enumerate(node.declarations):
                    if isinstance(decl, SchemaInclusion):
                        decl_line = self._emit_schema_inclusion(decl, block_kind)
                        plain_body.append(
                            f"{decl_line} \\\\"
                            if i < len(node.declarations) - 1
                            else decl_line
                        )
                        pk_body.append(plain_body[-1])
                    else:
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
                                parts = type_latex.split(pattern, 1)
                                if len(parts) == 2:
                                    second_part = pattern.split()[-1] + " " + parts[1]
                                    type_latex = (
                                        parts[0]
                                        + pattern.split()[0]
                                        + f" ({second_part})"
                                    )
                                    break

                        plain_decl_line = f"{var_latex} : {type_latex}"
                        self._reject_ra_in_box(
                            decl.type_expr,
                            decl.type_expr.line,
                            plain_decl_line,
                            block_kind,
                        )
                        self._check_overflow(
                            plain_decl_line,
                            decl.type_expr.line,
                            f"{schema_context} declaration",
                            f"{decl.variable} : ...",
                        )

                        sep = " \\\\" if i < len(node.declarations) - 1 else ""
                        plain_body.append(f"{plain_decl_line}{sep}")

                        # Wrap identifier in \underline for PK fields
                        if decl.variable in pk_vars:
                            pk_var_latex = rf"\underline{{{var_latex}}}"
                            pk_decl_line = f"{pk_var_latex} : {type_latex}"
                        else:
                            pk_decl_line = plain_decl_line
                        pk_body.append(f"{pk_decl_line}{sep}")

            # Generate where clause if predicate groups exist
            where_lines: list[str] = []
            if node.predicates and any(group for group in node.predicates):
                where_lines.append(r"\where")
                for group_idx, group in enumerate(node.predicates):
                    for pred_idx, pred in enumerate(group):
                        pred_latex = self.generate_expr(pred, parent=None)
                        self._reject_ra_in_box(pred, pred.line, pred_latex, block_kind)
                        self._check_overflow(
                            pred_latex,
                            pred.line,
                            f"{schema_context} where clause",
                        )
                        if pred_idx < len(group) - 1:
                            where_lines.append(f"{pred_latex} \\\\")
                        else:
                            where_lines.append(pred_latex)
                    if group_idx < len(node.predicates) - 1:
                        where_lines.append(r"\also")
        finally:
            self._in_z_paragraph = prev_z

        if node.nofuzz_reason is not None:
            # NOFUZZ: fuzz never sees this box, so render once -- with PK
            # underlining if marked -- instead of the checked+rendered
            # dual-emit a plain pk-marked schema needs.
            if node.generic_params:
                msg = (
                    "NOFUZZ does not support generic parameters yet — remove "
                    "the generic parameters or the NOFUZZ modifier."
                )
                raise NoFuzzUnsupportedError(msg)
            probe_snippet = "\n".join(
                [begin_schema, *plain_body, *where_lines, r"\end{schema}"]
            )
            self.nofuzz_lint_items.append(
                NoFuzzLintItem(
                    line=node.line,
                    reason=node.nofuzz_reason,
                    probe_snippet=probe_snippet,
                )
            )
            escaped_reason = self._escape_latex_text(node.nofuzz_reason)
            begin_schemanofuzz = (
                f"\\begin{{schemanofuzz}}{{{schema_name}}}{{{escaped_reason}}}"
            )
            lines.append(begin_schemanofuzz)
            lines.extend(pk_body if pk_vars else plain_body)
            lines.extend(where_lines)
            lines.append(r"\end{schemanofuzz}")
        elif pk_vars:
            # Dual-emit: fuzz-checked copy inside \vbox (invisible), then
            # rendered schemapk copy with \underline on PK fields.
            # Must use \setbox0=\vbox, not \savebox — fuzz.sty's schema
            # environment uses \halign which requires a \vbox context.
            lines.append(r"\setbox0=\vbox{%")
            lines.append(begin_schema)
            lines.extend(plain_body)
            lines.extend(where_lines)
            lines.append(r"\end{schema}%")
            lines.append("}")
            lines.append(begin_schemapk)
            lines.extend(pk_body)
            lines.extend(where_lines)
            lines.append(r"\end{schemapk}")
        else:
            lines.append(begin_schema)
            lines.extend(plain_body)
            lines.extend(where_lines)
            lines.append(r"\end{schema}")

        lines.append("")

        return lines

    def _generate_schema_text(self, node: SchemaText, block_kind: str | None) -> str:
        r"""Return the LaTeX fragment for an inline schema text body.

        Emits: ``[ decl1; decl2 | pred1 \land pred2 ]``

        Declaration separator is ``;`` (Z RM §3.6).  Predicates are joined
        with ``\land``.  When there are no predicates the form is
        ``[ decl1; decl2 ]``.  ``block_kind`` is forwarded to
        ``_emit_schema_inclusion`` so a nested schema-inclusion's generic
        arguments are checked for RA taint against the correct enclosing box.
        ``block_kind=None`` marks an inline / display-math caller, where no
        rejection applies.
        """
        # Build declaration fragment
        decl_parts: list[str] = []
        for decl in node.declarations:
            if isinstance(decl, SchemaInclusion):
                decl_parts.append(self._emit_schema_inclusion(decl, block_kind))
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

    def _reject_ra_in_schema_text_box(
        self, node: SchemaText, block_kind: str | None
    ) -> None:
        """Raise ``RaInZedError`` if any decl type or predicate is RA-tainted.

        ``_generate_schema_text`` renders every plain declaration's type and
        every predicate via ``generate_expr`` with no RA guard of its own --
        it is also reached as a plain ``Expr`` operand
        (``_generate_schema_text_expr``), where RA taint is a routing
        decision, not a rejection.  Call this guard only at boxed call sites,
        mirroring ``_generate_schema``'s own per-declaration and
        per-predicate guards above; ``block_kind=None`` is an explicit no-op
        -- the inline handler never calls this guard at all.  A nested
        ``SchemaInclusion`` declaration is skipped here (``continue``)
        because ``_generate_schema_text`` already forwards ``block_kind`` to
        ``_emit_schema_inclusion``, which guards the inclusion's own generic
        arguments.  Taint is checked before rendering so the common
        (untainted) path never pays for a redundant ``generate_expr`` call --
        ``_generate_schema_text`` renders every declaration and predicate
        again regardless.
        """
        if block_kind is None:
            return
        for decl in node.declarations:
            if isinstance(decl, SchemaInclusion):
                continue
            if self._is_ra_tainted(decl.type_expr):
                var_latex = self._generate_identifier(
                    Identifier(line=0, column=0, name=decl.variable)
                )
                type_latex = self.generate_expr(decl.type_expr)
                self._reject_ra_in_box(
                    decl.type_expr,
                    decl.type_expr.line,
                    f"{var_latex} : {type_latex}",
                    block_kind,
                )
        for pred in node.predicates:
            if self._is_ra_tainted(pred):
                pred_latex = self.generate_expr(pred, parent=None)
                self._reject_ra_in_box(pred, pred.line, pred_latex, block_kind)

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
            self._reject_ra_in_schema_text_box(node.body, "zed")
            rhs = self._generate_schema_text(node.body, "zed")
        elif isinstance(node.body, SchemaInclusion):
            rhs = self._emit_schema_inclusion(node.body, "zed")
        else:
            rhs = self.generate_expr(node.body)
            self._reject_ra_in_box(
                node.body, node.body.line, f"{lhs} \\defs {rhs}", "zed"
            )

        lines.append("\\begin{zed}")
        lines.append(f"{lhs} \\defs {rhs}")
        lines.append("\\end{zed}")
        lines.append("")
        return lines
