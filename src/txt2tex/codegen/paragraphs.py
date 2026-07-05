"""Codegen handlers for Z paragraph constructs.

Covers: GivenType, FreeType, SyntaxBlock, Abbreviation, AxDef, GenDef, Zed.

This mixin is composed into :class:`LaTeXGenerator` via multiple
inheritance.  Methods are byte-identical to their counterparts in the
pre-refactor monolithic ``latex_gen.py``; only their file location has
changed.
"""

from __future__ import annotations

from dataclasses import dataclass

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    Binding,
    Document,
    Expr,
    FreeType,
    GenDef,
    GivenType,
    Identifier,
    SchemaInclusion,
    SequenceLiteral,
    SetComprehension,
    SyntaxBlock,
    SyntaxDefinition,
    Zed,
)
from txt2tex.codegen._dispatch import CodegenDispatch, item_register


@dataclass(frozen=True)
class NoFuzzLintItem:
    """One NOFUZZ box's throwaway checked-form probe, staged for the lint.

    Populated during code generation wherever ``node.nofuzz_reason`` is
    set (``_generate_given_type``, ``_generate_free_type``,
    ``_generate_abbreviation``, ``_generate_axdef``, and schema's
    ``_generate_schema``); consumed by the CLI, once the full document has
    been generated, via ``LaTeXGenerator.nofuzz_lint_items``.

    ``probe_snippet`` is a complete, self-contained checked-box LaTeX
    fragment -- e.g. ``\\begin{axdef}...\\end{axdef}`` or
    ``\\begin{zed}...\\end{zed}`` -- built from the *same* body lines the
    real NOFUZZ box renders, but wrapped in the plain (fuzz-checked)
    environment instead of its ``*nofuzz`` twin.  The CLI drops this
    verbatim into a minimal document and asks fuzz whether it type-checks
    on its own.
    """

    line: int
    reason: str
    probe_snippet: str


class NoFuzzUnsupportedError(Exception):
    """Raised when a NOFUZZ modifier cannot be honored with valid output.

    Covers the cases that have no correct rendering: a box carrying generic
    parameters (the twin environments take no generic argument yet) and
    zed-cm (``--zed``) mode (the twin environments are undefined there, and
    that mode performs no type-checking, so a waiver is meaningless).
    Codegen rejects with an actionable message rather than emit broken
    LaTeX.
    """


class NoFuzzGenDefNotImplementedError(NoFuzzUnsupportedError):
    """Raised when a NOFUZZ modifier marks a ``gendef``.

    No ``gendefnofuzz`` LaTeX environment exists yet (unlike
    ``axdefnofuzz``/``zednofuzz``/``schemanofuzz``).  Rather than emit an
    undefined environment that would break compilation, codegen rejects
    the input with an actionable message pointing at the gap.
    """


class RaInZedError(Exception):
    """Raised when a relational-algebra construct sits inside a boxed Z paragraph.

    RA constructs (algebra, binding, GROUP/UNGROUP) are not Z; fuzz would
    reject the ``\\mathrm{...}`` macros the generator would otherwise emit
    inside a boxed Z environment (``zed``, ``schema``, ``axdef``, ``gendef``,
    ``syntax``).
    Unlike a top-level RA line -- which the consolidation pass silently
    routes to display math -- a boxed environment is an explicit request for
    a Z paragraph, so RA content there is a user error rather than something
    to relocate.  See docs/DESIGN.md, ADR "RA construct inside an explicit
    `zed` block -- hard rejection (issue #83)".
    """


class _ParagraphsCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for Z paragraph constructs."""

    # Populated on LaTeXGenerator (see latex_gen.py __init__/_resolve_toc_depth);
    # declared here so mypy/pyright resolve self.nofuzz_lint_items in this file.
    nofuzz_lint_items: list[NoFuzzLintItem]

    def _reject_ra_in_box(
        self, expr: Expr, line: int, rendered: str, block_kind: str | None
    ) -> None:
        """Raise ``RaInZedError`` if `expr` is RA-tainted inside a boxed paragraph.

        Called before appending the rendered line to a boxed Z paragraph's
        body (`block_kind` is ``"zed"``, ``"schema"``, ``"axdef"``,
        ``"gendef"``, or ``"syntax"``), so the invalid ``\\mathrm{...}`` LaTeX
        never reaches the box.  ``block_kind is None`` marks an inline /
        display-math call site instead -- there the enclosing expression is
        already routed to display math by the taint system, so
        ``\\mathrm{...}`` is valid LaTeX and no rejection applies.
        """
        if block_kind is None or not self._is_ra_tainted(expr):
            return
        article = "an" if block_kind[:1] in "aeiou" else "a"
        msg = (
            f"line {line}: relational-algebra expression `{rendered}` "
            f"cannot appear inside {article} `{block_kind}` block — write it "
            "at top level, where it renders as display math."
        )
        raise RaInZedError(msg)

    @item_register.register(GivenType)
    def _generate_given_type(self, node: GivenType) -> list[str]:
        """Generate LaTeX for given type declaration.

        ``nofuzz_reason`` (set by a preceding ``NOFUZZ:`` modifier) swaps
        the wrapper to ``zednofuzz`` and stages the plain-``zed`` probe for
        the CLI's reject-if-clean lint; the body -- ``[A, B, C]`` -- is
        identical either way.
        """
        lines: list[str] = []
        names_str = ", ".join(node.names)
        body = f"[{names_str}]"
        if node.nofuzz_reason is None:
            lines.append(f"\\begin{{zed}}{body}\\end{{zed}}")
        else:
            self.nofuzz_lint_items.append(
                NoFuzzLintItem(
                    line=node.line,
                    reason=node.nofuzz_reason,
                    probe_snippet=f"\\begin{{zed}}{body}\\end{{zed}}",
                )
            )
            escaped_reason = self._escape_latex_text(node.nofuzz_reason)
            lines.append(
                f"\\begin{{zednofuzz}}{{{escaped_reason}}}{body}\\end{{zednofuzz}}"
            )
        lines.append("")
        return lines

    @item_register.register(FreeType)
    def _generate_free_type(self, node: FreeType) -> list[str]:
        """Generate LaTeX for free type definition.

        Examples:
        - Status ::= active | inactive (simple branches)
        - Tree ::= stalk | leaf \\ldata N \\rdata |
          branch \\ldata Tree \\cross Tree \\rdata

        ``nofuzz_reason`` swaps the wrapper to ``zednofuzz`` and stages
        the plain-``zed`` probe for the CLI's reject-if-clean lint; see
        ``_generate_given_type`` for the identical pattern.
        """
        lines: list[str] = []
        block_kind = "zednofuzz" if node.nofuzz_reason is not None else "zed"

        # Generate each branch with proper LaTeX formatting
        branch_strs: list[str] = []
        for branch in node.branches:
            if branch.parameters is None:
                # Simple branch: just the name
                branch_strs.append(branch.name)
            else:
                # Parameterized constructor: name \\ldata params \\rdata
                # Special handling: if params is SequenceLiteral, extract contents
                # (user writes <<...>> in ASCII to represent constructor delimiters)
                if isinstance(branch.parameters, SequenceLiteral):
                    # Generate contents without sequence delimiters
                    # \ldata ... \rdata already provide the delimiters
                    if branch.parameters.elements:
                        param_expr = branch.parameters.elements[0]
                        params_latex = self.generate_expr(param_expr)
                        self._reject_ra_in_box(
                            param_expr, param_expr.line, params_latex, block_kind
                        )
                    else:
                        params_latex = ""
                else:
                    params_latex = self.generate_expr(branch.parameters)
                    self._reject_ra_in_box(
                        branch.parameters,
                        branch.parameters.line,
                        params_latex,
                        block_kind,
                    )
                branch_strs.append(f"{branch.name} \\ldata {params_latex} \\rdata")

        # Join branches with |
        branches_str = " | ".join(branch_strs)
        body = f"{node.name} ::= {branches_str}"

        if node.nofuzz_reason is None:
            lines.append(f"\\begin{{zed}}{body}\\end{{zed}}")
        else:
            self.nofuzz_lint_items.append(
                NoFuzzLintItem(
                    line=node.line,
                    reason=node.nofuzz_reason,
                    probe_snippet=f"\\begin{{zed}}{body}\\end{{zed}}",
                )
            )
            escaped_reason = self._escape_latex_text(node.nofuzz_reason)
            lines.append(
                f"\\begin{{zednofuzz}}{{{escaped_reason}}}{body}\\end{{zednofuzz}}"
            )
        lines.append("")
        return lines

    @item_register.register(SyntaxBlock)
    def _generate_syntax_block(self, node: SyntaxBlock) -> list[str]:
        """Generate LaTeX for syntax environment (aligned free type definitions).

        Generates column-aligned LaTeX with & separators:
        \\begin{syntax}
        TypeName & ::= & branch1 | branch2
        \\also
        AnotherType & ::= & branch1 \\\\
        & | & branch2
        \\end{syntax}
        """
        lines: list[str] = []
        lines.append("\\begin{syntax}")

        for group_idx, group in enumerate(node.groups):
            # Add \also between groups (but not before first group)
            if group_idx > 0:
                lines.append("\\also")

            for def_idx, definition in enumerate(group):
                # Generate branches for this definition
                branch_lines = self._generate_syntax_definition_branches(definition)

                # Determine if we need \\ at the end of this definition
                is_last_in_group = def_idx == len(group) - 1
                is_last_group = group_idx == len(node.groups) - 1
                needs_line_break = not (is_last_in_group and is_last_group)

                # First line: TypeName & ::= & branches
                first_line = branch_lines[0]
                if needs_line_break and len(branch_lines) == 1:
                    # Only one line and not the last: add \\
                    first_line += " \\\\"
                lines.append(first_line)

                # Continuation lines: & | & branches
                for cont_idx, continuation in enumerate(branch_lines[1:]):
                    is_last_continuation = cont_idx == len(branch_lines) - 2
                    if needs_line_break and is_last_continuation:
                        continuation += " \\\\"
                    lines.append(continuation)

        lines.append("\\end{syntax}")
        lines.append("")
        return lines

    def _generate_syntax_definition_branches(
        self, definition: SyntaxDefinition
    ) -> list[str]:
        """Generate branch lines for a single type definition in syntax block.

        Returns list of lines:
        - First line: "TypeName & ::= & branch1 | branch2 | ..."
        - Continuation lines (if any): "& | & branch3 | branch4 | ..."

        ``\\syntax`` is defined in terms of fuzz's ``\\@zed`` (fuzz.sty line
        232), so it is type-checked exactly like a ``zed`` block -- a
        relational-algebra branch parameter is rejected the same way.
        """
        # Generate LaTeX for each branch
        branch_strs: list[str] = []
        for branch in definition.branches:
            if branch.parameters is None:
                branch_strs.append(branch.name)
            else:
                # Generate parameter expression
                if isinstance(branch.parameters, SequenceLiteral):
                    if branch.parameters.elements:
                        param_expr = branch.parameters.elements[0]
                        params_latex = self.generate_expr(param_expr)
                        self._reject_ra_in_box(
                            param_expr, param_expr.line, params_latex, "syntax"
                        )
                    else:
                        params_latex = ""
                else:
                    params_latex = self.generate_expr(branch.parameters)
                    self._reject_ra_in_box(
                        branch.parameters,
                        branch.parameters.line,
                        params_latex,
                        "syntax",
                    )
                branch_strs.append(f"{branch.name} \\ldata {params_latex} \\rdata")

        # For now, put all branches on one line
        # Future enhancement: could split long lines across multiple rows
        branches_str = " | ".join(branch_strs)
        first_line = f"{definition.name} & ::= & {branches_str}"

        return [first_line]

    @item_register.register(Abbreviation)
    def _generate_abbreviation(self, node: Abbreviation) -> list[str]:
        r"""Generate LaTeX for abbreviation definition.

        Supports optional generic parameters.

        Emission depends on the RHS:
        - Pure Z RHS → ``\begin{zed} Name == Expr \end{zed}``. fuzz
          parses it as a standard Z abbreviation paragraph (Z RM
          §3.2.4 abbreviation uses literal ``==``, not ``\defs``;
          ``\defs`` is reserved for horizontal schema definition).
        - Relational RHS (algebra, binding, GROUP/UNGROUP) →
          ``\noindent$Name == Expr$`` outside any Z block. fuzz
          silently skips it; schemas/axdefs in the same document still
          type-check.

        This lets users write one operator (``==``) for both Z and relational
        definitions and have txt2tex pick the fuzz-compatible emission
        form automatically.

        Fuzz syntax requires generic parameters AFTER the name: Name[X, Y]
        not before: [X, Y]Name.

        Processes abbreviation names through _generate_identifier() for
        compound identifiers like R+, R*, R~ (partial support, GitHub #3
        still open).
        """
        lines: list[str] = []

        # Process name through _generate_identifier() for compound identifiers.
        name_latex = self._generate_identifier(
            Identifier(line=0, column=0, name=node.name),
        )

        # Decide wrapping before generating the RHS so the math-context flag
        # is set correctly for context-sensitive operators like o9 (→ \comp
        # inside zed, → \semi inside inline $...$ math). RA-tainted covers
        # both a literal relational construct and a reference to a name an
        # earlier RA abbreviation defined (fuzz never saw that name declared).
        is_relational_rhs = self._is_ra_tainted(node.expression)

        prev_z = self._in_z_paragraph
        self._in_z_paragraph = not is_relational_rhs
        try:
            expr_latex = self.generate_expr(node.expression)
        finally:
            self._in_z_paragraph = prev_z

        # Build the abbreviation body (without environment wrapping)
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            abbrev = f"{name_latex}[{params_str}] == {expr_latex}"
        else:
            abbrev = f"{name_latex} == {expr_latex}"

        # A relational-algebra RHS is already emitted as display math outside
        # any Z environment (fuzz never checks it, and RA is barred from a
        # box), so a NOFUZZ waiver has nothing to waive -- reject rather than
        # silently drop the note and the reject-if-clean probe.
        if is_relational_rhs and node.nofuzz_reason is not None:
            msg = (
                "NOFUZZ cannot be applied to a relational-algebra abbreviation "
                "— RA is rendered as display math outside any fuzz-checked box, "
                "so there is nothing to waive."
            )
            raise NoFuzzUnsupportedError(msg)

        # Generic abbreviations are rejected under NOFUZZ for the same reason
        # as generic axdef/schema: the twin environments do not render generic
        # parameters yet.  Keep the rule uniform across box kinds (and matching
        # the user guide) rather than silently accept it here.
        if node.generic_params and node.nofuzz_reason is not None:
            msg = (
                "NOFUZZ does not support generic parameters yet — remove the "
                "generic parameters or the NOFUZZ modifier."
            )
            raise NoFuzzUnsupportedError(msg)

        # Pick the wrapping based on RHS content
        if is_relational_rhs:
            # Dual-emit for binding set comprehensions: hidden copy with
            # tuple for fuzz validation, visible copy with binding for PDF.
            if (
                self.use_fuzz
                and isinstance(node.expression, SetComprehension)
                and isinstance(node.expression.expression, Binding)
            ):
                converted = self._replace_binding_with_tuple(node.expression)
                if not self._is_ra_tainted(converted):
                    if node.generic_params:
                        params_str = ", ".join(node.generic_params)
                        hidden_name = f"{name_latex}[{params_str}]"
                    else:
                        hidden_name = name_latex
                    lines.extend(self._emit_hidden_abbreviation(hidden_name, converted))
            # Relational RHS — emit outside any Z environment so fuzz silently
            # skips it.  When the RHS breaks across lines, wrap the whole
            # abbreviation in a single \begin{array}{l}: every \t{depth} break
            # inside it (comprehensions, quantifiers, RA line breaks) then
            # shares one left margin, exactly like the zed box's own \t{depth}
            # commands (jms ruling, fix/display-math-binding-indent).
            lines.append("\\noindent")
            if self._has_line_breaks(node.expression):
                lines.append(r"$\displaystyle")
                lines.append(r"\begin{array}{l}")
                lines.append(abbrev)
                lines.append(r"\end{array}$")
            else:
                lines.append(f"${abbrev}$")
        else:
            # Pure Z RHS — emit inside a zed paragraph for fuzz type-checking.
            # nofuzz_reason swaps the wrapper to zednofuzz and stages the
            # plain-zed probe for the CLI's reject-if-clean lint.
            block_kind = "zednofuzz" if node.nofuzz_reason is not None else "zed"
            self._check_overflow(
                abbrev,
                node.line,
                f"{block_kind} abbreviation",
                f"{node.name} == ...",
            )
            if node.nofuzz_reason is None:
                lines.append("\\begin{zed}")
                lines.append(abbrev)
                lines.append("\\end{zed}")
            else:
                self.nofuzz_lint_items.append(
                    NoFuzzLintItem(
                        line=node.line,
                        reason=node.nofuzz_reason,
                        probe_snippet="\n".join([r"\begin{zed}", abbrev, r"\end{zed}"]),
                    )
                )
                escaped_reason = self._escape_latex_text(node.nofuzz_reason)
                lines.append(f"\\begin{{zednofuzz}}{{{escaped_reason}}}")
                lines.append(abbrev)
                lines.append("\\end{zednofuzz}")

        lines.append("")
        return lines

    @item_register.register(AxDef)
    def _generate_axdef(self, node: AxDef) -> list[str]:
        """Generate LaTeX for axiomatic definition.

        Supports optional generic parameters.
        Multiple declarations appear on separate lines with line breaks.

        ``nofuzz_reason`` swaps the wrapper to ``axdefnofuzz{<reason>}``
        and stages a throwaway plain-``axdef`` probe (same body) for the
        CLI's reject-if-clean lint -- the declaration/where-clause body
        itself renders identically either way.
        """
        block_kind = "axdefnofuzz" if node.nofuzz_reason is not None else "axdef"
        body_lines: list[str] = []

        # All expression generation inside this block uses Z-paragraph context so
        # that context-sensitive operators (e.g. o9 → \comp) emit correctly.
        prev_z = self._in_z_paragraph
        self._in_z_paragraph = True
        try:
            # Generate declarations on separate lines
            if node.declarations:
                for i, decl in enumerate(node.declarations):
                    if isinstance(decl, SchemaInclusion):
                        decl_line = self._emit_schema_inclusion(decl, block_kind)
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
                        self._reject_ra_in_box(
                            decl.type_expr, decl.type_expr.line, decl_line, block_kind
                        )
                        self._check_overflow(
                            decl_line,
                            decl.type_expr.line,
                            f"{block_kind} declaration",
                            f"{decl.variable} : ...",
                        )

                    # Add line break after each declaration except the last
                    if i < len(node.declarations) - 1:
                        body_lines.append(f"{decl_line} \\\\")
                    else:
                        body_lines.append(decl_line)

            # Generate where clause if predicate groups exist
            if node.predicates and any(group for group in node.predicates):
                body_lines.append(r"\where")

                # Iterate through predicate groups (separated by blank lines)
                for group_idx, group in enumerate(node.predicates):
                    # Generate predicates in current group
                    for pred_idx, pred in enumerate(group):
                        # Pass parent=None for smart parenthesization
                        pred_latex = self.generate_expr(pred, parent=None)

                        self._reject_ra_in_box(pred, pred.line, pred_latex, block_kind)

                        # Auto-wrap long predicates; fall back to warning
                        self._check_overflow(
                            pred_latex,
                            pred.line,
                            f"{block_kind} where clause",
                        )

                        # Use \\ as separator within group
                        if pred_idx < len(group) - 1:
                            body_lines.append(f"{pred_latex} \\\\")
                        else:
                            body_lines.append(pred_latex)

                    # Add \also between groups (not after last group)
                    if group_idx < len(node.predicates) - 1:
                        body_lines.append(r"\also")
        finally:
            self._in_z_paragraph = prev_z

        generics_suffix = (
            f"[{', '.join(node.generic_params)}]" if node.generic_params else ""
        )

        if node.nofuzz_reason is None:
            lines: list[str] = [f"\\begin{{axdef}}{generics_suffix}"]
            lines.extend(body_lines)
            lines.append(r"\end{axdef}")
            lines.append("")
            return lines

        if node.generic_params:
            msg = (
                "NOFUZZ does not support generic parameters yet — remove the "
                "generic parameters or the NOFUZZ modifier."
            )
            raise NoFuzzUnsupportedError(msg)

        probe_snippet = "\n".join(
            [f"\\begin{{axdef}}{generics_suffix}", *body_lines, r"\end{axdef}"]
        )
        self.nofuzz_lint_items.append(
            NoFuzzLintItem(
                line=node.line, reason=node.nofuzz_reason, probe_snippet=probe_snippet
            )
        )
        escaped_reason = self._escape_latex_text(node.nofuzz_reason)
        lines = [f"\\begin{{axdefnofuzz}}{{{escaped_reason}}}{generics_suffix}"]
        lines.extend(body_lines)
        lines.append(r"\end{axdefnofuzz}")
        lines.append("")
        return lines

    @item_register.register(GenDef)
    def _generate_gendef(self, node: GenDef) -> list[str]:
        """Generate LaTeX for generic definition.

        Generic definitions always have generic parameters (required).
        Multiple declarations appear on separate lines with line breaks.

        Raises:
            NoFuzzGenDefNotImplementedError: if ``node.nofuzz_reason`` is
                set.  No ``gendefnofuzz`` environment exists yet -- see
                the exception's docstring.
        """
        if node.nofuzz_reason is not None:
            msg = (
                "gendefnofuzz not yet implemented — mark support pending "
                "(NOFUZZ cannot be applied to a gendef block)"
            )
            raise NoFuzzGenDefNotImplementedError(msg)

        lines: list[str] = []

        # Generic parameters are always present for gendef
        params_str = ", ".join(node.generic_params)
        lines.append(f"\\begin{{gendef}}[{params_str}]")

        # All expression generation inside this block uses Z-paragraph context.
        prev_z = self._in_z_paragraph
        self._in_z_paragraph = True
        try:
            # Generate declarations on separate lines
            if node.declarations:
                for i, decl in enumerate(node.declarations):
                    if isinstance(decl, SchemaInclusion):
                        decl_line = f"  {self._emit_schema_inclusion(decl, 'gendef')}"
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
                        decl_line = f"  {var_latex}: {type_latex}"
                        self._reject_ra_in_box(
                            decl.type_expr, decl.type_expr.line, decl_line, "gendef"
                        )
                        self._check_overflow(
                            decl_line,
                            decl.type_expr.line,
                            "gendef declaration",
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

                        self._reject_ra_in_box(pred, pred.line, pred_latex, "gendef")

                        # Auto-wrap long predicates; fall back to warning
                        self._check_overflow(
                            pred_latex,
                            pred.line,
                            "gendef where clause",
                        )

                        # Fuzz requires \\ after each predicate except the last in group
                        if self.use_fuzz and pred_idx < len(group) - 1:
                            lines.append(f"  {pred_latex} \\\\")
                        else:
                            lines.append(f"  {pred_latex}")

                    # Add \also between groups (not after last group)
                    if group_idx < len(node.predicates) - 1:
                        lines.append(r"\also")
        finally:
            self._in_z_paragraph = prev_z

        lines.append(r"\end{gendef}")
        lines.append("")

        return lines

    @item_register.register(Zed)
    def _generate_zed(self, node: Zed) -> list[str]:
        """Generate LaTeX for zed block (unboxed paragraph).

        Zed blocks contain Z notation constructs:
        - Given types: [A, B, C]
        - Free types: Type ::= branch1 | branch2
        - Abbreviations: Name == expression
        - Predicates: forall x : N | P

        Supports mixed content (multiple construct types in one block).
        """
        lines: list[str] = [r"\begin{zed}"]
        lines.extend(self._generate_zed_body(node.content))
        lines.append(r"\end{zed}")
        lines.append("")
        return lines

    def _generate_zed_body(self, content: Expr | Document) -> list[str]:
        """Generate the inner lines of a zed block's body (no env wrapper).

        ``Zed`` does not carry a ``nofuzz_reason`` (NOFUZZ only marks the
        top-level box-producing nodes -- axdef/schema/gendef/given
        type/free type/abbreviation -- not an explicit ``zed ... end``
        block's internal items), so this always renders for the plain
        ``zed`` environment.
        """
        block_kind = "zed"
        lines: list[str] = []

        # All expression generation inside this block uses Z-paragraph context.
        prev_z = self._in_z_paragraph
        self._in_z_paragraph = True
        try:
            # Handle Document content (multiple items in zed block)
            if isinstance(content, Document):
                for idx, item in enumerate(content.items):
                    # Add \also separator before all items except the first
                    # Note: fuzz requires \also between Z paragraphs, not \\
                    if idx > 0:
                        lines.append(r"\also")

                    # Generate given types: [A, B, C]
                    if isinstance(item, GivenType):
                        names_str = ", ".join(item.names)
                        given_line = f"[{names_str}]"
                        self._check_overflow(
                            given_line,
                            item.line,
                            f"{block_kind} given types",
                        )
                        lines.append(given_line)

                    # Generate free types: Type ::= branch1 | branch2
                    elif isinstance(item, FreeType):
                        branch_strs: list[str] = []
                        for branch in item.branches:
                            if branch.parameters is None:
                                branch_strs.append(branch.name)
                            else:
                                params_latex = self.generate_expr(branch.parameters)
                                self._reject_ra_in_box(
                                    branch.parameters,
                                    branch.parameters.line,
                                    params_latex,
                                    block_kind,
                                )
                                branch_str = (
                                    f"{branch.name} \\ldata {params_latex} \\rdata"
                                )
                                branch_strs.append(branch_str)
                        branches_str = " | ".join(branch_strs)
                        free_type_line = f"{item.name} ::= {branches_str}"
                        self._check_overflow(
                            free_type_line,
                            item.line,
                            f"{block_kind} free type",
                            f"{item.name} ::= ...",
                        )
                        lines.append(free_type_line)

                    # Generate abbreviations: Name == expression
                    elif isinstance(item, Abbreviation):
                        expr_latex = self.generate_expr(item.expression)
                        name_latex = self._generate_identifier(
                            Identifier(line=0, column=0, name=item.name),
                        )
                        if item.generic_params:
                            params_str = ", ".join(item.generic_params)
                            abbrev_line = f"{name_latex}[{params_str}] == {expr_latex}"
                        else:
                            abbrev_line = f"{name_latex} == {expr_latex}"
                        self._reject_ra_in_box(
                            item.expression, item.line, abbrev_line, block_kind
                        )
                        self._check_overflow(
                            abbrev_line,
                            item.line,
                            f"{block_kind} abbreviation",
                            f"{item.name} == ...",
                        )
                        lines.append(abbrev_line)

                    # Generate expressions/predicates
                    elif isinstance(item, Expr):
                        content_latex = self.generate_expr(item)
                        self._reject_ra_in_box(
                            item, item.line, content_latex, block_kind
                        )
                        self._check_overflow(
                            content_latex,
                            item.line,
                            f"{block_kind} predicate",
                        )
                        lines.append(f"{content_latex}")
            else:
                # Single expression (backward compatible)
                content_latex = self.generate_expr(content)
                self._reject_ra_in_box(content, content.line, content_latex, block_kind)
                self._check_overflow(
                    content_latex,
                    content.line,
                    f"{block_kind} predicate",
                )
                lines.append(f"{content_latex}")
        finally:
            self._in_z_paragraph = prev_z

        return lines
