"""Codegen handlers for Z paragraph constructs.

Covers: GivenType, FreeType, SyntaxBlock, Abbreviation, AxDef, GenDef, Zed.

This mixin is composed into :class:`LaTeXGenerator` via multiple
inheritance.  Methods are byte-identical to their counterparts in the
pre-refactor monolithic ``latex_gen.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    Document,
    Expr,
    FreeType,
    GenDef,
    GivenType,
    Identifier,
    SchemaInclusion,
    SequenceLiteral,
    SyntaxBlock,
    SyntaxDefinition,
    Zed,
)
from txt2tex.codegen._dispatch import CodegenDispatch, item_register


class _ParagraphsCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for Z paragraph constructs."""

    @item_register.register(GivenType)
    def _generate_given_type(self, node: GivenType) -> list[str]:
        """Generate LaTeX for given type declaration."""
        lines: list[str] = []
        # Generate as: [A, B, C] in zed environment
        names_str = ", ".join(node.names)
        lines.append(f"\\begin{{zed}}[{names_str}]\\end{{zed}}")
        lines.append("")
        return lines

    @item_register.register(FreeType)
    def _generate_free_type(self, node: FreeType) -> list[str]:
        """Generate LaTeX for free type definition.

        Examples:
        - Status ::= active | inactive (simple branches)
        - Tree ::= stalk | leaf \\ldata N \\rdata |
          branch \\ldata Tree \\cross Tree \\rdata
        """
        lines: list[str] = []

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
                        params_latex = self.generate_expr(branch.parameters.elements[0])
                    else:
                        params_latex = ""
                else:
                    params_latex = self.generate_expr(branch.parameters)
                branch_strs.append(f"{branch.name} \\ldata {params_latex} \\rdata")

        # Join branches with |
        branches_str = " | ".join(branch_strs)

        # Wrap in zed environment for proper formatting
        lines.append(f"\\begin{{zed}}{node.name} ::= {branches_str}\\end{{zed}}")
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
                        params_latex = self.generate_expr(branch.parameters.elements[0])
                    else:
                        params_latex = ""
                else:
                    params_latex = self.generate_expr(branch.parameters)
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
        # inside zed, → \semi inside inline $...$ math).
        is_relational_rhs = self._expression_contains_dat_construct(node.expression)

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

        # Pick the wrapping based on RHS content
        if is_relational_rhs:
            # Relational RHS — emit outside any Z environment so fuzz silently skips
            lines.append("\\noindent")
            lines.append(f"${abbrev}$")
        else:
            # Pure Z RHS — emit inside a zed paragraph for fuzz type-checking
            self._check_overflow(
                abbrev,
                node.line,
                "zed abbreviation",
                f"{node.name} == ...",
            )
            lines.append("\\begin{zed}")
            lines.append(abbrev)
            lines.append("\\end{zed}")

        lines.append("")
        return lines

    @item_register.register(AxDef)
    def _generate_axdef(self, node: AxDef) -> list[str]:
        """Generate LaTeX for axiomatic definition.

        Supports optional generic parameters.
        Multiple declarations appear on separate lines with line breaks.
        """
        lines: list[str] = []

        # Add generic parameters if present
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            lines.append(f"\\begin{{axdef}}[{params_str}]")
        else:
            lines.append(r"\begin{axdef}")

        # All expression generation inside this block uses Z-paragraph context so
        # that context-sensitive operators (e.g. o9 → \comp) emit correctly.
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
                            "axdef declaration",
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
                            "axdef where clause",
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

        lines.append(r"\end{axdef}")
        lines.append("")

        return lines

    @item_register.register(GenDef)
    def _generate_gendef(self, node: GenDef) -> list[str]:
        """Generate LaTeX for generic definition.

        Generic definitions always have generic parameters (required).
        Multiple declarations appear on separate lines with line breaks.
        """
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
                        decl_line = f"  {self._emit_schema_inclusion(decl)}"
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
        lines: list[str] = []

        lines.append(r"\begin{zed}")

        # All expression generation inside this block uses Z-paragraph context.
        prev_z = self._in_z_paragraph
        self._in_z_paragraph = True
        try:
            # Handle Document content (multiple items in zed block)
            if isinstance(node.content, Document):
                for idx, item in enumerate(node.content.items):
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
                            "zed given types",
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
                                branch_str = (
                                    f"{branch.name} \\ldata {params_latex} \\rdata"
                                )
                                branch_strs.append(branch_str)
                        branches_str = " | ".join(branch_strs)
                        free_type_line = f"{item.name} ::= {branches_str}"
                        self._check_overflow(
                            free_type_line,
                            item.line,
                            "zed free type",
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
                        self._check_overflow(
                            abbrev_line,
                            item.line,
                            "zed abbreviation",
                            f"{item.name} == ...",
                        )
                        lines.append(abbrev_line)

                    # Generate expressions/predicates
                    elif isinstance(item, Expr):
                        content_latex = self.generate_expr(item)
                        self._check_overflow(
                            content_latex,
                            item.line,
                            "zed predicate",
                        )
                        lines.append(f"{content_latex}")
            else:
                # Single expression (backward compatible)
                content_latex = self.generate_expr(node.content)
                self._check_overflow(
                    content_latex,
                    node.content.line,
                    "zed predicate",
                )
                lines.append(f"{content_latex}")
        finally:
            self._in_z_paragraph = prev_z

        lines.append(r"\end{zed}")
        lines.append("")

        return lines
