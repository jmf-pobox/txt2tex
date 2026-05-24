"""Parser rules for proof constructs.

Covers: ProofTree, ProofNode, CaseAnalysis, ArgueChain
(ARGUE / EQUIV / EQUAL), InfruleBlock.  Includes the small helper
``_smart_join_justification`` that is shared among the proof-rule
methods.

This mixin is composed into :class:`Parser` via multiple inheritance.
Method bodies are byte-identical to their counterparts in the
pre-refactor monolithic ``parser.py``; only their file location has
changed.
"""

from __future__ import annotations

import re
from typing import Literal

from txt2tex.ast_nodes import (
    ArgueChain,
    ArgueStep,
    CaseAnalysis,
    Expr,
    Identifier,
    InfruleBlock,
    ProofNode,
    ProofTree,
)
from txt2tex.parser_pkg._base import ParserBase, ParserError
from txt2tex.tokens import TokenType


class _ProofsParser(ParserBase):  # pyright: ignore[reportUnusedClass]
    """Mixin: rules for proof constructs."""

    def _smart_join_justification(self, parts: list[str]) -> str:
        """Join justification tokens intelligently.

        Strategy: Join with spaces (preserving word separation), then remove
        spaces around parentheses, brackets, and equals signs to compact
        mathematical notation.

        Examples:
        - ["length", "(", "<", "ple", ">", "^", "pl", ")"] → "length(<ple>^pl)"
        - ["commutativity", "of", "or"] → "commutativity of or"
        - ["x", "is", "not", "free", "in", "y", "|->", "z"] → "x is not free in y|->z"
        - ["def", ".", "of", "=>"] → "def. of =>" (preserves space before =>)
        """
        if not parts:
            return ""

        # First join with spaces (preserves all word separation)
        result = " ".join(parts)

        # Remove spaces around specific punctuation to compact notation
        # ONLY touch safe characters that aren't part of operators
        result = re.sub(r"\s*\(\s*", "(", result)  # Remove space before/after (
        result = re.sub(r"\s*\)\s*", ")", result)  # Remove space before/after )
        # Remove space around standalone = but NOT part of operators (=>, <=>)
        # Negative lookahead/lookbehind avoids matching = in operators
        result = re.sub(r"\s*(?<![<>])=(?![>])\s*", "=", result)
        result = re.sub(r"\s*\.", ".", result)  # Remove space BEFORE period only
        return re.sub(r"\s*,", ",", result)  # Remove space BEFORE comma only

        # DO NOT touch < or > as they appear in many operators (=>, ->>, etc.)
        # Sequences like <ple> will have internal spacing, but that's acceptable
        # to avoid breaking operator conversion in _escape_justification

    def _parse_argue_chain(self, connector: Literal["iff", "eq"] = "iff") -> ArgueChain:
        """Parse ARGUE:, EQUIV:, or EQUAL: block into an ArgueChain.

        Both EQUIV: and ARGUE: keywords produce connector='iff', rendered
        with \\Leftrightarrow between steps. EQUAL: produces connector='eq',
        rendered with = between steps (for expression equality chains).
        The generator uses a standard LaTeX array environment — not fuzz's
        argue environment — for reliable column spacing and adjustbox scaling.
        """
        start_token = self._advance()  # Consume 'ARGUE:', 'EQUIV:', or 'EQUAL:'
        self._skip_newlines()

        steps: list[ArgueStep] = []

        # Parse steps until we hit another structural element or end
        while not self._at_end() and not self._is_structural_token():
            # Consume leading connective if present on continuation lines.
            # Connector specificity: an EQUAL: block must never silently consume
            # a leading <=>, and an EQUIV/ARGUE block must never consume a leading =.
            # Note: = on a continuation line is consumed by _parse_comparison
            # (which crosses newlines), so the EQUALS branch rarely fires in
            # practice. The IFF branch fires because _parse_iff does NOT cross
            # newlines, so a bare <=> at line start reaches this check.
            if connector == "eq" and self._match(TokenType.EQUALS):
                self._advance()  # Consume leading '='
            elif connector == "iff" and self._match(TokenType.IFF):
                self._advance()  # Consume leading '<=>'
            elif connector == "eq" and self._match(TokenType.IFF):
                # <=> at the start of an EQUAL: continuation line means the
                # author used the wrong block type.  A clear message is more
                # helpful than the generic "unexpected token" from _parse_expr.
                tok = self._current()
                msg = (
                    "found '<=>' continuation in an EQUAL: chain; "
                    "use EQUIV: or ARGUE: for logical-equivalence chains"
                )
                raise ParserError(msg, tok)
            elif connector == "iff" and self._match(TokenType.EQUALS):
                # bare '=' at the start of an EQUIV:/ARGUE: continuation line
                # — the author may have intended EQUAL:.  Note: in practice
                # _parse_comparison absorbs 'a\n= b' as a single step, so
                # this branch fires only for a truly bare '=' with nothing
                # before it on the line, which is syntactically invalid.
                tok = self._current()
                msg = (
                    "found '=' continuation in an EQUIV:/ARGUE: chain; "
                    "use EQUAL: for expression-equality chains"
                )
                raise ParserError(msg, tok)

            # Parse expression
            expr = self._parse_expr()
            self._skip_newlines()

            # Check for optional justification [text]
            justification: str | None = None
            if self._match(TokenType.LBRACKET):
                self._advance()  # Consume '['

                # Collect justification text (all tokens until ']')
                just_parts: list[str] = []
                while not self._match(TokenType.RBRACKET) and not self._at_end():
                    if self._match(TokenType.NEWLINE):
                        break  # Justification on one line
                    just_parts.append(self._current().value)
                    self._advance()

                if not self._match(TokenType.RBRACKET):
                    raise ParserError(
                        "Expected closing ']' for justification", self._current()
                    )

                self._advance()  # Consume ']'
                # Join tokens smartly: add spaces only between consecutive identifiers
                justification = self._smart_join_justification(just_parts)

            # Create step
            steps.append(
                ArgueStep(
                    expression=expr,
                    justification=justification,
                    line=expr.line,
                    column=expr.column,
                )
            )

            self._skip_newlines()

        if not steps:
            raise ParserError(
                "Expected at least one step in ARGUE/EQUIV/EQUAL chain",
                self._current(),
            )

        return ArgueChain(
            steps=steps,
            connector=connector,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_infrule_block(self) -> InfruleBlock:
        """Parse INFRULE: block with premises, ---, and conclusion.

        Format:
          INFRULE:
          premise1 [label1]
          premise2 [label2]
          ---
          conclusion [label]
        """
        start_token = self._advance()  # Consume 'INFRULE:'
        self._skip_newlines()

        premises: list[tuple[Expr, str | None]] = []

        # Parse premises until we hit ---
        while not self._at_end() and not self._match(TokenType.DERIVE):
            # Check if we hit another structural token (error)
            if self._is_structural_token():
                raise ParserError(
                    "Expected '---' separator in INFRULE block", self._current()
                )

            # Parse premise expression
            expr = self._parse_expr()
            self._skip_newlines()

            # Check for optional label [text]
            label: str | None = None
            if self._match(TokenType.LBRACKET):
                self._advance()  # Consume '['

                # Collect label text (all tokens until ']')
                label_parts: list[str] = []
                while not self._match(TokenType.RBRACKET) and not self._at_end():
                    if self._match(TokenType.NEWLINE):
                        break  # Label on one line
                    label_parts.append(self._current().value)
                    self._advance()

                if not self._match(TokenType.RBRACKET):
                    raise ParserError("Expected closing ']' for label", self._current())

                self._advance()  # Consume ']'
                label = self._smart_join_justification(label_parts)

            premises.append((expr, label))
            self._skip_newlines()

        # Check for --- separator
        if not self._match(TokenType.DERIVE):
            raise ParserError(
                "Expected '---' separator in INFRULE block", self._current()
            )

        self._advance()  # Consume '---'
        self._skip_newlines()

        # Parse conclusion expression
        if self._at_end() or self._is_structural_token():
            raise ParserError(
                "Expected conclusion after '---' in INFRULE block", self._current()
            )

        conclusion_expr = self._parse_expr()
        self._skip_newlines()

        # Check for optional label [text]
        conclusion_label: str | None = None
        if self._match(TokenType.LBRACKET):
            self._advance()  # Consume '['

            # Collect label text
            conclusion_label_parts: list[str] = []
            while not self._match(TokenType.RBRACKET) and not self._at_end():
                if self._match(TokenType.NEWLINE):
                    break
                conclusion_label_parts.append(self._current().value)
                self._advance()

            if not self._match(TokenType.RBRACKET):
                raise ParserError(
                    "Expected closing ']' for conclusion label", self._current()
                )

            self._advance()  # Consume ']'
            conclusion_label = self._smart_join_justification(conclusion_label_parts)

        if not premises:
            raise ParserError(
                "Expected at least one premise in INFRULE block", self._current()
            )

        return InfruleBlock(
            premises=premises,
            conclusion=(conclusion_expr, conclusion_label),
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_proof_tree(self) -> ProofTree:
        """Parse proof tree with Path C syntax (conclusion with supporting proof).

        Supports top-level CASE analysis where proof starts with cases.
        """
        start_token = self._advance()  # Consume 'PROOF:'
        self._skip_newlines()

        if self._at_end() or self._is_structural_token():
            raise ParserError("Expected proof node after PROOF:", self._current())

        # Check if first item is a case keyword (top-level case analysis)
        if self._match(TokenType.IDENTIFIER) and self._current().value == "case":
            # Parse all top-level cases
            cases: list[CaseAnalysis] = []

            while (
                not self._at_end()
                and not self._is_structural_token()
                and self._match(TokenType.IDENTIFIER)
                and self._current().value == "case"
            ):
                case_analysis = self._parse_case_analysis(
                    base_indent=0, parent_indent=None
                )
                cases.append(case_analysis)
                self._skip_newlines()

            # Check if there's a final conclusion after the cases
            final_conclusion_expr: Expr | None = None
            final_justification: str | None = None

            if not self._at_end() and not self._is_structural_token():
                # Parse potential final conclusion (e.g., "q [or elim]")
                final_conclusion_node = self._parse_proof_node(
                    base_indent=0, parent_indent=None
                )
                final_conclusion_expr = final_conclusion_node.expression
                final_justification = final_conclusion_node.justification

            # Create synthetic conclusion node to wrap the cases
            # Use the final conclusion if present, otherwise placeholder
            if final_conclusion_expr is None:
                final_conclusion_expr = Identifier(
                    name="[case_analysis]",
                    line=start_token.line,
                    column=start_token.column,
                )
                final_justification = "case analysis"

            # Type hint for children: explicitly cast to expected union type
            children_list: list[ProofNode | CaseAnalysis] = list(cases)

            conclusion = ProofNode(
                expression=final_conclusion_expr,
                justification=final_justification,
                label=None,
                is_assumption=False,
                is_sibling=False,
                children=children_list,
                indent_level=0,
                line=start_token.line,
                column=start_token.column,
            )
        else:
            # Standard proof: parse the conclusion node
            conclusion = self._parse_proof_node(base_indent=0, parent_indent=None)

        return ProofTree(
            conclusion=conclusion, line=start_token.line, column=start_token.column
        )

    def _parse_proof_node(
        self, base_indent: int, parent_indent: int | None
    ) -> ProofNode:
        """Parse a single proof node with Path C syntax."""
        if self._at_end() or self._is_structural_token():
            raise ParserError("Expected proof node", self._current())

        line_token = self._current()
        current_indent = line_token.column

        # If we've dedented past the parent level, stop
        if parent_indent is not None and current_indent <= parent_indent:
            raise ParserError("Unexpected dedent in proof tree", self._current())

        # Check for assumption label [1], [2], etc.
        label: int | None = None
        if self._match(TokenType.LBRACKET):
            self._advance()  # Consume '['
            if self._match(TokenType.NUMBER):
                label = int(self._current().value)
                self._advance()
                if not self._match(TokenType.RBRACKET):
                    raise ParserError(
                        "Expected ']' after assumption label", self._current()
                    )
                self._advance()  # Consume ']'
            else:
                # Not a label, must be justification - back up by recreating the bracket
                # Actually, we can't back up easily. Let's handle this differently.
                # For now, assume [number] is always a label at the start of a line.
                raise ParserError(
                    "Expected number in assumption label", self._current()
                )

        # Check for sibling marker ::
        is_sibling = False
        if self._match(TokenType.DOUBLE_COLON):
            is_sibling = True
            self._advance()  # Consume '::'

        # Check for ellipsis ... (steps omitted in proof)
        if self._match(TokenType.ELLIPSIS):
            ellipsis_token = self._advance()
            # Create a text node representing omitted steps
            expr: Expr = Identifier(
                name="...",
                line=ellipsis_token.line,
                column=ellipsis_token.column,
            )
        else:
            # Parse the expression
            expr = self._parse_expr()

        # Check for justification [rule name]
        justification: str | None = None
        is_assumption = False
        if self._match(TokenType.LBRACKET):
            self._advance()  # Consume '['

            # Collect justification text
            just_parts: list[str] = []
            while not self._match(TokenType.RBRACKET) and not self._at_end():
                if self._match(TokenType.NEWLINE):
                    break
                just_parts.append(self._current().value)
                self._advance()

            if self._match(TokenType.RBRACKET):
                self._advance()  # Consume ']'
                # Join tokens smartly: add spaces only between consecutive identifiers
                justification = self._smart_join_justification(just_parts)
                # Check if this is the [assumption] keyword
                if justification == "assumption":
                    is_assumption = True

        self._skip_newlines()

        # Parse children (nodes indented more than current)
        children: list[ProofNode | CaseAnalysis] = []
        while not self._at_end() and not self._is_structural_token():
            if self._match(TokenType.NEWLINE):
                self._skip_newlines()
                if self._at_end() or self._is_structural_token():
                    break

            next_token = self._current()
            next_indent = next_token.column

            # Check if still indented relative to current node
            if next_indent <= current_indent:
                break

            # Check for case analysis
            if self._match(TokenType.IDENTIFIER) and self._current().value == "case":
                case_analysis = self._parse_case_analysis(
                    base_indent=base_indent, parent_indent=current_indent
                )
                children.append(case_analysis)
            else:
                # Regular proof node
                child = self._parse_proof_node(
                    base_indent=base_indent, parent_indent=current_indent
                )
                children.append(child)

        return ProofNode(
            expression=expr,
            justification=justification,
            label=label,
            is_assumption=is_assumption,
            is_sibling=is_sibling,
            children=children,
            indent_level=current_indent - base_indent,
            line=line_token.line,
            column=line_token.column,
        )

    def _parse_case_analysis(
        self, base_indent: int, parent_indent: int | None
    ) -> CaseAnalysis:
        """Parse case analysis: case name: followed by proof steps.

        parent_indent can be None for top-level cases.
        """
        if not self._match(TokenType.IDENTIFIER) or self._current().value != "case":
            raise ParserError("Expected 'case' keyword", self._current())

        case_token = self._advance()  # Consume 'case'

        # Parse case name - collect all tokens until colon
        case_parts: list[str] = []
        while not self._match(TokenType.COLON) and not self._at_end():
            if self._match(TokenType.NEWLINE):
                raise ParserError("Expected ':' after case name", self._current())
            case_parts.append(self._current().value)
            self._advance()

        if not case_parts:
            raise ParserError("Expected case name after 'case'", self._current())

        case_name = " ".join(case_parts)

        # Expect colon
        if not self._match(TokenType.COLON):
            raise ParserError("Expected ':' after case name", self._current())
        self._advance()  # Consume ':'

        self._skip_newlines()

        # Parse proof steps indented under this case
        steps: list[ProofNode] = []
        case_indent = case_token.column

        while not self._at_end() and not self._is_structural_token():
            if self._match(TokenType.NEWLINE):
                self._skip_newlines()
                if self._at_end() or self._is_structural_token():
                    break

            next_token = self._current()
            next_indent = next_token.column

            # Check if still indented relative to case
            if next_indent <= case_indent:
                break

            # Check if this is another case (sibling case)
            if self._match(TokenType.IDENTIFIER) and self._current().value == "case":
                break  # Stop parsing this case

            # Parse proof node for this case
            step = self._parse_proof_node(
                base_indent=base_indent, parent_indent=case_indent
            )
            steps.append(step)

        return CaseAnalysis(
            case_name=case_name,
            steps=steps,
            line=case_token.line,
            column=case_token.column,
        )
