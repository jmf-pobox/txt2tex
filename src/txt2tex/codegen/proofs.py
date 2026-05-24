"""Codegen handlers for proof constructs.

Covers: ProofTree, InfruleBlock, ArgueChain (ARGUE / EQUIV / EQUAL),
together with the proof-tree internals (ProofNode rendering, case
analysis, assumption scoping) and justification-label/text formatting
helpers.

This mixin is composed into :class:`LaTeXGenerator` via multiple
inheritance.  Methods are byte-identical to their counterparts in the
pre-refactor monolithic ``latex_gen.py``; only their file location has
changed.
"""

from __future__ import annotations

import re

from txt2tex.ast_nodes import (
    ArgueChain,
    BinaryOp,
    CaseAnalysis,
    Expr,
    Identifier,
    InfruleBlock,
    ProofNode,
    ProofTree,
)
from txt2tex.codegen._dispatch import CodegenDispatch, item_register


class _ProofsCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for proof constructs."""

    def _escape_justification(self, text: str) -> str:
        """Escape operators in justification text for LaTeX.

        CRITICAL: Operators must be replaced in order of length (longest first)
        to avoid partial matches. For example, |-> must be replaced before ->
        otherwise -> gets replaced first, leaving | and causing incorrect output.

        Also handles sequences like <> and <a, b, c> which must be processed
        BEFORE other operators containing < or >.
        """
        result = text

        # Handle specific operators FIRST before sequence matching
        # <=> must be replaced before sequences or it gets matched as <=>
        result = result.replace("<=>", r"$\Leftrightarrow$")  # Logical equivalence

        # Handle sequences (before other operators containing < or >)
        # Match sequences: < followed by anything except < or >, then >
        # This handles both <> (empty) and <a, b, c> (non-empty)
        result = re.sub(r"<\s*>", r"$\\langle \\rangle$", result)  # Empty sequence
        result = re.sub(r"<([^<>]+)>", r"$\\langle \1 \\rangle$", result)  # Non-empty

        # 5-character operators (process first)
        result = result.replace("77->", r"$\ffun$")  # Finite partial function

        # 4-character operators
        result = result.replace(">->>", r"$\bij$")  # Bijection
        result = result.replace("+->>", r"$\psurj$")  # Partial surjection
        result = result.replace("-->>", r"$\surj$")  # Total surjection

        # 3-character operators (process before 2-character)
        result = result.replace("<<|", r"$\ndres$")  # Domain corestriction
        result = result.replace("|>>", r"$\nrres$")  # Range corestriction
        result = result.replace("|->", r"$\mapsto$")  # Maplet (MUST be before ->)
        result = result.replace("<->", r"$\rel$")  # Relation type
        result = result.replace(">+>", r"$\pinj$")  # Partial injection
        result = result.replace("-|>", r"$\pinj$")  # Partial injection (alt)
        result = result.replace(">->", r"$\inj$")  # Total injection
        result = result.replace("+->", r"$\pfun$")  # Partial function

        # 2-character operators (process after all longer operators)
        result = result.replace("=>", r"$\Rightarrow$")  # Logical implication
        result = result.replace("<|", r"$\dres$")  # Domain restriction
        result = result.replace("|>", r"$\rres$")  # Range restriction
        result = result.replace("->", r"$\fun$")  # Total function (AFTER |-> and +->)
        result = result.replace("++", r"$\oplus$")  # Override
        result = result.replace("o9", r"$\semi$")  # Forward composition

        # Single-character operators
        result = result.replace("^", r"$\cat$")  # Sequence concatenation

        # Word-based operators (use word boundaries to avoid partial matches)
        # After migration: only LaTeX-style keywords are converted (not English)
        result = re.sub(r"\bland\b", r"$\\land$", result)
        result = re.sub(r"\blor\b", r"$\\lor$", result)
        result = re.sub(r"\blnot\b", r"$\\lnot$", result)
        result = re.sub(r"\belem\b", r"$\\in$", result)  # Set membership
        result = re.sub(r"\bdom\b", r"$\\dom$", result)
        result = re.sub(r"\bran\b", r"$\\ran$", result)
        result = re.sub(r"\bcomp\b", r"$\\comp$", result)
        result = re.sub(r"\binv\b", r"$\\inv$", result)
        result = re.sub(r"\bid\b", r"$\\id$", result)

        # Convert Z notation keywords to symbols (QA fixes)
        # Order matters: exists1+ before exists1 to avoid partial match
        result = re.sub(r"(?<!\\)exists1\+", r"$\\exists$", result)  # exists1+ → ∃
        result = re.sub(r"(?<!\\)\bexists1\b", r"$\\exists_1$", result)  # exists1 → ∃₁
        result = re.sub(r"(?<!\\)\bexists\b", r"$\\exists$", result)  # exists → ∃
        result = re.sub(r"(?<!\\)\bemptyset\b", r"$\\emptyset$", result)  # emptyset → ∅
        result = re.sub(r"(?<!\\)\bforall\b", r"$\\forall$", result)  # forall → ∀

        # Escape underscores in identifiers for prose rendering (not subscripts)
        # Must happen AFTER all operator replacements to avoid interfering
        # Pattern: word characters around underscore, not already in math mode
        # This handles cases like count_N, total_S in justification text
        # Escapes as count\_N (prose) not $count_N$ (subscript)
        return re.sub(
            r"(?<!\$)(\w+_\w+)(?!\$)", lambda m: m.group(1).replace("_", r"\_"), result
        )

    @item_register.register(ArgueChain)
    def _generate_argue_chain(self, node: ArgueChain) -> list[str]:
        r"""Generate LaTeX for equivalence or equality chain using array environment.

        EQUIV: and ARGUE: keywords generate \Leftrightarrow between steps.
        EQUAL: generates = between steps (for expression equality chains).
        Uses standard LaTeX array instead of argue environment for better control.
        Wraps array in display math \[...\] for proper spacing. Centers the block
        and right-aligns justifications. Auto-scales if wider than page.
        """
        lines: list[str] = []

        # Calculate available width and setup positioning
        if self._in_inline_part:
            # Inside part with leftskip: skip centering, align naturally
            lines.append(r"\savedleftskip=\leftskip")
            max_width = r"\dimexpr\textwidth-\savedleftskip\relax"
            # Just prevent extra indentation - leftskip handles positioning
            lines.append(r"\noindent")
        else:
            # Normal context: use centering
            max_width = r"\textwidth"
            lines.append(r"\begin{center}")

        # Wrap in adjustbox to scale if wider than available width
        lines.append(r"\adjustbox{max width=" + max_width + r"}{%")

        lines.append(r"$\displaystyle")
        # Use l@{\hspace{2em}}r: left-aligned expressions, right-aligned justifications
        lines.append(r"\begin{array}{l@{\hspace{2em}}r}")

        # Set context for line break formatting
        self._in_argue_block = True

        # Select connective: EQUIV/ARGUE use \Leftrightarrow; EQUAL uses =
        connective = r"= " if node.connector == "eq" else r"\Leftrightarrow "

        # Generate steps
        for i, step in enumerate(node.steps):
            expr_latex = self.generate_expr(step.expression)

            # No leading & - start directly with expression for flush left
            # First step: expression; subsequent: connective + expression
            line = expr_latex if i == 0 else connective + expr_latex

            # Add justification if present (flush right)
            if step.justification:
                escaped_just = self._escape_justification(step.justification)
                line += r" & [\mbox{" + escaped_just + "}]"

            # Add line break except for last line
            if i < len(node.steps) - 1:
                line += r" \\"

            lines.append(line)

        # Reset context
        self._in_argue_block = False

        lines.append(r"\end{array}$%")
        # Close adjustbox wrapper
        lines.append(r"}")
        # Close center environment (only if we opened it)
        if not self._in_inline_part:
            lines.append(r"\end{center}")
        # Add trailing spacing for separation from following content
        lines.append(r"\bigskip")
        lines.append("")

        return lines

    @item_register.register(InfruleBlock)
    def _generate_infrule_block(self, node: InfruleBlock) -> list[str]:
        r"""Generate LaTeX for infrule block.

        Uses fuzz's infrule environment with premises, \derive separator,
        and conclusion. Two-column format: expression & label.
        """
        lines: list[str] = []

        lines.append(r"\begin{infrule}")

        # Generate premises
        for premise_expr, label in node.premises:
            expr_latex = self.generate_expr(premise_expr)
            line = "  " + expr_latex + " &"

            # Add label if present
            if label:
                escaped_label = self._escape_justification(label)
                line += r" \mbox{" + escaped_label + "}"

            line += r" \\"
            lines.append(line)

        # Add \derive separator
        lines.append(r"  \derive \\")

        # Generate conclusion
        conclusion_expr, conclusion_label = node.conclusion
        conclusion_latex = self.generate_expr(conclusion_expr)
        line = "  " + conclusion_latex + " &"

        # Add label if present
        if conclusion_label:
            escaped_label = self._escape_justification(conclusion_label)
            line += r" \mbox{" + escaped_label + "}"

        lines.append(line)

        lines.append(r"\end{infrule}")
        lines.append("")

        return lines

    @item_register.register(ProofTree)
    def _generate_proof_tree(self, node: ProofTree) -> list[str]:
        """Generate LaTeX for proof tree (auto-scales if needed)."""
        lines: list[str] = []

        # Calculate available width and setup positioning
        if self._in_inline_part:
            # Inside part with leftskip: skip centering, align naturally
            lines.append(r"\savedleftskip=\leftskip")
            max_width = r"\dimexpr\textwidth-\savedleftskip\relax"
            # Just prevent extra indentation - leftskip handles positioning
            lines.append(r"\noindent")
        else:
            # Normal context: use centering
            max_width = r"\textwidth"
            lines.append(r"\begin{center}")

        # Wrap in adjustbox to scale if wider than available width
        lines.append(r"\adjustbox{max width=" + max_width + r"}{%")

        # Generate proof tree in display math
        proof_latex = self._generate_proof_node_infer(node.conclusion)
        lines.append(r"$\displaystyle")
        lines.append(proof_latex)
        lines.append(r"$%")
        # Close adjustbox wrapper
        lines.append(r"}")
        # Close center environment (only if we opened it)
        if not self._in_inline_part:
            lines.append(r"\end{center}")
        # Add trailing spacing for separation from following content
        lines.append(r"\bigskip")
        lines.append("")

        return lines

    def _format_boxed_assumption(self, expr: Expr, label: int | None) -> str:
        """Generate boxed assumption with corner brackets ⌈expr⌉[n]."""
        expr_latex = self.generate_expr(expr)
        # Use \ulcorner and \urcorner for corner brackets (requires amsmath)
        if label is not None:
            return f"\\ulcorner {expr_latex} \\urcorner^{{[{label}]}}"
        return f"\\ulcorner {expr_latex} \\urcorner"

    def _calculate_tree_depth(self, node: ProofNode | CaseAnalysis) -> int:
        """Calculate the depth of a proof tree (number of inference levels)."""
        if isinstance(node, CaseAnalysis):
            if not node.steps:
                return 0

            # For case analysis, count sequential steps (not just nested depth)
            # Sequential steps stack vertically, increasing height
            sibling_count = 0
            sequential_count = 0

            for step in node.steps:
                if step.is_sibling:
                    if sequential_count == 0:
                        sibling_count += 1
                    else:
                        # Sibling after sequential - treat as sequential
                        sequential_count += 1
                else:
                    sequential_count += 1

            # Height is based on sequential steps + 1 for sibling layer (if any)
            # Plus the depth of any nested children
            sibling_layer = 1 if sibling_count > 0 else 0
            max_child_depth = max(
                (self._calculate_tree_depth(step) for step in node.steps), default=0
            )

            return sibling_layer + sequential_count + max_child_depth

        if not node.children:
            return 0

        return 1 + max(self._calculate_tree_depth(child) for child in node.children)

    def _generate_proof_node_infer(self, node: ProofNode) -> str:
        """
        Generate \\infer macro for a proof node (bottom-up natural deduction).

        Returns LaTeX string for this node and its supporting premises.

        Handles synthetic top-level case analysis nodes.
        """
        # Check for synthetic top-level case analysis node
        # These are created when proof starts with CASE statements
        if (
            isinstance(node.expression, Identifier)
            and node.expression.name == "[case_analysis]"
            and node.justification == "case analysis"
        ):
            # Don't render the synthetic node itself, just its case children
            case_latexes: list[str] = []
            for child in node.children:
                if isinstance(child, CaseAnalysis):
                    # Use existing case analysis generation method
                    case_latexes.append(self._generate_case_analysis(child))
                else:
                    # Must be ProofNode
                    case_latexes.append(self._generate_proof_node_infer(child))

            # Join cases side-by-side with &
            return " & ".join(case_latexes) if case_latexes else ""

        # If this is an assumption node, it should appear as a boxed premise
        if node.is_assumption:
            # The assumption itself is a premise (leaf)
            assumption_latex = self._format_boxed_assumption(
                node.expression, node.label
            )

            # If it has children, they are derivations from this assumption
            # The assumption should be the base of the tree
            if not node.children:
                return assumption_latex

            # For now, treat the first child as the main derivation from the
            # assumption. This is a simplified approach - full natural deduction
            # requires dependency analysis.
            if len(node.children) == 1 and isinstance(node.children[0], ProofNode):
                single_child = node.children[0]
                # Generate child with assumption as its premise
                return self._generate_inference_from_assumption(
                    single_child, assumption_latex, node.label
                )

            # Multiple children or case analysis - need special handling
            return self._generate_complex_assumption_scope(node, assumption_latex)

        # Generate expression for conclusion
        expr_latex = self.generate_expr(node.expression)

        # Check for assumption reference FIRST (before checking children)
        # Pattern: "from N" where N is a digit
        # This should render as boxed assumption notation regardless of children
        if node.justification:
            just_lower = node.justification.lower()
            # Check if this is purely a "from N" reference (not "rule from N")
            from_only_match = re.match(r"^\s*from\s+(\d+)\s*$", just_lower)
            if from_only_match:
                ref_label = from_only_match.group(1)
                # Render as boxed assumption reference
                # If this node has children, they should be rendered below
                if node.children:
                    # Generate children as premises
                    child_latexes = [
                        self._generate_proof_node_infer(child)
                        for child in node.children
                        if isinstance(child, ProofNode)
                    ]
                    premises = "\n  ".join(child_latexes)
                    boxed = f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"
                    return f"\\infer{{{boxed}}}{{\n  {premises}\n}}"
                # Leaf node - just return the boxed reference
                return f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"

        # If no children, return expression (possibly with justification)
        if not node.children:
            # Check if justification indicates a reference (not a derivation rule)
            if node.justification:
                just_lower = node.justification.lower()
                # References like "copy", etc. should not be wrapped in \infer
                if "copy" in just_lower:
                    # Just return the expression - it's a reference
                    return expr_latex
                # Otherwise it's a derivation rule, wrap in \infer
                just = self._format_justification_label(node.justification)
                return f"\\infer[{just}]{{{expr_latex}}}{{}}"
            return expr_latex

        # Group children by siblings
        # Siblings (marked with ::) should be rendered side-by-side with &
        child_groups: list[list[str]] = []
        current_group: list[str] = []
        # Track case analysis with indices for raiseproof handling
        case_children: list[tuple[int, CaseAnalysis]] = []

        for idx, child in enumerate(node.children):
            if isinstance(child, CaseAnalysis):
                # Track case analysis for raiseproof handling
                case_children.append((idx, child))
                # Close current group before case
                if current_group:
                    child_groups.append(current_group)
                    current_group = []
            else:
                # child is ProofNode (only other type in union)
                child_latex = self._generate_proof_node_infer(child)

                if child.is_sibling and current_group:
                    # Add to current sibling group
                    current_group.append(child_latex)
                elif child.is_assumption and current_group:
                    # Assumptions should be laid out horizontally with siblings
                    # for proper spacing (e.g., in => elim with p => r & p)
                    current_group.append(child_latex)
                else:
                    # Start new group
                    if current_group:
                        child_groups.append(current_group)
                    current_group = [child_latex]

        # Add last group
        if current_group:
            child_groups.append(current_group)

        # Generate premises by joining siblings with &
        # Put & on its own line to avoid LaTeX parser issues with nested contexts
        non_case_premises = ["\n&\n".join(group) for group in child_groups]

        # If we have case analysis, apply raiseproof for vertical layout
        if case_children:
            # Identify disjunction siblings (for or-elim)
            disjunction_premises = [
                premise
                for group in child_groups
                for premise in group
                if r"\lor" in premise  # Check if this is a disjunction
            ]

            # Generate raised cases with staggered heights
            raised_cases: list[str] = []
            for case_position, (_idx, case) in enumerate(case_children):
                case_latex = self._generate_case_analysis(case)
                depth = self._calculate_tree_depth(case)

                # STAGGERED HEIGHT FORMULA:
                # First case: 6-8ex (minimal)
                # Subsequent cases: 18-24ex (much taller to avoid overlap)
                if case_position == 0:
                    # First case: minimal height
                    height = 6 + (depth * 2)  # Conservative for first case
                    # raiseproof naturally protects nested & from outer \infer alignment
                    raised = f"\\raiseproof{{{height}ex}}{{{case_latex}}}"
                else:
                    # Subsequent cases: taller + horizontal spacing
                    height = 18 + (depth * 4)  # Much taller for subsequent cases
                    # raiseproof naturally protects nested & from outer \infer alignment
                    raised = f"\\hskip 6em \\raiseproof{{{height}ex}}{{{case_latex}}}"

                raised_cases.append(raised)

            # Combine: disjunction premises first (if any), then raised case branches
            if disjunction_premises:
                all_premises = disjunction_premises + raised_cases
            else:
                # No disjunction - might be other premises before cases
                all_premises = non_case_premises + raised_cases

            # Put & on its own line to avoid LaTeX parser issues with nested contexts
            premises = "\n&\n".join(all_premises)
        else:
            # No case analysis - use normal premises
            premises = "\n  ".join(non_case_premises)

        # Generate justification label
        if node.justification:
            # Escape LaTeX special characters in justification
            just = self._format_justification_label(node.justification)
            return f"\\infer[{just}]{{{expr_latex}}}{{\n  {premises}\n}}"
        # No justification - use plain \infer
        return f"\\infer{{{expr_latex}}}{{\n  {premises}\n}}"

    def _generate_inference_from_assumption(
        self, node: ProofNode, assumption_latex: str, assumption_label: int | None
    ) -> str:
        """Generate an inference that derives from a boxed assumption."""
        expr_latex = self.generate_expr(node.expression)

        # If this node has no children, it directly derives from the assumption
        if not node.children:
            if node.justification:
                just = self._format_justification_label(node.justification)
                return f"\\infer[{just}]{{{expr_latex}}}{{{assumption_latex}}}"
            return f"\\infer{{{expr_latex}}}{{{assumption_latex}}}"

        # Node has children - generate them recursively
        # Children should ultimately reference the assumption as their premise
        return self._generate_proof_node_infer_with_assumption(
            node, assumption_latex, assumption_label
        )

    def _generate_proof_node_infer_with_assumption(
        self, node: ProofNode, assumption_latex: str, assumption_label: int | None
    ) -> str:
        """Generate inference node with leaves referencing the given assumption."""
        expr_latex = self.generate_expr(node.expression)

        # Base case: no children means this should derive from the assumption
        if not node.children:
            if node.justification:
                just_lower = node.justification.lower()
                # References like "from 1", "copy", etc. should not be wrapped in \infer
                if "from" in just_lower or "copy" in just_lower:
                    # Extract assumption label if present (e.g., "from 1" -> "1")
                    from_match = re.search(r"from\s+(\d+)", just_lower)
                    if from_match:
                        ref_label = from_match.group(1)
                        # Render as boxed assumption reference
                        return f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"
                    # Just return the expression - it's a reference without label
                    return expr_latex
                # Otherwise it's a derivation rule
                just = self._format_justification_label(node.justification)
                return f"\\infer[{just}]{{{expr_latex}}}{{{assumption_latex}}}"
            return expr_latex

        # Process children
        premises: list[str] = []
        for child in node.children:
            if isinstance(child, CaseAnalysis):
                premises.append(self._generate_case_analysis(child))
            elif child.is_assumption:
                # Child is its own assumption - process independently
                child_latex = self._generate_proof_node_infer(child)
                premises.append(child_latex)
            else:
                child_latex = self._generate_proof_node_infer_with_assumption(
                    child, assumption_latex, assumption_label
                )
                premises.append(child_latex)

        # Join premises
        premises_str = " & ".join(premises) if premises else assumption_latex

        # Generate with justification
        if node.justification:
            just = self._format_justification_label(node.justification)
            return f"\\infer[{just}]{{{expr_latex}}}{{{premises_str}}}"
        return f"\\infer{{{expr_latex}}}{{{premises_str}}}"

    def _generate_complex_assumption_scope(
        self, assumption_node: ProofNode, assumption_latex: str
    ) -> str:
        """Handle complex assumption scopes with multiple children or case analysis."""
        # Group children into sibling groups and sequential derivations
        # Siblings (marked with ::) are horizontal, non-siblings nest vertically

        children = assumption_node.children
        if not children:
            return assumption_latex

        # Separate siblings from sequential derivations
        sibling_group: list[ProofNode | CaseAnalysis] = []
        sequential: list[ProofNode | CaseAnalysis] = []

        for child in children:
            if isinstance(child, CaseAnalysis):
                # Case analysis can appear in sibling position
                if not sequential:
                    sibling_group.append(child)
                else:
                    sequential.append(child)
            elif child.is_sibling:
                # Only add to sibling group if we haven't started sequential yet
                if not sequential:
                    sibling_group.append(child)
                else:
                    # Sibling after non-sibling - this is a new context
                    sequential.append(child)
            else:
                # Non-sibling - starts sequential derivations
                sequential.append(child)

        # Generate sibling group (derives directly from assumption)
        sibling_latex_parts: list[str] = []
        for child in sibling_group:
            if isinstance(child, CaseAnalysis):
                sibling_latex_parts.append(self._generate_case_analysis(child))
            else:
                child_latex = self._generate_proof_node_infer_with_assumption(
                    child, assumption_latex, assumption_node.label
                )
                sibling_latex_parts.append(child_latex)

        # Combine siblings horizontally with &
        if sibling_latex_parts:
            current_premises = " & ".join(sibling_latex_parts)
        else:
            current_premises = assumption_latex

        # Now build sequential derivations vertically on top
        # Each sequential step uses the previous result as its premise
        for child in sequential:
            if isinstance(child, CaseAnalysis):
                child_latex = self._generate_case_analysis(child)
            # Generate the child
            # If it has children, we need to process them recursively
            elif child.children:
                # This node has children - need to generate a full subtree
                # The subtree should use current_premises as its base
                expr_latex = self.generate_expr(child.expression)

                # Generate children
                child_premises_parts: list[str] = []
                has_case_analysis = False
                for grandchild in child.children:
                    if isinstance(grandchild, CaseAnalysis):
                        child_premises_parts.append(
                            self._generate_case_analysis(grandchild)
                        )
                        has_case_analysis = True
                    else:
                        # Recurse to handle nested structure
                        grandchild_latex = self._generate_proof_node_infer(grandchild)
                        child_premises_parts.append(grandchild_latex)

                # Include siblings from parent scope as additional premises.
                # Special case: for or-elim with case analysis, only include
                # disjunction siblings. Other siblings (like extracted
                # conjuncts) are handled within case branches.
                if sibling_latex_parts and child_premises_parts:
                    if has_case_analysis:
                        # Only include disjunction siblings as top-level
                        # premises for or-elim
                        disjunction_siblings: list[str] = []
                        for i, sib_child in enumerate(sibling_group):
                            if (
                                isinstance(sib_child, ProofNode)
                                and isinstance(sib_child.expression, BinaryOp)
                                and sib_child.expression.operator == "or"
                            ):
                                disjunction_siblings.append(sibling_latex_parts[i])

                        # Apply \raiseproof to case branches for vertical
                        # layout. STAGGERED STRATEGY: Different cases get
                        # different heights + horizontal spacing
                        raised_cases: list[str] = []

                        # Collect all case indices first
                        case_indices: list[int] = []
                        for idx, grandchild in enumerate(child.children):
                            if isinstance(grandchild, CaseAnalysis):
                                case_indices.append(idx)

                        # Generate raised cases with staggered heights
                        for case_position, idx in enumerate(case_indices):
                            grandchild = child.children[idx]
                            depth = self._calculate_tree_depth(grandchild)
                            case_latex = child_premises_parts[idx]

                            # STAGGERED HEIGHT FORMULA:
                            # First case: 6-8ex (minimal)
                            # Subsequent cases: 18-24ex (much taller to
                            # avoid overlap)
                            if case_position == 0:
                                # First case: minimal height
                                height = 6 + (depth * 2)  # Conservative for first case
                                raised = f"\\raiseproof{{{height}ex}}{{{case_latex}}}"
                            else:
                                # Subsequent cases: taller + horizontal
                                # spacing
                                height = 18 + (
                                    depth * 4
                                )  # Much taller for subsequent cases
                                raised = (
                                    f"\\hskip 6em "
                                    f"\\raiseproof{{{height}ex}}"
                                    f"{{{case_latex}}}"
                                )

                            raised_cases.append(raised)

                        # Combine: disjunction siblings first, then raised
                        # case branches
                        all_premises = disjunction_siblings + raised_cases
                        child_premises = " & ".join(all_premises)
                    else:
                        # Not case analysis - include all siblings
                        all_premises = sibling_latex_parts + child_premises_parts
                        child_premises = " & ".join(all_premises)
                elif child_premises_parts:
                    child_premises = " & ".join(child_premises_parts)
                else:
                    child_premises = current_premises

                if child.justification:
                    just = self._format_justification_label(child.justification)
                    child_latex = f"\\infer[{just}]{{{expr_latex}}}{{{child_premises}}}"
                else:
                    child_latex = f"\\infer{{{expr_latex}}}{{{child_premises}}}"
            else:
                # No children - derive directly from current_premises
                expr_latex = self.generate_expr(child.expression)

                if child.justification:
                    just = self._format_justification_label(child.justification)
                    child_latex = (
                        f"\\infer[{just}]{{{expr_latex}}}{{{current_premises}}}"
                    )
                else:
                    child_latex = f"\\infer{{{expr_latex}}}{{{current_premises}}}"

            # This becomes the new premise for next step
            current_premises = child_latex

        return current_premises

    def _generate_case_analysis(self, case: CaseAnalysis) -> str:
        """Generate LaTeX for case analysis branch."""
        # For each case, generate the proof steps
        # Cases are typically rendered as separate inference branches
        if not case.steps:
            return f"\\mbox{{case {case.case_name}}}"

        # Generate the first step (usually the conclusion of this case)
        # In many cases, there's just one step per case
        if len(case.steps) == 1:
            return self._generate_proof_node_infer(case.steps[0])

        # Multiple steps - need to group siblings horizontally, rest vertically
        # Separate siblings from sequential steps
        sibling_group: list[ProofNode] = []
        sequential: list[ProofNode] = []

        for step in case.steps:
            if step.is_sibling:
                # Only add to sibling group if we haven't started sequential yet
                if not sequential:
                    sibling_group.append(step)
                else:
                    sequential.append(step)
            else:
                # Non-sibling - starts sequential derivations
                sequential.append(step)

        # Generate sibling group
        # When multiple siblings exist in a case, the LAST one wraps earlier
        # This ensures each \raiseproof contains exactly ONE top-level \infer
        if sibling_group:
            if len(sibling_group) == 1:
                # Single step - straightforward
                current_result = self._generate_proof_node_infer(sibling_group[0])
            else:
                # Multiple sibling steps: last step wraps earlier ones as premises
                # Generate earlier siblings as complete inference trees
                earlier_parts = [
                    self._generate_proof_node_infer(s) for s in sibling_group[:-1]
                ]

                # Last step becomes the outer wrapper
                last_step = sibling_group[-1]
                expr_latex = self.generate_expr(last_step.expression)

                # Combine earlier siblings with last step's own premises
                all_premises = earlier_parts.copy()
                if last_step.children:
                    # Last step has its own children/premises too
                    for child in last_step.children:
                        if isinstance(child, ProofNode):
                            all_premises.append(self._generate_proof_node_infer(child))
                        else:
                            # child is CaseAnalysis (only other type in union)
                            all_premises.append(self._generate_case_analysis(child))

                premises_str = " & ".join(all_premises) if all_premises else ""

                # Generate outer infer for last step
                if last_step.justification:
                    just = self._format_justification_label(last_step.justification)
                    current_result = (
                        f"\\infer[{just}]{{{expr_latex}}}{{{premises_str}}}"
                    )
                else:
                    current_result = f"\\infer{{{expr_latex}}}{{{premises_str}}}"
        else:
            # No siblings, start with first sequential
            if not sequential:
                return ""
            current_result = self._generate_proof_node_infer(sequential[0])
            sequential = sequential[1:]

        # Build sequential steps vertically on top
        for step in sequential:
            expr_latex = self.generate_expr(step.expression)

            if step.justification:
                just = self._format_justification_label(step.justification)
                current_result = f"\\infer[{just}]{{{expr_latex}}}{{{current_result}}}"
            else:
                current_result = f"\\infer{{{expr_latex}}}{{{current_result}}}"

        return current_result

    def _format_justification_label(self, just: str) -> str:
        """Format justification text for \\infer label.

        Converts patterns:
        - "=> intro from 1" → "\\Rightarrow\\textrm{-intro}^{[1]}" (discharge)
        - "and elim 1"      → "\\land\\textrm{-elim-1}" (projection subscript)
        - "false-intro"     → "false\\textrm{-intro}" (plain rule label)
        - "=> elim"         → "\\Rightarrow\\textrm{-elim}" (plain rule label)
        """
        # First, check for discharge pattern: "rule from N" or "rule[N]"
        # Match: operator + rule name + (from N | [N])
        discharge_pattern = r"^(.*?)\s+(intro|elim)\s+(?:from\s+(\d+)|\[(\d+)\])$"
        match = re.match(discharge_pattern, just)

        if match:
            operator_part = match.group(1).strip()
            rule_name = match.group(2)
            label_num = match.group(3) or match.group(4)

            # Convert operator to LaTeX (no $ delimiters - already in math mode)
            # CRITICAL: Process by length (longest first) to avoid partial matches
            op_latex: str = operator_part

            # 5-character operators
            op_latex = op_latex.replace("77->", r"\ffun")

            # 4-character operators
            op_latex = op_latex.replace(">->>", r"\bij")
            op_latex = op_latex.replace("+->>", r"\psurj")
            op_latex = op_latex.replace("-->>", r"\surj")

            # 3-character operators (process before 2-character)
            op_latex = op_latex.replace("<=>", r"\Leftrightarrow")
            op_latex = op_latex.replace("<<|", r"\ndres")
            op_latex = op_latex.replace("|>>", r"\nrres")
            op_latex = op_latex.replace("|->", r"\mapsto")  # MUST be before ->
            op_latex = op_latex.replace("<->", r"\rel")
            op_latex = op_latex.replace(">+>", r"\pinj")
            op_latex = op_latex.replace("-|>", r"\pinj")
            op_latex = op_latex.replace(">->", r"\inj")
            op_latex = op_latex.replace("+->", r"\pfun")

            # 2-character operators (process after longer operators)
            op_latex = op_latex.replace("=>", r"\Rightarrow")
            op_latex = op_latex.replace("<|", r"\dres")
            op_latex = op_latex.replace("|>", r"\rres")
            op_latex = op_latex.replace("->", r"\fun")  # AFTER |-> and +->
            op_latex = op_latex.replace("++", r"\oplus")
            op_latex = op_latex.replace("o9", r"\semi")

            # Word-based operators (both English and L-prefixed forms)
            op_latex = re.sub(r"\bland\b", r"\\land", op_latex)  # land → \land
            op_latex = re.sub(r"\blor\b", r"\\lor", op_latex)  # lor → \lor
            op_latex = re.sub(r"\blnot\b", r"\\lnot", op_latex)  # lnot → \lnot
            op_latex = re.sub(r"\band\b", r"\\land", op_latex)  # and → \land
            op_latex = re.sub(r"\bor\b", r"\\lor", op_latex)  # or → \lor
            op_latex = re.sub(r"\bnot\b", r"\\lnot", op_latex)  # not → \lnot
            op_latex = re.sub(r"\bin\b", r"\\in", op_latex)  # Set membership
            op_latex = re.sub(r"\bdom\b", r"\\dom", op_latex)
            op_latex = re.sub(r"\bran\b", r"\\ran", op_latex)
            op_latex = re.sub(r"\bcomp\b", r"\\comp", op_latex)
            op_latex = re.sub(r"\binv\b", r"\\inv", op_latex)
            op_latex = re.sub(r"\bid\b", r"\\id", op_latex)

            # Z notation keywords (QA fixes - matches _escape_justification)
            # Order matters: exists1+ before exists1 to avoid partial match
            op_latex = re.sub(r"exists1\+", r"\\exists", op_latex)  # exists1+ → ∃
            op_latex = re.sub(r"\bexists1\b", r"\\exists_1", op_latex)  # exists1 → ∃₁
            op_latex = re.sub(r"\bexists\b", r"\\exists", op_latex)  # exists → ∃
            op_latex = re.sub(r"\bemptyset\b", r"\\emptyset", op_latex)  # emptyset → ∅
            op_latex = re.sub(r"\bforall\b", r"\\forall", op_latex)  # forall → ∀

            # Format as: operator-rule^{[label]}
            # Use \textrm instead of \mbox to work correctly in math mode contexts
            return f"{op_latex}\\textrm{{-{rule_name}}}^{{[{label_num}]}}"

        # Check for rule subscript pattern: "operator rule N" (like "and elim 1")
        # Match: operator + rule name + number (1 or 2)
        subscript_pattern = r"^(.*?)\s+(intro|elim)\s*([12])$"
        match = re.match(subscript_pattern, just)

        if match:
            operator_part = match.group(1).strip()
            rule_name = match.group(2)
            subscript_num = match.group(3)

            # Convert operator to LaTeX (no $ delimiters - already in math mode)
            # CRITICAL: Process by length (longest first) to avoid partial matches
            op_latex = operator_part

            # 5-character operators
            op_latex = op_latex.replace("77->", r"\ffun")

            # 4-character operators
            op_latex = op_latex.replace(">->>", r"\bij")
            op_latex = op_latex.replace("+->>", r"\psurj")
            op_latex = op_latex.replace("-->>", r"\surj")

            # 3-character operators (process before 2-character)
            op_latex = op_latex.replace("<=>", r"\Leftrightarrow")
            op_latex = op_latex.replace("<<|", r"\ndres")
            op_latex = op_latex.replace("|>>", r"\nrres")
            op_latex = op_latex.replace("|->", r"\mapsto")  # MUST be before ->
            op_latex = op_latex.replace("<->", r"\rel")
            op_latex = op_latex.replace(">+>", r"\pinj")
            op_latex = op_latex.replace("-|>", r"\pinj")
            op_latex = op_latex.replace(">->", r"\inj")
            op_latex = op_latex.replace("+->", r"\pfun")

            # 2-character operators (process after longer operators)
            op_latex = op_latex.replace("=>", r"\Rightarrow")
            op_latex = op_latex.replace("<|", r"\dres")
            op_latex = op_latex.replace("|>", r"\rres")
            op_latex = op_latex.replace("->", r"\fun")  # AFTER |-> and +->
            op_latex = op_latex.replace("++", r"\oplus")
            op_latex = op_latex.replace("o9", r"\semi")

            # Word-based operators (both English and L-prefixed forms)
            op_latex = re.sub(r"\bland\b", r"\\land", op_latex)  # land → \land
            op_latex = re.sub(r"\blor\b", r"\\lor", op_latex)  # lor → \lor
            op_latex = re.sub(r"\blnot\b", r"\\lnot", op_latex)  # lnot → \lnot
            op_latex = re.sub(r"\band\b", r"\\land", op_latex)  # and → \land
            op_latex = re.sub(r"\bor\b", r"\\lor", op_latex)  # or → \lor
            op_latex = re.sub(r"\bnot\b", r"\\lnot", op_latex)  # not → \lnot
            op_latex = re.sub(r"\bin\b", r"\\in", op_latex)  # Set membership
            op_latex = re.sub(r"\bdom\b", r"\\dom", op_latex)
            op_latex = re.sub(r"\bran\b", r"\\ran", op_latex)
            op_latex = re.sub(r"\bcomp\b", r"\\comp", op_latex)
            op_latex = re.sub(r"\binv\b", r"\\inv", op_latex)
            op_latex = re.sub(r"\bid\b", r"\\id", op_latex)

            # Z notation keywords (QA fixes - matches _escape_justification)
            # Order matters: exists1+ before exists1 to avoid partial match
            op_latex = re.sub(r"exists1\+", r"\\exists", op_latex)  # exists1+ → ∃
            op_latex = re.sub(r"\bexists1\b", r"\\exists_1", op_latex)  # exists1 → ∃₁
            op_latex = re.sub(r"\bexists\b", r"\\exists", op_latex)  # exists → ∃
            op_latex = re.sub(r"\bemptyset\b", r"\\emptyset", op_latex)  # emptyset → ∅
            op_latex = re.sub(r"\bforall\b", r"\\forall", op_latex)  # forall → ∀

            # Format as: operator-rule-number (just regular text, no subscript)
            # Use \textrm instead of \mbox to work correctly in math mode contexts
            return f"{op_latex}\\textrm{{-{rule_name}-{subscript_num}}}"

        # Pattern 3: plain rule label (no discharge, no subscript).
        # Matches: "false-intro", "=> elim", "and intro", "lnot elim", etc.
        # The separator between operator and rule name may be whitespace or hyphen.
        plain_pattern = r"^(.*?)[\s-]+(intro|elim)$"
        match = re.match(plain_pattern, just)

        if match:
            operator_part = match.group(1).strip()
            rule_name = match.group(2)

            # Convert operator to LaTeX (no $ delimiters - already in math mode)
            # CRITICAL: Process by length (longest first) to avoid partial matches
            op_latex = operator_part

            # 5-character operators
            op_latex = op_latex.replace("77->", r"\ffun")

            # 4-character operators
            op_latex = op_latex.replace(">->>", r"\bij")
            op_latex = op_latex.replace("+->>", r"\psurj")
            op_latex = op_latex.replace("-->>", r"\surj")

            # 3-character operators (process before 2-character)
            op_latex = op_latex.replace("<=>", r"\Leftrightarrow")
            op_latex = op_latex.replace("<<|", r"\ndres")
            op_latex = op_latex.replace("|>>", r"\nrres")
            op_latex = op_latex.replace("|->", r"\mapsto")  # MUST be before ->
            op_latex = op_latex.replace("<->", r"\rel")
            op_latex = op_latex.replace(">+>", r"\pinj")
            op_latex = op_latex.replace("-|>", r"\pinj")
            op_latex = op_latex.replace(">->", r"\inj")
            op_latex = op_latex.replace("+->", r"\pfun")

            # 2-character operators (process after longer operators)
            op_latex = op_latex.replace("=>", r"\Rightarrow")
            op_latex = op_latex.replace("<|", r"\dres")
            op_latex = op_latex.replace("|>", r"\rres")
            op_latex = op_latex.replace("->", r"\fun")  # AFTER |-> and +->
            op_latex = op_latex.replace("++", r"\oplus")
            op_latex = op_latex.replace("o9", r"\semi")

            # Word-based operators (both English and L-prefixed forms)
            op_latex = re.sub(r"\bland\b", r"\\land", op_latex)  # land → \land
            op_latex = re.sub(r"\blor\b", r"\\lor", op_latex)  # lor → \lor
            op_latex = re.sub(r"\blnot\b", r"\\lnot", op_latex)  # lnot → \lnot
            op_latex = re.sub(r"\band\b", r"\\land", op_latex)  # and → \land
            op_latex = re.sub(r"\bor\b", r"\\lor", op_latex)  # or → \lor
            op_latex = re.sub(r"\bnot\b", r"\\lnot", op_latex)  # not → \lnot
            op_latex = re.sub(r"\bin\b", r"\\in", op_latex)  # Set membership
            op_latex = re.sub(r"\bdom\b", r"\\dom", op_latex)
            op_latex = re.sub(r"\bran\b", r"\\ran", op_latex)
            op_latex = re.sub(r"\bcomp\b", r"\\comp", op_latex)
            op_latex = re.sub(r"\binv\b", r"\\inv", op_latex)
            op_latex = re.sub(r"\bid\b", r"\\id", op_latex)

            # Z notation keywords (QA fixes - matches _escape_justification)
            # Order matters: exists1+ before exists1 to avoid partial match
            op_latex = re.sub(r"exists1\+", r"\\exists", op_latex)  # exists1+ → ∃
            op_latex = re.sub(r"\bexists1\b", r"\\exists_1", op_latex)  # exists1 → ∃₁
            op_latex = re.sub(r"\bexists\b", r"\\exists", op_latex)  # exists → ∃
            op_latex = re.sub(r"\bemptyset\b", r"\\emptyset", op_latex)  # emptyset → ∅
            op_latex = re.sub(r"\bforall\b", r"\\forall", op_latex)  # forall → ∀

            # Format as: operator-rule (tight, matching patterns 1 and 2)
            # Use \textrm instead of \mbox to work correctly in math mode contexts
            return f"{op_latex}\\textrm{{-{rule_name}}}"

        # No special pattern - process normally
        # CRITICAL: Process by length (longest first) to avoid partial matches
        result = just

        # 5-character operators
        result = result.replace("77->", r"\ffun")

        # 4-character operators
        result = result.replace(">->>", r"\bij")
        result = result.replace("+->>", r"\psurj")
        result = result.replace("-->>", r"\surj")

        # 3-character operators (process before 2-character)
        result = result.replace("<=>", r"\Leftrightarrow")
        result = result.replace("<<|", r"\ndres")
        result = result.replace("|>>", r"\nrres")
        result = result.replace("|->", r"\mapsto")  # MUST be before ->
        result = result.replace("<->", r"\rel")
        result = result.replace(">+>", r"\pinj")
        result = result.replace("-|>", r"\pinj")
        result = result.replace(">->", r"\inj")
        result = result.replace("+->", r"\pfun")

        # 2-character operators (process after longer operators)
        result = result.replace("=>", r"\Rightarrow")
        result = result.replace("<|", r"\dres")
        result = result.replace("|>", r"\rres")
        result = result.replace("->", r"\fun")  # AFTER |-> and +->
        result = result.replace("++", r"\oplus")
        result = result.replace("o9", r"\semi")

        # Word-based operators (both English and L-prefixed forms)
        result = re.sub(r"\bland\b", r"\\land", result)  # land → \land
        result = re.sub(r"\blor\b", r"\\lor", result)  # lor → \lor
        result = re.sub(r"\blnot\b", r"\\lnot", result)  # lnot → \lnot
        result = re.sub(r"\band\b", r"\\land", result)  # and → \land
        result = re.sub(r"\bor\b", r"\\lor", result)  # or → \lor
        result = re.sub(r"\bnot\b", r"\\lnot", result)  # not → \lnot
        result = re.sub(r"\bin\b", r"\\in", result)  # Set membership
        result = re.sub(r"\bdom\b", r"\\dom", result)
        result = re.sub(r"\bran\b", r"\\ran", result)
        result = re.sub(r"\bcomp\b", r"\\comp", result)
        result = re.sub(r"\binv\b", r"\\inv", result)
        result = re.sub(r"\bid\b", r"\\id", result)

        # Z notation keywords (QA fixes - matches _escape_justification)
        # Order matters: exists1+ before exists1 to avoid partial match
        result = re.sub(r"exists1\+", r"\\exists", result)  # exists1+ → ∃
        result = re.sub(r"\bexists1\b", r"\\exists_1", result)  # exists1 → ∃₁
        result = re.sub(r"\bexists\b", r"\\exists", result)  # exists → ∃
        result = re.sub(r"\bemptyset\b", r"\\emptyset", result)  # emptyset → ∅
        result = re.sub(r"\bforall\b", r"\\forall", result)  # forall → ∀

        # Wrap ALL remaining text sequences in \mathrm{} for proper spacing
        # In math mode, spaces between letters are ignored, so we must wrap
        # text phrases to preserve word spacing.
        #
        # Strategy: Find sequences of words (letters/digits/underscores + spaces)
        # that aren't LaTeX commands (not preceded by \) and wrap them.
        # This handles phrases like "inductive hypothesis", "strong IH", etc.
        return self._wrap_text_in_mathrm(result)

    def _wrap_text_in_mathrm(self, text: str) -> str:
        """Wrap non-operator text sequences in \\mbox{} for proper math mode spacing.

        In math mode, spaces between bare letters are ignored. This function
        identifies text segments (between operators/symbols) and wraps them
        in \\mbox{} to preserve word spacing.

        Note: We use \\mbox{} instead of \\mathrm{} because \\mbox{} preserves
        spaces between words, while \\mathrm{} ignores them in math mode.

        Examples:
        - "inductive hypothesis" → "\\mbox{inductive hypothesis}"
        - "\\land intro" → "\\land \\mbox{intro}"
        - "strong IH, a < n" → "\\mbox{strong IH}, a < n"
        """
        # Pattern: Match sequences of words (with spaces between them)
        # that are NOT LaTeX commands (not preceded by \)
        # A "text segment" is: word (optional: space + word)*
        # where word = [a-zA-Z_][a-zA-Z0-9_]*
        #
        # We need to be careful not to match:
        # - LaTeX commands like \land, \mbox{}, etc.
        # - Single letters that are math variables (like a, b, n)
        # - Numbers that are math
        #
        # Strategy: Find word sequences of 2+ words OR single words that are
        # clearly text (not single letters, not LaTeX commands)

        # First, handle multi-word sequences (these are definitely text)
        # Pattern: word + (space + word)+  (2 or more words with spaces)
        # Use lookbehind to exclude matches inside LaTeX commands like \lor
        # (?<![a-zA-Z\\]) ensures we don't start inside a command or word
        word = r"[a-zA-Z_][a-zA-Z0-9_]*"
        multi_word_pattern = rf"(?<![a-zA-Z\\])({word}(?:\s+{word})+)"

        def wrap_multi(m: re.Match[str]) -> str:
            return f"\\mbox{{{m.group(1)}}}"

        text = re.sub(multi_word_pattern, wrap_multi, text)

        # Then handle known single-word text that should be wrapped
        # (rule names, common justification words)
        text_words = [
            "elim",
            "intro",
            "assumption",
            "premise",
            "from",
            "case",
            "contradiction",
            "middle",
            "excluded",
            "false",
            "definition",
            "substitution",
            "arithmetic",
            "algebra",
            "factoring",
            "equality",
            "trivial",
            "singleton",
            "factorization",
            "construction",
            "verification",
            "dichotomy",
            "known",
            "identity",
            "simplification",
            "logic",
            "previous",
            "line",
            "proof",
            "steps",
            "separately",
            "proved",
            "inductive",
            "step",
            "minimality",
            "well",
            "ordering",
            "principle",
            "choice",
            "axiom",
            "lemma",
            "direct",
            "negation",
            "trichotomy",
            "integers",
            "multiplication",
            "factorizations",
            "composite",
            "hypothesis",
            "diagonal",
            "method",
            "differs",
            "digit",
            "countable",
            "enumeration",
            "preservation",
            "terminates",
            "termination",
            "condition",
            "invariant",
            "exponent",
            "law",
        ]

        for word in text_words:
            # Only wrap if not already in \mbox{} and not a LaTeX command
            pattern = rf"(?<!\\)(?<!\{{)\b{word}\b(?!\}})"
            text = re.sub(pattern, rf"\\mbox{{{word}}}", text)

        return text
