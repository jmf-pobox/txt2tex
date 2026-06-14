"""LaTeX generator for txt2tex - converts AST to LaTeX."""

from __future__ import annotations

__all__ = ["LaTeXGenerator", "toc_depth_from_keyword"]

from typing import ClassVar

from txt2tex.__version__ import __version__
from txt2tex.ast_nodes import (
    Abbreviation,
    BinaryOp,
    Conditional,
    Contents,
    Divide,
    Document,
    DocumentItem,
    Expr,
    FreeType,
    FunctionApp,
    GenericInstantiation,
    GivenType,
    Group,
    GroupAggregate,
    Identifier,
    Lambda,
    NaturalJoin,
    Part,
    Project,
    Quantifier,
    RelationalImage,
    RelationRename,
    Restrict,
    Section,
    SequenceLiteral,
    SetComprehension,
    SetLiteral,
    Solution,
    Subscript,
    Superscript,
    Tuple,
    UnaryOp,
    Ungroup,
)
from txt2tex.codegen._dispatch import CodegenDispatch
from txt2tex.codegen._smoke import (
    _SmokeTestMixin,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen._toc import toc_depth_from_keyword
from txt2tex.codegen.algebra import (
    _AlgebraCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.bindings import (
    _BindingsCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.expressions import (
    _ExpressionsCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.fuzz_routing import (
    _FuzzRoutingCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.overflow import (
    _OverflowCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.paragraphs import (
    _ParagraphsCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.paren_policy import (
    _ParenPolicyCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.proofs import (
    _ProofsCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.schemas import (
    _SchemasCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.text_blocks import (
    _TextBlocksCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.text_pipeline import (
    _TextPipelineCodegen,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.codegen.types import (
    _TypesCodegen,  # pyright: ignore[reportPrivateUsage]
)


class LaTeXGenerator(
    _ParagraphsCodegen,
    _SchemasCodegen,
    _ProofsCodegen,
    _AlgebraCodegen,
    _ExpressionsCodegen,
    _TypesCodegen,
    _BindingsCodegen,
    _TextBlocksCodegen,
    _OverflowCodegen,
    _FuzzRoutingCodegen,
    _ParenPolicyCodegen,
    _TextPipelineCodegen,
    _SmokeTestMixin,
    CodegenDispatch,
):
    """Converts txt2tex AST to LaTeX source code.

    Supports propositional/predicate logic, Z notation (schemas, axdefs, free types),
    sets, relations, functions, sequences, bags, proof trees, and text blocks.
    """

    UNARY_OPS: ClassVar[dict[str, str]] = {
        "lnot": r"\lnot",  # Only LaTeX-style keyword
        "-": r"-",  # Unary negation
        "#": r"\#",  # Cardinality
        # Relation functions
        "dom": r"\dom",  # Domain of relation
        "ran": r"\ran",  # Range of relation
        # Extended relation functions
        "inv": r"\inv",  # Inverse function
        "id": r"\id",  # Identity relation
        # Set functions
        "P": r"\power",  # Power set
        "P1": r"\power_{1}",  # Non-empty power set (braced subscript)
        "F": r"\finset",  # Finite set
        "F1": r"\finset_{1}",  # Non-empty finite set (braced subscript)
        "bigcup": r"\bigcup",  # Distributed union
        "bigcap": r"\bigcap",  # Distributed intersection
        # Postfix operators - special handling needed
        "~": r"^{-1}",  # Relational inverse (superscript -1)
        "+": r"^{+}",  # Transitive closure (superscript +)
        "*": r"^{*}",  # Reflexive-transitive closure (superscript *)
    }

    # Quantifier mappings
    QUANTIFIERS: ClassVar[dict[str, str]] = {
        "forall": r"\forall",
        "exists": r"\exists",
        "exists1": r"\exists_1",  # Unique existence quantifier
        "mu": r"\mu",  # Definite description (mu-operator)
        "lambda": r"\lambda",  # Multi-decl lambda (Quantifier node form)
    }

    # Fuzz-mode operators that behave like prefix functions and must wrap
    # a following unary-operator operand in parens to avoid mis-parsing.
    # Fuzz manual §2.3: prefix generic symbols are operator symbols; fuzz
    # grammar requires the argument to be parenthesised when it is itself
    # a prefix-function application.
    _FUZZ_FUNCTION_LIKE_UNARY: ClassVar[frozenset[str]] = frozenset(
        {
            "dom",
            "ran",
            "inv",
            "id",
            "P",
            "P1",
            "F",
            "F1",
            "bigcup",
            "bigcap",
        }
    )

    # Instance variable type annotations
    use_fuzz: bool
    toc_parts: bool
    _toc_depth: int
    parts_format: str
    _in_argue_block: bool
    _first_part_in_solution: bool
    _in_inline_part: bool
    _in_z_paragraph: bool
    _quantifier_depth: int
    _warn_overflow: bool
    _overflow_threshold: int
    _overflow_warnings: list[str]
    _dollar_sanitise_registry: dict[str, str]
    _synth_abbrev_counter: int
    _in_hidden_fuzz_block: bool

    def __init__(
        self,
        *,
        use_fuzz: bool = False,
        toc_parts: bool = False,
        warn_overflow: bool = True,
        overflow_threshold: int | None = None,
    ) -> None:
        """Initialize generator with package choice and TOC options.

        Args:
            use_fuzz: Use fuzz package instead of zed-* packages.
            toc_parts: Include parts (a, b, c) in table of contents.
            warn_overflow: Emit warnings for lines that may overflow page margins.
            overflow_threshold: LaTeX character threshold for overflow warnings.
                Defaults to DEFAULT_OVERFLOW_THRESHOLD (~100 chars).
        """
        self.use_fuzz = use_fuzz
        self.toc_parts = toc_parts
        self._toc_depth = 3  # Default: emit all three heading levels into TOC
        self.parts_format = "subsection"  # Document-level parts format
        self._in_argue_block = False  # Track context for line break formatting
        self._first_part_in_solution = False  # Track if we're generating first part
        self._in_inline_part = False  # Track if we're inside an inline part
        # True when generating inside axdef/schema/gendef/zed
        self._in_z_paragraph = False
        self._quantifier_depth = 0  # Track nesting for \t1, \t2 indentation
        self._warn_overflow = warn_overflow
        self._overflow_threshold = (
            overflow_threshold
            if overflow_threshold is not None
            else self.DEFAULT_OVERFLOW_THRESHOLD
        )
        self._overflow_warnings = []  # Collected warnings to emit
        # Populated by _pre_sanitise_dollars, consumed by _restore_dollar_sanitise
        self._dollar_sanitise_registry = {}
        self._synth_abbrev_counter = 0
        self._in_hidden_fuzz_block = False

    def _next_synth_name(self) -> str:
        """Generate the next synthetic abbreviation name for fuzz validation."""
        self._synth_abbrev_counter += 1
        return f"zS_{self._synth_abbrev_counter}"

    def _find_contents_depth(self, items: list[DocumentItem]) -> int | None:
        """Return the toc depth from the first Contents node found in document order.

        Performs a pre-order DFS through items, descending into the .items of
        Section, Solution, and Part nodes so that a CONTENTS: directive nested
        inside a section heading is not silently ignored.

        Returns None when no Contents node exists anywhere in the subtree.
        """
        for item in items:
            if isinstance(item, Contents):
                return toc_depth_from_keyword(item.depth)
            if isinstance(item, (Section, Solution, Part)):
                result = self._find_contents_depth(item.items)
                if result is not None:
                    return result
        return None

    def _resolve_toc_depth(self, items: list[DocumentItem]) -> None:
        """Set self._toc_depth for one document body.

        Reset to the default, derive from the first Contents node anywhere in
        the tree, then apply the --toc-parts override.  Called by both
        generate_document and generate_fragment so the two entry points cannot
        diverge: generate_fragment previously skipped this, ignoring CONTENTS:
        depth in REPL previews and leaking _toc_depth across inputs.
        """
        self._toc_depth = 3
        found_depth = self._find_contents_depth(items)
        if found_depth is not None:
            self._toc_depth = found_depth
        if self.toc_parts:
            self._toc_depth = 3

    # -------------------------------------------------------------------------
    # Overflow warning helpers
    # -------------------------------------------------------------------------

    def _get_bullet_separator(self) -> str:
        """Return bullet separator: @ for fuzz, \\bullet for standard LaTeX."""
        return "@" if self.use_fuzz else r"\bullet"

    def _get_colon_separator(self) -> str:
        """Return colon separator: : for fuzz, \\colon for standard LaTeX."""
        return ":" if self.use_fuzz else r"\colon"

    def _get_mid_separator(self) -> str:
        """Return mid separator: | for fuzz, \\mid for standard LaTeX."""
        return "|" if self.use_fuzz else r"\mid"

    def _get_type_latex(self, name: str) -> str | None:
        """Return LaTeX for mathematical type names (N, Z, N1).

        Returns None if name is not a known type name.
        """
        type_map_fuzz = {"Z": r"\num", "N": r"\nat", "N1": r"\nat_1"}
        type_map_std = {"Z": r"\mathbb{Z}", "N": r"\mathbb{N}", "N1": r"\mathbb{N}_1"}
        if name in type_map_fuzz:
            return type_map_fuzz[name] if self.use_fuzz else type_map_std[name]
        return None

    def _get_closure_operator_latex(self, operator: str, operand: str) -> str:
        """Return LaTeX for closure/inverse operators (+, *, ~).

        Args:
            operator: One of '+', '*', '~'
            operand: The operand LaTeX string

        Returns:
            Formatted LaTeX with appropriate operator for fuzz/standard mode.
        """
        if self.use_fuzz:
            if operator == "+":
                return rf"{operand} \plus"
            if operator == "*":
                return rf"{operand} \star"
            # ~ inverse uses \inv in fuzz mode (fuzz.sty defines \inv as ^\sim)
            return rf"{operand} \inv"
        # Standard LaTeX: superscript notation
        op_superscript = {"+": "^{+}", "*": "^{*}", "~": "^{-1}"}
        return f"{operand}{op_superscript[operator]}"

    def _format_multiword_identifier(self, name: str) -> str:
        """Format a multi-word identifier with underscores.

        For fuzz: just escape underscores (name\\_with\\_underscores)
        For standard LaTeX: escape and wrap in \\mathit{...}
        """
        escaped = name.replace("_", r"\_")
        if self.use_fuzz:
            return escaped
        return rf"\mathit{{{escaped}}}"

    def _generate_document_items_with_consolidation(
        self, items: list[DocumentItem]
    ) -> list[str]:
        """Generate document items with zed environment consolidation.

        Groups consecutive GivenType, FreeType, and Abbreviation items
        into a single zed environment with \\also between them.
        """
        lines: list[str] = []
        i = 0
        while i < len(items):
            item = items[i]
            # Check if this is a zed-generating item
            if isinstance(item, (GivenType, FreeType, Abbreviation)) and not (
                isinstance(item, Abbreviation)
                and self._expression_contains_dat_construct(item.expression)
            ):
                # Collect consecutive zed items (exclude DAT abbreviations)
                zed_items: list[GivenType | FreeType | Abbreviation] = [item]
                j = i + 1
                while j < len(items):
                    next_item = items[j]
                    if not isinstance(next_item, (GivenType, FreeType, Abbreviation)):
                        break
                    if isinstance(
                        next_item, Abbreviation
                    ) and self._expression_contains_dat_construct(next_item.expression):
                        break
                    zed_items.append(next_item)
                    j += 1

                # Generate consolidated zed environment
                if len(zed_items) == 1:
                    # Single item: generate normally
                    item_lines = self.generate_document_item(item)
                    lines.extend(item_lines)
                else:
                    # Multiple consecutive items: consolidate
                    lines.append(r"\begin{zed}")
                    for idx, zed_item in enumerate(zed_items):
                        if idx > 0:
                            lines.append(r"\also")
                        # Generate content without wrapping zed environment
                        content = self._generate_zed_content(zed_item)
                        self._check_overflow(
                            content,
                            zed_item.line,
                            "zed abbreviation (consolidated)",
                        )
                        lines.append(content)
                    lines.append(r"\end{zed}")
                    lines.append("")

                # Skip processed items
                i = j
            else:
                # Not a zed item: generate normally
                item_lines = self.generate_document_item(item)
                lines.extend(item_lines)
                i += 1

        return lines

    def _generate_zed_content(self, item: GivenType | FreeType | Abbreviation) -> str:
        """Generate the content of a zed item without the environment wrapper."""
        if isinstance(item, GivenType):
            names_str = ", ".join(item.names)
            return f"[{names_str}]"
        if isinstance(item, FreeType):
            # Generate branches
            branch_strs: list[str] = []
            for branch in item.branches:
                if branch.parameters is None:
                    branch_strs.append(branch.name)
                else:
                    if isinstance(branch.parameters, SequenceLiteral):
                        if branch.parameters.elements:
                            params_latex = self.generate_expr(
                                branch.parameters.elements[0]
                            )
                        else:
                            params_latex = ""
                    else:
                        params_latex = self.generate_expr(branch.parameters)
                    branch_strs.append(f"{branch.name} \\ldata {params_latex} \\rdata")
            branches_str = " | ".join(branch_strs)
            return f"{item.name} ::= {branches_str}"
        # Abbreviation LHS: definition slot, not a math-mode reference.
        expr_latex = self.generate_expr(item.expression)
        name_latex = self._generate_identifier(
            Identifier(line=0, column=0, name=item.name),
        )
        if item.generic_params:
            params_str = ", ".join(item.generic_params)
            return f"{name_latex}[{params_str}] == {expr_latex}"
        return f"{name_latex} == {expr_latex}"

    def generate_fragment(self, ast: Document) -> str:
        """Generate LaTeX content without document wrapper.

        Useful for interactive mode and previews where the content
        will be wrapped in a minimal document separately.

        Args:
            ast: The Document AST to generate content for.

        Returns:
            LaTeX content (body only, no preamble/postamble).
        """
        # Store document-level parts format
        self.parts_format = ast.parts_format
        self._resolve_toc_depth(ast.items)

        # Generate all document items
        lines = self._generate_document_items_with_consolidation(ast.items)

        return "\n".join(lines)

    def generate_document(self, ast: Document | Expr) -> str:
        """Generate complete LaTeX document with preamble and postamble.

        Produces a full LaTeX document including documentclass, packages,
        title/author metadata, bibliography, and document body.

        Args:
            ast: The AST root node, either a Document with structural elements
                or a single Expr for backward compatibility.

        Returns:
            Complete LaTeX source code ready for compilation.
        """
        lines: list[str] = []

        # Preamble
        # Use fleqn option to left-align all equations (no centering)
        # a4paper for A4 page size, 10pt font
        lines.append(r"\documentclass[a4paper,10pt,fleqn]{article}")
        # Standard 1 inch margins on all sides
        lines.append(r"\usepackage[margin=1in]{geometry}")
        # Load amssymb for \mathbb{N} and \mathbb{Z} blackboard bold
        # Note: amsmath removed - using array{lll} instead of align* for EQUIV
        lines.append(r"\usepackage{amssymb}")  # For \mathbb{N} and \mathbb{Z}
        # Load adjustbox for scaling wide elements to fit page width
        lines.append(r"\usepackage{adjustbox}")
        # Load natbib for author-year citations (Harvard style)
        lines.append(r"\usepackage{natbib}")
        # Load hyperref BEFORE fuzz to avoid conflict with fuzz's \t command
        # hyperref redefines \t, but fuzz needs to override it for indentation
        lines.append(
            r"\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}"
        )
        if self.use_fuzz:
            lines.append(r"\usepackage{fuzz}")  # Replaces zed-cm (fonts/styling)
        else:
            lines.append(r"\usepackage{zed-cm}")  # Computer Modern fonts/styling
        lines.append(r"\usepackage{schemapk}")  # schemapk env for PK underlines
        # These packages work with both fuzz and zed-cm
        lines.append(r"\usepackage{zed-maths}")  # Mathematical operators
        lines.append(r"\usepackage{zed-proof}")  # Proof tree macros (\infer)

        # Declare dimension register for saving \leftskip before \begin{center}
        # The center environment resets \leftskip, but we need it for width calc
        lines.append(r"\newdimen\savedleftskip")

        # Title metadata (if present)
        if isinstance(ast, Document) and ast.title_metadata:
            meta = ast.title_metadata
            if meta.title:
                lines.append(r"\title{" + meta.title + "}")
            # Generate author field with optional subtitle/institution footnotes
            # Even without author name, generate \author{} if they're present
            if meta.author or meta.subtitle or meta.institution:
                author_parts: list[str] = []
                if meta.author:
                    author_parts.append(meta.author)
                if meta.subtitle:
                    author_parts.append(r"\thanks{" + meta.subtitle + "}")
                if meta.institution:
                    author_parts.append(r"\thanks{" + meta.institution + "}")
                lines.append(r"\author{" + " ".join(author_parts) + "}")
            if meta.date:
                lines.append(r"\date{" + meta.date + "}")

            # PDF metadata via hyperref (already loaded above)
            hypersetup_opts: list[str] = []
            if meta.title:
                hypersetup_opts.append(f"pdftitle={{{meta.title}}}")
            if meta.author:
                hypersetup_opts.append(f"pdfauthor={{{meta.author}}}")
            if meta.subtitle:
                hypersetup_opts.append(f"pdfsubject={{{meta.subtitle}}}")
            hypersetup_opts.append(f"pdfcreator={{txt2tex v{__version__}}}")
            lines.append(r"\hypersetup{" + ",".join(hypersetup_opts) + "}")

        lines.append(r"\begin{document}")
        lines.append("")

        # Generate title page if metadata present
        if isinstance(ast, Document) and ast.title_metadata:
            lines.append(r"\maketitle")
            lines.append("")

        # Content - handle both Document and single Expr
        if isinstance(ast, Document):
            # Store document-level parts format
            self.parts_format = ast.parts_format
            self._resolve_toc_depth(ast.items)
            # Multi-line document: generate each item
            # Consolidate consecutive zed environments
            lines.extend(self._generate_document_items_with_consolidation(ast.items))

            # Generate bibliography if bibliography file is specified
            if ast.bibliography_metadata and ast.bibliography_metadata.file:
                # Reset indentation before bibliography
                lines.append(r"\setlength{\leftskip}{0pt}")
                lines.append("")
                # Generate bibliography style (default to "plainnat" if not specified)
                # plainnat works with natbib package and provides author-year citations
                style = ast.bibliography_metadata.style or "plainnat"
                lines.append(r"\bibliographystyle{" + style + "}")
                lines.append("")
                # Generate bibliography command (remove .bib extension if present)
                bib_file = ast.bibliography_metadata.file
                if bib_file.endswith(".bib"):
                    bib_file = bib_file[:-4]
                lines.append(r"\bibliography{" + bib_file + "}")
                lines.append("")
        else:
            # Single expression (backward compatibility)
            latex_expr = self.generate_expr(ast)
            lines.append(f"${latex_expr}$")
            lines.append("")

        # Postamble
        lines.append(r"\end{document}")

        return "\n".join(lines)

    # generate_document_item is inherited from _CodegenDispatch (dispatch stub +
    # fallback body for bare Expr items).

    def _has_line_breaks(self, expr: Expr) -> bool:
        """Recursively check if expression contains any line breaks.

        Args:
            expr: The expression to check

        Returns:
            True if expr or any sub-expression has line breaks
        """
        # Nodes with line_break_after flag — check flag first, then children
        if isinstance(
            expr, (BinaryOp, NaturalJoin, Divide, Group, Ungroup, GroupAggregate)
        ):
            return self._has_line_breaks_flagged(expr)
        # Quantifier has a different flag name
        if isinstance(expr, Quantifier):
            if expr.line_break_after_pipe:
                return True
            if expr.domain and self._has_line_breaks(expr.domain):
                return True
            return self._has_line_breaks(expr.body)
        # Relational algebra wrappers: recurse into the inner relation
        if isinstance(expr, (Restrict, Project, RelationRename)):
            has_rel = self._has_line_breaks(expr.relation)
            if isinstance(expr, Restrict):
                return has_rel or self._has_line_breaks(expr.predicate)
            return has_rel
        return self._has_line_breaks_structural(expr)

    def _has_line_breaks_flagged(
        self,
        expr: BinaryOp | NaturalJoin | Divide | Group | Ungroup | GroupAggregate,
    ) -> bool:
        """Check line breaks for nodes that carry a line_break_after flag."""
        if expr.line_break_after:
            return True
        if isinstance(expr, BinaryOp):
            return self._has_line_breaks(expr.left) or self._has_line_breaks(expr.right)
        if isinstance(expr, NaturalJoin):
            left_has = self._has_line_breaks(expr.left)
            right_has = self._has_line_breaks(expr.right)
            sub_has = bool(expr.subscript and self._has_line_breaks(expr.subscript))
            return left_has or right_has or sub_has
        if isinstance(expr, Divide):
            return self._has_line_breaks(expr.left) or self._has_line_breaks(expr.right)
        # Group, Ungroup, GroupAggregate: only the relation child matters
        return self._has_line_breaks(expr.relation)

    def _has_line_breaks_structural(self, expr: Expr) -> bool:
        """Check line breaks for structural/container expression nodes."""
        if isinstance(expr, UnaryOp):
            return self._has_line_breaks(expr.operand)
        if isinstance(expr, Lambda):
            return self._has_line_breaks(expr.body)
        if isinstance(expr, Subscript):
            return self._has_line_breaks(expr.base) or self._has_line_breaks(expr.index)
        if isinstance(expr, Superscript):
            return self._has_line_breaks(expr.base) or self._has_line_breaks(
                expr.exponent
            )
        if isinstance(expr, SetComprehension):
            if expr.domain and self._has_line_breaks(expr.domain):
                return True
            if expr.predicate and self._has_line_breaks(expr.predicate):
                return True
            return bool(expr.expression and self._has_line_breaks(expr.expression))
        if isinstance(expr, (SetLiteral, SequenceLiteral)):
            return any(self._has_line_breaks(elem) for elem in expr.elements)
        if isinstance(expr, FunctionApp):
            if self._has_line_breaks(expr.function):
                return True
            return any(self._has_line_breaks(arg) for arg in expr.args)
        if isinstance(expr, Tuple):
            return any(self._has_line_breaks(elem) for elem in expr.elements)
        if isinstance(expr, RelationalImage):
            return self._has_line_breaks(expr.relation) or self._has_line_breaks(
                expr.set
            )
        if isinstance(expr, GenericInstantiation):
            if self._has_line_breaks(expr.base):
                return True
            return any(self._has_line_breaks(param) for param in expr.type_params)
        if isinstance(expr, Conditional):
            return (
                self._has_line_breaks(expr.condition)
                or self._has_line_breaks(expr.then_expr)
                or self._has_line_breaks(expr.else_expr)
            )
        # Base cases: Identifier, Number, StringLit, etc. - no line breaks
        return False

    # generate_expr is inherited from _CodegenDispatch (dispatch stub).

    def _get_indentation(self) -> str:
        """Get indentation command based on current quantifier depth.

        Returns:
            \\t1, \\t2, etc. for nested indentation, or \\quad for depth 0
        """
        # Use depth-based \t commands for nested quantifiers
        # \t1 = 1 * 2em, \t2 = 2 * 2em, etc.
        if self._quantifier_depth == 0:
            return r"\quad"  # Fallback for non-quantifier contexts
        return f"\\t{self._quantifier_depth}"
