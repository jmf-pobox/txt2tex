# txt2tex: Software Design Document

## Executive Summary

**Goal**: Convert whiteboard-style mathematical notation to typechecked, high-quality LaTeX.

**Core Philosophy**: Parse, don't pattern-match. Understand structure semantically, then generate LaTeX with confidence.

**Key Features**:

1. Lexical analysis and parsing for robust conversion
2. Context-aware formatting (math vs prose vs Z notation)
3. fuzz validation integration
4. High-quality PDF generation

## Design Principles

These principles guide all design decisions in txt2tex, balancing accessibility for beginners with alignment to Z notation standards.

### Principle 1: Whiteboard Fidelity with LaTeX Transparency

<!-- markdownlint-disable-next-line MD036 -->
*"Make the simple things invisible, the complex things explicit."*

Users write natural whiteboard notation, but the generated LaTeX should be recognizable and teachable. A student who learns txt2tex should be 70%+ prepared to write LaTeX with fuzz directly.

**Application**:

- ✅ **Automatic smart defaults**: Add `\t1` for indentation when users break lines (Spivey-canonical Z RM §3 form; `\t1` is fuzz's tab-stop, not `\quad`)
- ✅ **Automatic line breaks**: Convert newlines to `\\` in appropriate contexts
- ✅ **Automatic spacing**: Insert `~` in set comprehensions, function application
- ❌ **Don't hide LaTeX structure**: Keep environment boundaries clear (`schema...end`, not implicit)
- ❌ **Don't invent new operators**: Use Z notation conventions or ASCII approximations

### Principle 2: Align Notation with Z Standards

<!-- markdownlint-disable-next-line MD036 -->
*"When whiteboard notation matches formal notation, prefer formal notation."*

Where Z notation has established conventions (like `\land`, `\lor`, `\forall`), our ASCII input mirrors these closely. This reduces cognitive load when students transition to reading research papers or formal specifications.

**Application**:

- ✅ **Use standard Z keywords**: `land`, `lor`, `lnot` (not `and`, `or`, `not`)
- ✅ **Use standard Z symbols where ASCII-friendly**: `forall`, `exists`, `cross`, `subset`
- ✅ **Preserve Z operator precedence**: Match zed2e exactly
- ✅ **Use Z terminology**: "maplet" not "pair", "dom" not "domain"
- ⚠️ **ASCII approximations only where necessary**: `|->` for `\mapsto`, `<->` for `\rel`

**Rationale**: Students learning `land` and `lor` are learning the actual Z notation names. Reading `\land` in LaTeX or papers becomes immediate recognition.

### Principle 3: Progressive Disclosure of Complexity

<!-- markdownlint-disable-next-line MD036 -->
*"Simple cases should be simple; complex cases should be explicit."*

Common patterns get smart defaults. Advanced users can override with explicit LaTeX hints. Never force complexity on beginners, never hide power from experts.

**Supported Levels**:

| Level | User | Approach |
|-------|------|----------|
| **Level 1** (Beginner) | Write `land`, `lor`, let system handle spacing and breaks | Auto-formatting |
| **Level 2** (Intermediate) | Use blank lines for `\also` grouping in where clauses | Structural control |
| **Level 3** (Expert) | Use `LATEX:` blocks for direct control | Full LaTeX escape hatch |
| **Level 4** (Expert+) | Mix txt2tex with hand-written LaTeX | Hybrid mode |

**Future Enhancement**: Inline LaTeX hints (e.g., `\\`, `\t1`, `~`) within expressions are not currently supported. Users who need fine formatting control should use `LATEX:` blocks (Level 3).

### Strategic Goals

1. **Training Wheels for Z Notation**: A student proficient in txt2tex can read 80% of Z notation papers and write 60% of fuzz LaTeX without additional training.

2. **Textbook-Quality LaTeX**: Generated LaTeX should be indistinguishable from examples in Spivey's "The Z Notation" or Woodcock & Davies' "Using Z".

3. **Preserve Accessibility**: Keep the "whiteboard feel" - users shouldn't feel like they're writing code.

---

## Requirements

### Functional Requirements

1. **Input Format**
   - Plain ASCII whiteboard notation
   - Allow Unicode characters for mathematical symbols (user's preference)
   - Minimal syntax - "write like on a whiteboard"
   - Support for:
     - Propositional logic (and, or, not, =>, <=>)
     - Predicate logic (forall, exists, quantifiers)
     - Z notation (schemas, axiomatic definitions, types)
     - Truth tables
     - Equivalence chains with justifications
     - Proof trees (indentation-based)

2. **Output Format**
   - LaTeX that compiles with fuzz or zed-* packages
   - Properly formatted mathematics
   - Submission-ready PDF quality
   - Correct spacing and typography

3. **Validation**
   - fuzz typechecking integration
   - Report type errors before PDF generation
   - Clear error messages pointing to input location

4. **User Experience**
   - Single command conversion: `txt2tex input.txt -o output.pdf`
   - Clear error messages with line numbers
   - Optional intermediate LaTeX output for debugging
   - Warnings for ambiguous constructs

### Non-Functional Requirements

1. **Correctness**: Prefer failing with clear error over silent misinterpretation
2. **Maintainability**: Clean architecture, extensible for new operators/constructs
3. **Performance**: Fast enough for interactive use (<1s for typical documents)
4. **Testability**: Comprehensive test suite with known good inputs/outputs

## Architecture Overview

### High-Level Pipeline

```text
Input Text
    ↓
┌─────────────────┐
│ Lexer           │ → Token Stream
│ (Tokenization)  │
└─────────────────┘
    ↓
┌─────────────────┐
│ Parser          │ → Abstract Syntax Tree (AST)
│ (Structure)     │
└─────────────────┘
    ↓
┌─────────────────┐
│ Semantic        │ → Annotated AST
│ Analyzer        │
└─────────────────┘
    ↓
┌─────────────────┐
│ LaTeX Generator │ → LaTeX Source
└─────────────────┘
    ↓
┌─────────────────┐
│ fuzz Validator  │ → Type Errors (if any)
│ (Optional)      │
└─────────────────┘
    ↓
┌─────────────────┐
│ pdflatex        │ → PDF Output
└─────────────────┘
```

**Simplified Example**: For a minimal implementation of this pipeline, see [rpn2tex](https://github.com/jmf-pobox/rpn2tex) — a tutorial project that converts RPN expressions to LaTeX using the same architecture (lexer → parser → AST → generator) with only ~6 token types and 2 AST nodes instead of 100+.

## Component Design

### 1. Lexer (Tokenizer)

**Responsibility**: Convert raw text into a stream of tokens.

**Token Types**:

```python
class TokenType(Enum):
    # Structural
    SECTION_MARKER = "==="
    SOLUTION_MARKER = "**"
    PART_LABEL = "(a)"          # (a), (b), (c), etc.

    # Environments
    TRUTH_TABLE = "TRUTH TABLE:"
    EQUIV_CHAIN = "EQUIV:"
    PROOF_TREE = "PROOF:"

    # Z Notation
    GIVEN = "given"
    AXDEF = "axdef"
    SCHEMA = "schema"
    WHERE = "where"
    END = "end"
    FREE_TYPE = "::="
    ABBREV = "=="

    # Operators
    AND = "land"
    OR = "lor"
    NOT = "lnot"
    IMPLIES = "=>"
    IFF = "<=>"
    FORALL = "forall"
    EXISTS = "exists"
    BULLET = "|"

    # Math
    SUPERSCRIPT = "^"
    SUBSCRIPT = "_"
    NUMBER = "123"
    IDENTIFIER = "xyz"

    # Delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    LBRACE = "{"
    RBRACE = "}"

    # Special
    PIPE = "|"              # For table columns or quantifiers
    NEWLINE = "\n"
    INDENT = "  "           # Significant whitespace
    TEXT = "..."            # Plain text/prose
    EOF = ""
```

**Key Features**:

- **Whitespace significance**: Track indentation for proof trees
- **Line tracking**: Maintain line numbers for error messages
- **Lookahead**: Support for multi-character operators (<=>)

**Lexer State Machine**:

```text
START →
  | "===" → SECTION_MARKER
  | "**"  → SOLUTION_MARKER
  | "("letter")" → PART_LABEL
  | "TRUTH TABLE:" → TRUTH_TABLE
  | "EQUIV:" → EQUIV_CHAIN
  | "PROOF:" → PROOF_TREE
  | "given" → GIVEN (if at line start)
  | "axdef" → AXDEF (if at line start)
  | "schema" → SCHEMA (if at line start)
  | letter → IDENTIFIER
  | digit → NUMBER
  | whitespace → skip or INDENT
  | operator → AND/OR/NOT/etc.
  | else → TEXT
```

**Unicode Support**:

- Accept Unicode operators directly: ∧, ∨, ¬, ⇒, ⇔, ∀, ∃
- Map to same token types as ASCII equivalents
- User can choose ASCII or Unicode in input

**Implementation Notes**:

```python
class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def tokenize(self) -> List[Token]:
        while not self.at_end():
            self.scan_token()
        return self.tokens

    def scan_token(self):
        # Peek ahead for multi-character operators
        # Track position for error reporting
        # Distinguish operators from identifiers by context
        pass
```

#### Whitespace-Sensitive Operator Disambiguation

The lexer uses whitespace to disambiguate the `^` operator, which has dual meaning:

**Disambiguation Rule**:

- **Space/tab/newline before `^`** → CAT token (sequence concatenation)
- **No space before `^`** → CARET token (exponentiation/superscript)
- **Special case `>^<`** → LexerError with helpful message

**Rationale**: The `^` operator's meaning depends on operand types (sequences vs numbers),
which cannot be determined at lexing time. Previous heuristic (checking if previous
char was `>`) failed for function results `f() ^ <x>`, variables `s ^ t`, and
parenthesized expressions `(s) ^ <x>`. Whitespace-based disambiguation is simple,
consistent, and matches mathematical convention (e.g., `4^2` vs `s ^ t`).

**Examples**:

```text
<x> ^ <y>     → CAT token (space before ^) → \langle x \rangle \cat \langle y \rangle
R^2           → CARET token (no space) → R \bsup 2 \esup (relation iteration)
s ^ t         → CAT token (space before ^) → s \cat t
R^n           → CARET token (no space) → R \bsup n \esup (relation iteration)
f(x) ^ <y>    → CAT token (space before ^) → f(x) \cat \langle y \rangle
<x>^<y>       → ERROR: "Sequence concatenation requires space: use '> ^ <' not '>^<'"
```

**Important:** CARET without space generates `\bsup...\esup` which fuzz interprets as `iter` (relation iteration). This ONLY works for relations, NOT arithmetic (x^2 causes fuzz type error).

**Error Handling**: The `>^<` pattern is explicitly detected and produces a clear
error message directing users to add space. This prevents a common mistake when
writing sequence concatenation.

**Token Types**:

- `CAT`: Sequence concatenation operator (renders as `\cat` in LaTeX)
- `CARET`: Superscript/exponentiation operator (renders as `^{...}` in LaTeX)

### 2. Parser

**Responsibility**: Build Abstract Syntax Tree from token stream.

**AST Node Types**:

```python
@dataclass
class ASTNode:
    line: int
    column: int

@dataclass
class Document(ASTNode):
    sections: List[Section]

@dataclass
class Section(ASTNode):
    title: Optional[str]
    content: List[Block]

@dataclass
class Solution(ASTNode):
    number: int
    parts: List[Part]

@dataclass
class Part(ASTNode):
    label: str          # "a", "b", "c"
    content: List[Block]

# Block types
@dataclass
class Prose(ASTNode):
    text: str
    inline_math: List[MathExpr]  # Parsed math expressions

@dataclass
class TruthTable(ASTNode):
    headers: List[str]
    rows: List[List[str]]

@dataclass
class EquivChain(ASTNode):
    steps: List[EquivStep]

@dataclass
class EquivStep(ASTNode):
    expression: MathExpr
    justification: Optional[str]

@dataclass
class ProofTree(ASTNode):
    root: ProofNode

@dataclass
class ProofNode(ASTNode):
    expression: MathExpr
    children: List[ProofNode]
    indent_level: int

# Z Notation
@dataclass
class GivenType(ASTNode):
    names: List[str]

@dataclass
class FreeType(ASTNode):
    name: str
    branches: List[str]

@dataclass
class AxDef(ASTNode):
    declarations: List[Declaration]
    predicates: List[MathExpr]

@dataclass
class Schema(ASTNode):
    name: str
    declarations: List[Declaration]
    predicates: List[MathExpr]

# Math expressions
@dataclass
class MathExpr(ASTNode):
    pass

@dataclass
class BinaryOp(MathExpr):
    op: str              # "land", "lor", "=>", etc.
    left: MathExpr
    right: MathExpr
    explicit_parens: bool = False  # Preserves user-written parentheses

@dataclass
class UnaryOp(MathExpr):
    op: str              # "lnot"
    operand: MathExpr

@dataclass
class Quantifier(MathExpr):
    quantifier: str      # "forall", "exists"
    variable: str
    domain: Optional[MathExpr]
    body: MathExpr

@dataclass
class Identifier(MathExpr):
    name: str

@dataclass
class Number(MathExpr):
    value: str

@dataclass
class Superscript(MathExpr):
    base: MathExpr
    exponent: MathExpr

@dataclass
class Application(MathExpr):
    function: str
    args: List[MathExpr]
```

**Parser Strategy**: Recursive descent with operator precedence

**Precedence Table** (lowest to highest):

```text
1. <=> (iff)
2. => (implies)
3. or (disjunction)
4. and (conjunction)
5. not (negation)
6. Comparison (=, <, >, <=, >=)
7. Arithmetic (+, -)
8. Multiplication (*, /, sequence concatenation ^)
9. Exponentiation (^)
10. Function application
11. Atoms (identifiers, numbers, parenthesized expressions)
```

**Note on `^` operator**:
The `^` symbol has dual meaning based on whitespace (disambiguated at lexing):

- **With space before**: CAT token → sequence concatenation (level 8, same as multiplication)
- **No space before**: CARET token → exponentiation/superscript (level 9, higher precedence)

**Explicit Parentheses Preservation**:

When users write explicit parentheses like `(A and B) and C`, these are preserved in the LaTeX output even if not strictly required by precedence rules. This maintains semantic grouping clarity from the source text.

**Implementation**:

- Parser marks `BinaryOp` nodes with `explicit_parens=True` when wrapped in parentheses
- LaTeX generator always adds parentheses for expressions with `explicit_parens=True`
- Prevents double parenthesization by checking flag before adding precedence-based parens

**Examples**:

```text
(A land B) land C      → (A \land B) \land C   (left parens preserved)
A land (B land C)      → A \land (B \land C)   (right parens preserved)
A land B land C        → A \land B \land C     (no parens, left-associative)
((A land B) land C)    → ((A \land B) \land C) (both levels preserved)
```

**Rationale**: User-written parentheses indicate semantic intent beyond operator precedence. In formal specifications, explicit grouping conveys important meaning about logical structure. The parser must distinguish between:

- **Precedence-required parens**: `(A lor B) land C` (needed because `lor` has lower precedence)
- **Explicit clarity parens**: `(A land B) land C` (not needed by precedence, but preserves grouping)

**Context Handling**:

The parser maintains context state to distinguish:

- **Math mode**: Inside equations, truth tables, proof trees
- **Prose mode**: Regular text paragraphs
- **Z mode**: Inside Z notation blocks
- **Justification mode**: Inside `[...]` brackets

```python
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.context = Context.PROSE

    def parse(self) -> Document:
        sections = []
        while not self.at_end():
            sections.append(self.parse_section())
        return Document(sections=sections)

    def parse_section(self) -> Section:
        # Handle === Section === markers
        # Parse content until next section
        pass

    def parse_block(self) -> Block:
        # Dispatch based on next token
        if self.match(TokenType.TRUTH_TABLE):
            return self.parse_truth_table()
        elif self.match(TokenType.EQUIV_CHAIN):
            return self.parse_equiv_chain()
        elif self.match(TokenType.PROOF_TREE):
            return self.parse_proof_tree()
        # ... etc

    def parse_math_expr(self) -> MathExpr:
        # Operator precedence parser
        return self.parse_iff()

    def parse_iff(self) -> MathExpr:
        left = self.parse_implies()
        while self.match(TokenType.IFF):
            right = self.parse_implies()
            left = BinaryOp(op="<=>", left=left, right=right)
        return left

    # ... more precedence levels
```

### 3. Semantic checks (no dedicated phase)

txt2tex does **not** ship a separate semantic-analysis pass.  The pipeline
runs `Lexer` → `Parser` → `LaTeXGenerator`, with no intermediate
annotated-AST stage.

That choice is deliberate.  The two consumers of semantic information are:

1. **fuzz**, the downstream Z typechecker, which runs on the generated
   `.tex` and reports identifier-resolution, type, and scope errors with
   precise source positions.  Re-implementing those checks in Python
   would duplicate fuzz's grammar and miss its semantic rules; fuzz is
   the authority.

2. **Targeted helpers**, where the *generator* needs structural
   information at emission time — for example
   `src/txt2tex/free_vars.py`, which computes free-variable sets used
   by the quantifier-chain collapse to decide when the Spivey
   multi-decl form is safe (see the dependent-domain ADR).  Such
   helpers run only on the AST nodes that need them; they are not a
   whole-tree analysis phase.

Constructs the parser does validate inline — primary-key uniqueness in
a schema, free-type branch shapes, syntactic well-formedness of `axdef`
declaration / `where` predicate split — raise `ParserError` at the
offending token.

### 4. LaTeX Generator

**Responsibility**: Generate correct LaTeX from annotated AST.

**Strategy**: Visitor pattern with context-aware formatting.

```python
class LaTeXGenerator:
    def __init__(self, ast: Document, options: Options):
        self.ast = ast
        self.options = options
        self.output = []
        self.indent_level = 0

    def generate(self) -> str:
        self.emit_preamble()
        self.visit(self.ast)
        self.emit_postamble()
        return '\n'.join(self.output)

    def emit_preamble(self):
        self.output.append(r'\documentclass{article}')
        if not self.options.use_zed:
            self.output.append(r'\usepackage{fuzz}')  # Default
        else:
            # Alternative: zed-* packages (via --zed flag)
            self.output.append(r'\usepackage{zed-cm}')
            self.output.append(r'\usepackage{zed-maths}')
            if self.has_proof_trees:  # Detected during parsing
                self.output.append(r'\usepackage{zed-proof}')
            if self.has_floats:
                self.output.append(r'\usepackage{zed-float}')
        self.output.append(r'\usepackage{amsmath}')
        # Load natbib for author-year citations (Harvard style)
        self.output.append(r'\usepackage{natbib}')
        self.output.append(r'\begin{document}')

    def visit_solution(self, node: Solution):
        self.output.append(r'\bigskip')
        self.output.append(r'\noindent')
        self.output.append(f'\\textbf{{Solution {node.number}}}')
        self.output.append('')
        for part in node.parts:
            self.visit(part)

    def visit_binary_op(self, node: BinaryOp):
        # Context: are we in math mode already?
        left = self.visit(node.left)
        right = self.visit(node.right)

        op_map = {
            'and': r'\land',
            'or': r'\lor',
            '=>': r'\Rightarrow',
            '<=>': r'\Leftrightarrow',
        }

        return f'{left} {op_map[node.op]} {right}'

    def visit_prose(self, node: Prose):
        # Handle inline math
        text = node.text
        for math_expr in node.inline_math:
            # Generate LaTeX for math expression
            math_latex = self.visit(math_expr)
            # Wrap in $ $ if not already
            text = text.replace(
                math_expr.original_text,
                f'${math_latex}$'
            )
        
        # Process citations: [cite key] → \citep{key}
        text = self._process_citations(text)
        
        self.output.append(text)

    def _process_citations(self, text: str) -> str:
        """Process citation markup in text.
        
        Converts [cite key] to \\citep{key} for Harvard-style parenthetical citations.
        Supports optional page/slide numbers.
        
        Examples:
            "[cite spivey92]" → "\\citep{spivey92}"
            "[cite spivey92 p. 42]" → "\\citep[p. 42]{spivey92}"
            "[cite spivey92 p. 42]" → "\\citep[p. 42]{spivey92}"
        """
        pattern = r"\[cite\s+([a-zA-Z0-9_-]+)(?:\s+([^\]]+))?\]"
        def replace_citation(match: re.Match[str]) -> str:
            key = match.group(1)
            locator = match.group(2)
            if locator:
                return f"\\citep[{locator.strip()}]{{{key}}}"
            else:
                return f"\\citep{{{key}}}"
        return re.sub(pattern, replace_citation, text)
```

**LaTeX Templates**:

Store common patterns as templates:

```python
TEMPLATES = {
    'truth_table': r'''
\begin{center}
\begin{tabular}{|{columns}|}
{header} \\
\hline
{rows}
\end{tabular}
\end{center}
''',

    'equiv_chain': r'''
\begin{align*}
{steps}
\end{align*}
''',

    'axdef': r'''
\begin{axdef}
{declarations}
\where
{predicates}
\end{axdef}
''',
}
```

### Parenthesisation Policy (ADR)

**Status**: SETTLED 2026-04-13.

**Context**: the parser builds an AST; the generator must decide which parentheses to emit. An early debate weighed *minimalist* (print only what is required for unambiguous parsing) against *instructive* (print what helps a human reader see precedence). The author started minimalist and conceded toward instructive in specific cases, but the end state was not clearly documented. Assessment feedback on Q8(b) surfaced the inconsistency — the grader expected parens around an existential predicate that the generator emitted bare.

**Decision**: precedence-driven output with a small, enumerable set of *always-paren* contexts, plus honouring author-written parens.

1. **Precedence-driven default.** The generator consults a PRECEDENCE table (`latex_gen.py:174`) and the `_needs_parens` helper (`latex_gen.py:939`) to decide whether a child expression needs parens against its parent. Standard compiler practice: emit parens iff the child's precedence is lower than the parent's (or equal with the wrong associativity).

2. **Author-written parens are preserved.** `BinaryOp.explicit_parens=True` (`ast_nodes.py:34`) is set by the parser when the source wrapped an expression in parens. The generator always emits parens for `explicit_parens=True`, irrespective of precedence. This is the mechanism documented at §2 *Explicit Parentheses Preservation*.

3. **Always-paren contexts** (additions on top of precedence + explicit flag):
   - Quantifier body containing propositional connectives (`∧`, `∨`, `⇒`, `⇔`). Wrap the body for visual chunking.
   - Set-comprehension constraint containing a nested quantifier. Wrap the inner quantifier.
   - Nested quantifiers without a structural separator (no `•` delimiter between them). Wrap the inner.

**Z RM citations**: §8.3 (concrete syntax precedence table), §2.1 (logical equivalence `⇔`), §2.3 (equality `=`), §3.6 (schema text `| … •`), §3.8.1 (set comprehension `{ … • … }`), §3.9 (quantified predicates/expressions). None of the Z RM sections *requires* the always-paren additions above — they are a Z-community convention for human legibility, not a syntactic obligation.

**Rationale**:

- Pure minimalism produces output that type-checks but can confuse human readers in exactly the way the Q8(b) feedback describes. The generator's output is read by human reviewers, not only by `fuzz`.
- Blanket instructive parenthesisation (parens around every non-atomic subexpression) produces cluttered output no Z reader writes by hand.
- Precedence-driven plus a short always-paren list matches the Z RM grammar for correctness and the standard Z style for readability, with a rule set small enough to document in one paragraph.

**Rejected alternatives**:

- *Minimalist-only*: fails the legibility bar set by the graders.
- *Instructive blanket*: fails the "textbook-quality output" requirement (Design Principle 1).
- *Source-parens-only*: under-specifies because the AST discards paren nodes for unambiguous subexpressions; only `BinaryOp` currently carries `explicit_parens`.

**Consequences**:

- Positive: a single policy statement. Tests can encode it with a parametrised matrix over operator pairs.
- Negative: the always-paren list is a judgment call per construct. Future constructs (new quantifier-like forms) will need to be classified deliberately.

**Known gaps requiring follow-up** (see task #15 and a forthcoming implementation mission):

1. **Arithmetic operators missing from the PRECEDENCE table.** `+`, `-`, `*`, `/` fall to the default precedence of 999. Today this yields accidentally-correct output for logical/set expressions but would produce wrong parens on mixed arithmetic, e.g., `a + b * c` emitted without parens around `b * c` when printed under a lower-precedence parent. Add explicit entries.

2. **Unary special cases outside the table.** `_generate_unary_op` (`latex_gen.py:878–922`) has four conditional blocks driven by operator-string matching rather than the PRECEDENCE table. Lift these into a `UNARY_PRECEDENCE` structure so `_needs_parens` is the single source of truth.

3. **Set-comprehension predicate loses parent context.** `_generate_set_comprehension` at `latex_gen.py:1314` calls `generate_expr(node.predicate)` with no `parent=` argument. Quantifiers inside `{ x : T | ∃ … }` therefore appear top-level and receive no wrapping parens. This is the direct mechanism behind the Q8(b) feedback. Pass `parent=node`; the always-paren rule for nested quantifier in comprehension constraint then fires.

4. **Cross-product rationale.** Documented — see subsection below.

5. **Test matrix is not exhaustive.** Per-feature tests exercise specific operator pairs; a `@pytest.mark.parametrize` matrix of `(child_op, parent_op, is_left_child, expected_parens)` across the PRECEDENCE table would make the policy machine-checkable and catch future table edits that break a pair.

#### Cross-product parenthesisation (settled, commit `6db389f`)

Fuzz distinguishes two cross-product forms with different access syntax:

- `A cross B cross C` — flat 3-tuple, destructured as `(a, b, c)`
- `(A cross B) cross C` — nested pair, destructured with `fst`/`snd`

An earlier version of `_needs_parens()` forced left-associative parenthesisation for all nested cross products, emitting `(A \cross B) \cross C` regardless of what the user wrote. This broke fuzz type-checking for flat n-tuple schemas, which require the un-parenthesised form `A \cross B \cross C`.

The fix removed the special case entirely. Cross-product now follows the same rule as every other operator: emit parens only when the user wrote them (i.e. `explicit_parens=True`) or when precedence genuinely requires it against a lower-precedence parent. Fuzz treats the flat form as the canonical n-ary product, so the generator must not impose structure the user did not write.

**Constraint for future work**: do not add cross-product to the always-paren list without confirming that fuzz's flat-tuple semantics are not in use. When a user needs a nested pair, they write the parens themselves.

**Z RM reference**: §2.5 (Spivey, *The Z Notation*, 2nd ed.) defines Cartesian product as an n-ary type constructor. `S × T × U` is a single product type whose elements are 3-tuples; it is not equivalent to `(S × T) × U`, whose elements are pairs with a pair as first component.

### Schema Calculus Operators — Context-Sensitive `;` Lift (ADR, Phase 3.2)

**Status**: SETTLED 2026-05-19.

**Context**: Z RM §3.11 defines `;` as schema-composition at the schema-expression level. The existing parser uses SEMICOLON as a declaration separator inside `axdef`, `schema`, and `gendef` bodies — and as a stop-token in `_can_continue_expression()`. Both uses must coexist without ambiguity.

**Decision**: Introduce a parser flag `_in_schema_expr_context` (default `False`). The flag is set to `True` in `_parse_horiz_def` immediately before parsing the RHS (after consuming `defs`), and restored to its previous value in a `try/finally` block. When the flag is `True`, a new schema-calculus precedence cascade handles the four operators:

1. `_parse_schema_pipe()`  — handles `>>`; calls compose for operands.
2. `_parse_schema_compose()` — handles `;` by consuming SEMICOLON; calls project/hide.
3. `_parse_schema_project_hide()` — handles `hide (names)` and `project T`; calls `_parse_expr()` for atomic operands.

Parenthesised sub-expressions `(S ; T)` are handled by modifying `_parse_parenthesized_expr_or_tuple()`: when `_in_schema_expr_context` is `True`, the inner expression is parsed by `_parse_schema_pipe()` rather than `_parse_expr()`. The tuple-element branch has the same conditional.

**Precedence implemented** (Z RM §3.11, tightest to loosest within schema-calculus):

1. `hide` / `project` — tightest
2. `;` (composition)
3. `>>` (piping) — loosest

**Tokens**: `PIPE_PIPE` (`>>`, two-char token detected in the lexer `>` branch, requiring whitespace before the first `>` to avoid conflict with closing RANGLE in nested sequences such as `<<a>, <b>>`). `HIDE` and `PROJECT` are keywords added to `KEYWORD_TO_TOKEN` and `RESERVED_WORDS`.

**Macros**: `\semi`, `\pipe`, `\hide`, `\project` — all defined in `fuzz.sty` (lines 295–302) and `zed-cm.sty` (lines 493–500). No preamble change is needed.

**Rejected alternative**: Add the four operators to the main expression-precedence cascade and use the flag only to gate SEMICOLON consumption. This would have required modifying the existing `_parse_iff` → … → `_parse_relation` chain, touching more code and risking regressions in non-schema expression contexts. The separate cascade is isolated behind the flag and adds ~120 LOC with no contact with existing precedence levels.

**Context-sensitivity guarantee**: `_parse_schema_compose()` is only reachable via `_parse_horiz_def_rhs()` when `_in_schema_expr_context` is `True`. The declaration-separator loops inside `axdef`, `schema`, and `gendef` bodies never call into the schema-calculus cascade; they consume SEMICOLON directly as a loop-continuation token.

**Test surface** (Phase 3.2):

- `tests/test_15_schema_calculus/test_schema_calculus.py` — 34 cases covering AST construction, generator output, precedence, context-sensitivity, and 4 negative cases.

### 5. fuzz Validator

**Responsibility**: Run fuzz typechecker on generated LaTeX.

**Approach**:

1. Generate complete LaTeX document
2. Run fuzz typechecker (if available)
3. Parse fuzz error output
4. Map errors back to original input line numbers
5. Report to user

```python
class FuzzValidator:
    def __init__(self, latex: str, source_map: SourceMap):
        self.latex = latex
        self.source_map = source_map

    def validate(self) -> List[ValidationError]:
        # Write LaTeX to temp file
        with tempfile.NamedTemporaryFile(suffix='.tex', mode='w') as f:
            f.write(self.latex)
            f.flush()

            # Run fuzz
            result = subprocess.run(
                ['fuzz', f.name],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return self.parse_fuzz_errors(result.stderr)

        return []

    def parse_fuzz_errors(self, stderr: str) -> List[ValidationError]:
        # Parse fuzz error format
        # Map LaTeX line numbers to original input line numbers
        errors = []
        for line in stderr.split('\n'):
            if 'error' in line.lower():
                # Extract line number, error message
                # Map back to original input
                errors.append(ValidationError(...))
        return errors
```

**Source Mapping**:

Maintain mapping between input line numbers and generated LaTeX line numbers:

```python
@dataclass
class SourceMap:
    mappings: Dict[int, int]  # LaTeX line → Input line

    def map_error(self, latex_line: int) -> int:
        # Find closest input line
        return self.mappings.get(latex_line, latex_line)
```

### 6. PDF Generator

**Responsibility**: Compile LaTeX to PDF using pdflatex.

```python
class PDFGenerator:
    def __init__(self, latex: str, output_path: str):
        self.latex = latex
        self.output_path = output_path

    def generate(self) -> bool:
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = os.path.join(tmpdir, 'output.tex')

            # Write LaTeX
            with open(tex_file, 'w') as f:
                f.write(self.latex)

            # Set environment for fuzz
            env = os.environ.copy()
            env['TEXINPUTS'] = '../tex//:'
            env['MFINPUTS'] = '../tex//:'

            # Run pdflatex
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', tex_file],
                cwd=tmpdir,
                env=env,
                capture_output=True
            )

            if result.returncode != 0:
                # Parse LaTeX errors
                raise LaTeXError(self.parse_latex_log(result.stdout))

            # Copy PDF to output location
            pdf_file = tex_file.replace('.tex', '.pdf')
            shutil.copy(pdf_file, self.output_path)

            return True
```

## Error Handling

### Error Types

```python
class Txt2TeXError(Exception):
    """Base exception class."""
    pass

class LexerError(Txt2TeXError):
    """Tokenization error."""
    line: int
    column: int
    message: str

class ParserError(Txt2TeXError):
    """Parsing error."""
    line: int
    expected: str
    got: str

class SemanticError(Txt2TeXError):
    """Semantic analysis error."""
    errors: List[str]

class ValidationError(Txt2TeXError):
    """fuzz validation error."""
    line: int
    message: str

class LaTeXError(Txt2TeXError):
    """LaTeX compilation error."""
    log: str
```

### Error Messages

Clear, actionable error messages with context:

```text
Error on line 42, column 15:
  (a) This is true: forall x in N, x * x >= 0
                          ^
Expected '|' or '.' after domain specification
Did you mean: forall x : N | x * x >= 0
```

## Testing Strategy

### Test Categories

1. **Unit Tests**
   - Lexer: Token generation for each construct
   - Parser: AST construction for valid inputs
   - Parser: Error handling for invalid inputs
   - Generator: LaTeX output for each AST node type

2. **Integration Tests**
   - Full pipeline: txt → LaTeX → PDF
   - Error propagation
   - Source mapping

3. **Regression Tests**
   - Edge cases discovered during development

4. **Golden Tests**
   - Compare against expected output
   - Pixel-perfect or text-diff comparison

### Test Structure

Tests are organized by feature area, mirroring the user guide topics:

```text
tests/
├── conftest.py                    # Shared fixtures
├── README.md                      # Test documentation
├── bugs/                          # Minimal reproducible test cases for bugs
│   └── *.txt
├── test_00_getting_started/       # Basic document structure
├── test_01_propositional_logic/   # Truth tables, equivalences, operators
├── test_02_predicate_logic/       # Quantifiers, nested quantifiers
├── test_03_equality/              # Equality operators
├── test_04_proof_trees/           # Natural deduction proofs
├── test_05_sets/                  # Set operations, comprehensions, tuples
├── test_06_definitions/           # Free types, generics, declarations
├── test_07_relations/             # Relation operators, composition
├── test_08_functions/             # Function types, lambda, application
├── test_09_sequences/             # Sequence literals, concatenation, bags
├── test_10_schemas/               # Schema definitions, zed blocks
├── test_11_text_blocks/           # Prose, citations, inline math
├── test_12_advanced/              # Conditionals, special identifiers
├── test_cli.py                    # CLI interface tests
├── test_coverage/                 # Additional coverage tests
├── test_edge_cases/               # Error handling, edge cases
├── test_error_formatting.py       # Error message formatting
├── test_infrule.py                # Inference rule tests
├── test_line_breaks/              # Line continuation handling
└── test_zed2e/                    # zed2e compatibility tests
```

Each feature directory contains:

- `README.md` - Description of tests in this area
- `test_*.py` - Test modules organized by sub-feature

## Configuration

### CLI Options

The `txt2tex` command accepts the following arguments:

```bash
txt2tex INPUT [-o OUTPUT] [--zed] [--toc-parts] [--no-warn-overflow] [--overflow-threshold N]
```

| Option | Description |
|--------|-------------|
| `INPUT` | Input text file with whiteboard notation (required) |
| `-o, --output` | Output LaTeX file (default: input with .tex extension) |
| `--zed` | Use zed-* packages instead of fuzz package (fuzz is default) |
| `--toc-parts` | Include parts (a, b, c) in table of contents |
| `--no-warn-overflow` | Disable warnings for lines that may overflow page margins |
| `--overflow-threshold N` | LaTeX character threshold for overflow warnings (default: 100) |

### LaTeXGenerator Options

The `LaTeXGenerator` class accepts these configuration options:

```python
generator = LaTeXGenerator(
    use_fuzz=True,           # True=fuzz package (default), False=zed-* packages
    toc_parts=False,         # Include parts in table of contents
    warn_overflow=True,      # Emit warnings for potential overflow
    overflow_threshold=100,  # Character threshold for overflow detection
)
```

### ADR: Q2(d) parser-bug fix — multi-decl + conjunction-predicate Z comprehensions

**Status**: SETTLED 2026-05-19.

**Context**: The parser's `_parse_postfix` method contained a 45-line heuristic (`is_bullet_indicator`) intended to stop field-projection consumption when a PERIOD token appeared to be a quantifier/comprehension bullet separator. In practice the heuristic conflated two distinct PERIOD roles:

- `s.x` — field projection, should be consumed by `_parse_postfix`
- `{ s : Ship | P . E }` — bullet separator, belongs to the outer comprehension/quantifier parser

The heuristic fired inside comprehension and quantifier bodies, blocking legitimate `s.field` projections in expression position. This caused 13 tests in `tests/test_q2d_calculus_predicate_chain.py` to fail. Two follow-on issues were also present: chained `TupleProjection` inside `mu` expressions greedily consumed the bullet PERIOD, and the RBRACE-separator heuristic in `_parse_postfix` swallowed RHS projections when parsing comparison expressions.

Separately, `_parse_lambda` lacked SEMICOLON and PIPE branches, so multi-declaration lambda expressions (`lambda s : Ship; c : Class | P . E`) raised a parse error.

**Decision**:

1. **Delete `is_bullet_indicator`** (parser.py lines 3637–3681). The `safe_followers` set at `_parse_postfix` (line 3722) already contains AND, OR, IN, IMPLIES, RBRACE, PIPE, and other tokens that legitimately follow a field-projection chain. Removing the heuristic lets `safe_followers` handle termination correctly. Bullet detection is the responsibility of the outer comprehension/quantifier parsers, not `_parse_postfix`.

2. **Add SEMICOLON/PIPE branches to `_parse_lambda`**. Multi-decl lambda now delegates to `_parse_quantifier_continuation`, producing nested `Quantifier(quantifier="lambda")` AST nodes. Single-decl `lambda x : T . body` continues to produce a `Lambda` node unchanged.

3. **Two residual fixes**: stop chained `TupleProjection` inside comprehension bodies; add `_in_comparison_rhs` flag to gate the RBRACE-separator heuristic so RHS projections are not swallowed.

4. **`_parse_quantifier_continuation` latent fix**: set `_parsing_schema_text` around domain parsing so multi-decl quantifiers parse domain types correctly. `latex_gen.py` QUANTIFIERS dict gains `"lambda": r"\lambda"`.

**AST shape for multi-decl lambda**: nested `Quantifier(quantifier="lambda")` nodes, not a single `Lambda` with a multi-decl SchemaText. Z RM §3.12 defines `lambda S • E` as syntactic sugar for `{ S • (\theta S, E) }`, so the nesting is a denormalized but semantically equivalent representation. This parallels how `forall`, `exists`, and `mu` handle multi-decl forms (nested `Quantifier` nodes), avoids inventing a new AST shape for a single edge case, and satisfies the type-checker boundary: fuzz sees LaTeX, not the AST.

**Z-semantic neutrality**: no Z RM construct's parse result changes. Only parser internals change. Confirmed with jms: `safe_followers` termination is an implementation detail of the descent parser and does not affect the accepted language.

**Rejected alternatives**:

- *(a) Keep heuristic, add context flag*: adds parser state and couples `_parse_postfix` to comprehension/quantifier context — exactly the design error the heuristic introduced. Does not fix the root cause (bullet detection belongs at the outer parser).
- *(b) Remove PERIOD/EOF from `safe_followers` globally*: would break chained projections outside comprehension bodies (e.g., `s.name.length` at the top level of a `zed` block). Too broad.

**Open question for jfreeman — LaTeX form of multi-decl lambda**:

The current generator emits nested lambdas:

```latex
\lambda s : Ship @ \lambda c : Class | P @ E
```

The Z RM canonical form (Spivey, §3.12) is a single lambda with a semicolon-separated SchemaText:

```latex
\lambda s : Ship; c : Class | P @ E
```

Both type-check in fuzz. The current code follows the same `_generate_quantifier` path used by multi-decl `forall`/`exists`, which is correct for those quantifiers. A specialisation of `_generate_quantifier` for `node.quantifier == "lambda"` could emit the Spivey form. This is not a blocker — fuzz accepts both — but the Spivey form is what Z RM readers expect to see. Decision deferred to jfreeman.

**Consequences**:

- All 13 tests in `tests/test_q2d_calculus_predicate_chain.py` pass.
- Multi-typed relational-calculus expressions (Z comprehensions with conjunction predicates over tuple projections, multi-decl `forall`/`exists`/`mu`/`lambda`) can be written natively without dropping into raw LaTeX.
- The `is_bullet_indicator` deletion removes 45 lines and one category of parser state. `_parse_postfix` is now simpler and more regular.
- Known limitation: multi-decl lambda without a pipe-predicate (e.g., `lambda s : Ship; c : Class . (s, c)`) is not yet supported. See `MISSING_FEATURES.md`.

## Supported Features

txt2tex is feature-complete for typical Z specifications. See [MISSING_FEATURES.md](guides/MISSING_FEATURES.md) for advanced operators not yet implemented.

### Document Structure

- Section headers (`=== Title ===`)
- Solution markers (`** Solution N **`)
- Part labels (`(a)`, `(b)`, `(c)`)
- Text paragraphs with `TEXT:` keyword
- Proper spacing (`\bigskip`, `\medskip`)

### Logic and Proofs

- **Propositional**: Truth tables, equivalence chains, operators (`land`, `lor`, `lnot`, `=>`, `<=>`)
- **Predicate**: `forall`, `exists`, `exists1`, mu-operator with multi-variable support
- **Proofs**: Natural deduction with inference rules, nested assumptions, discharge notation, case analysis

### Sets and Types

- **Operations**: `in`, `notin`, `subset`, `subseteq`, `cup`, `cap`, `cross`, `setminus`, `P`, `P1`, `#`, `bigcup`
- **Comprehension**: `{ x : X | predicate }`, `{ x : X | predicate . expression }`
- **Literals**: Set literals, maplets (`{1 |-> a, 2 |-> b}`)
- **Tuples**: `(a, b, c)` in expressions and comprehensions

### Relations

- Type syntax (`<->`), maplet (`|->`)
- Domain/range: `dom`, `ran`, restriction (`<|`, `|>`), subtraction (`<<|`, `|>>`)
- Composition (`comp`, `o9`), inverse (`~`), transitive closure (`+`, `*`)
- Relational image: `R(| S |)`
- Identity: `id[X]`

**Note**: Semicolon (`;`) is reserved for declaration separators, not composition.

### Functions

- All function types: partial (`+->`), total (`->`), injections, surjections, bijections
- Lambda expressions: `lambda x : X . expr`
- Function application: `f x`, `f(x)`
- Override: `f ++ {x |-> y}`

### Sequences and Bags

- Sequence literals: `<>`, `<a, b, c>`
- Concatenation: `^` (with space: `s ^ t`)
- Operators: `head`, `tail`, `front`, `last`, `rev`, `#`
- Sequence types: `seq`, `seq1`, `iseq`
- Bag operations: `bag`, `uplus`

### Z Notation Definitions

- Given types: `given A, B`
- Free types: `Status ::= active | inactive` with parameterized constructors
- Abbreviations: `Name == expression`
- Axiomatic definitions: `axdef...where...end`
- Generic definitions: `gendef [X]...where...end`
- Schemas: `schema Name...where...end`
- Generic instantiation: `Type[A, B]`, `emptyset[N]`

### Expressions

- Arithmetic: `+`, `-`, `*`, `mod`, unary minus
- Conditionals: `if condition then expr else expr`
- Subscripts/superscripts: `x_i`, `R^n` (relation iteration)
- Named field projection: `record.field`
- Multi-word identifiers: `cumulative_total`, `not_yet_viewed`

## Technology Choices

### Language

<!-- markdownlint-disable-next-line MD036 -->
**Python 3.12+**

- Good library support
- Dataclasses for AST nodes
- Type hints for maintainability

Alternative: **Rust**

- Better performance
- Strong type system
- But steeper learning curve and longer development time

**Decision**: Python for faster development

### Libraries

- **No external parser library**: Build custom recursive descent parser
  - Full control over error messages
  - Easy to extend
  - Lightweight

- **pytest**: Testing framework
- **click**: CLI argument parsing
- **pyyaml**: Configuration files
- **dataclasses**: AST node definitions

### File Organization

```text
txt2tex/
├── src/
│   ├── __init__.py
│   ├── lexer.py
│   ├── tokens.py
│   ├── parser.py
│   ├── ast_nodes.py
│   ├── semantic.py
│   ├── latex_gen.py
│   ├── fuzz_validator.py
│   ├── pdf_gen.py
│   ├── errors.py
│   └── cli.py
├── tests/
│   ├── ... (as above)
├── examples/
│   ├── 01_propositional_logic/
│   ├── 02_predicate_logic/
│   └── ...
├── docs/
│   ├── CLAUDE.md
│   ├── DESIGN.md
│   ├── README.md
│   └── TUTORIAL.md
├── pyproject.toml
├── setup.py
├── .gitignore
└── README.md
```

## Design Decisions

### 1. Package Choice: fuzz vs zed-* ✅ RESOLVED

**Decision**: Support both, default to **fuzz**

**Rationale**: Typechecking with fuzz is a core feature of txt2tex. The ability to validate Z specifications before PDF generation is a primary reason users convert to LaTeX.

- **fuzz advantages** (why it's the default):
  - Typechecker integration - validates Z notation correctness
  - Historical standard for Z notation
  - Single package simplicity

- **zed-* advantages** (available via `--zed` flag):
  - No custom fonts (uses Computer Modern + AMS)
  - Works on any LaTeX installation immediately
  - Built-in proof tree support (`\infer`, `\assume`, `\discharge`)
  - Modular design (load only what's needed)

**Implementation**: Both packages use identical macro names (`\land`, `\forall`, `\begin{schema}`, etc.), so generated LaTeX is 99% compatible. Only difference is preamble and proof tree syntax.

**Configuration**:

```python
# Default: fuzz package (for typechecking)
# Use --zed flag for zed-* packages
```

### 2. Proof tree syntax

**Decision**: Keep indentation-based, add explicit syntax later

**Notes**: zed-* packages provide `\infer` macros (from zed-maths.sty). Future enhancement could support explicit proof tree syntax.

### 3. Unicode operators

**Decision**: Accept both ASCII and Unicode on input

Users can write either `and` or `∧`, `forall` or `∀`, etc.

### 4. Justification syntax

**Decision**: Keep `[...]` bracket syntax

Users are familiar with `<=> q and p [commutative]`

### 5. Error recovery

**Decision**: Stop at first error initially, add recovery later

Clear, actionable error messages more important than partial output in v1.

### 6. ARGUE/EQUIV blocks: array vs argue environment ✅ RESOLVED

**Decision**: Use standard LaTeX `array` environment, NOT fuzz's `argue` environment

**Problem investigated**:

- Fuzz provides an `argue` environment specifically for equivalence chains with justifications
- Initial assumption was to use it for ARGUE/EQUIV blocks
- However, argue has fundamental limitations that make it unsuitable

**Root cause analysis**:

The fuzz `argue` environment uses this definition:

```tex
\def\argue{\@zed \interzedlinepenalty=\interdisplaylinepenalty
  \openup\@jot \halign to\linewidth\bgroup
    \strut$\@zlign##$\hfil \tabskip=0pt plus1fil
    &\hbox to0pt{\hss[\@zlign##\unskip]}\tabskip=0pt\cr
    \noalign{\vskip-\@jot}}
```

Key issues:

1. **Zero-width box for justifications**: `\hbox to0pt{\hss[...]}` places justifications in zero-width boxes
2. **No column spacing**: No mechanism for minimum spacing between expression and justification columns
3. **Result**: When both expressions and justifications are long, they overlap with no whitespace
4. **Cannot be scaled**: The raw `\halign` construct is incompatible with `adjustbox` (requires LR mode, but `\halign` expects display math mode)

**Attempted fixes**:

- Created `argue-fixed.sty` that replaces `\hbox to0pt{\hss[...]}` with `\hspace{2em}[...]`
- This fixed the spacing issue (2em guaranteed between columns)
- But scaling with `adjustbox{max width=\textwidth}` still fails due to `\halign` mode incompatibility
- Tried `\resizebox + minipage` wrapper but requires guessing content width (no conditional scaling)

**Array solution**:

```latex
\adjustbox{max width=\textwidth}{%
  $\displaystyle
  \begin{array}{l@{\hspace{2em}}r}
    expression & [justification] \\
    \Leftrightarrow expression & [justification]
  \end{array}$%
}
```

Advantages:

- `@{\hspace{2em}}` provides guaranteed 2em spacing between columns
- `adjustbox` works perfectly (conditional scaling only when needed)
- Standard LaTeX - no dependency on modified fuzz packages
- All 1199 tests pass

**Where adjustbox is critical**:

We use `adjustbox{max width=...}` in three places where content width is unpredictable:

1. **Truth tables** (line 3058 in latex_gen.py): Multi-column truth tables with complex headers
2. **ARGUE/EQUIV blocks** (line 3236): Long expressions AND long justifications
3. **Proof trees** (line 3809): Wide inference rules with multiple premises

In all cases, `adjustbox` provides **conditional scaling** - it measures natural content width and only scales down if needed to fit page margins. This maintains readability while preventing overflow.

The argue environment's use of raw `\halign` makes this impossible - it cannot be measured or wrapped in adjustbox. This was the deciding factor for using array instead.

**Conclusion**: The array-based approach is the correct solution. The argue environment, while designed for equivalence chains, has fundamental architectural limitations that prevent proper overflow handling in modern LaTeX documents.

### 7. Schema inclusion as declaration form ✅ RESOLVED

**Decision**: Schema inclusions (`Delta S`, `Xi S`, bare `S`) are parsed as a
new AST node `SchemaInclusion` within the declaration list of `schema`, `axdef`,
and `gendef` blocks.  The generator emits the schema name (with optional `\Delta`
or `\Xi` prefix) directly; fuzz handles semantic expansion.

**Alternatives considered**:

1. **Inline expansion** — expand the included schema's components at parse time,
   inserting them as `Declaration` nodes.  Rejected because: (a) the included
   schema may be defined later in the document; (b) it duplicates work fuzz
   already does; (c) it would break fuzz's own type checker which expects the
   schema name in the source, not expanded fields.

2. **Treat as expression in `where` clause only** — rejected because Z RM §3.7
   explicitly positions Delta/Xi in the *signature* (declaration) part, not the
   predicate part.  The fuzz box typesetter also requires the schema name to
   appear before `\where`.

**Disambiguation rule** (scan-ahead for colon):

The token stream for a declaration line is ambiguous: `Counter` could be a
single-name typed declaration without a type, or a bare schema inclusion.  The
rule is: scan ahead (without consuming tokens) looking for `COLON` before the
next `NEWLINE`, `WHERE`, `END`, `SEMICOLON`, or `EOF`.

- Colon found → typed declaration (`count, limit : N`)
- No colon found → schema inclusion (`Counter`)

This is a lookahead scan over the token array, O(k) where k is the length of
the variable list (typically 1–3 tokens).  It is not a backtracking parse.

**Delta/Xi as keywords and identifiers**:

`Delta` and `Xi` lex as `DELTA`/`XI` tokens when they start a declaration line.
The same identifiers can appear in expression context (e.g., `Gamma shows Delta`)
because `_parse_atom` accepts `DELTA` and `XI` as identifiers.  The disambiguation
is contextual: the declaration-loop checks for `DELTA`/`XI` tokens *first*, before
falling through to expression parsing.

Per the Phase-0 `RESERVED_WORDS` pattern, `Delta'` would be a `LexerError`
(decoration of a keyword is forbidden).  This matches Z RM intent.

**Generator convention**:

Inclusions emit into the schema/axdef/gendef box body, one per line, with `\\`
after every item except the last — the same convention as typed declarations.

```latex
\Delta Airline \\
bookingId? : BookingId \\
BookingInit \\
customerId? : CustomerId \\
routeId? : RouteId
```

## ADR: Horizontal Schema Definition RHS (Phase 1.3)

**Decision**: Represent the RHS of `Name defs RHS` as a union type
`Expr | SchemaInclusion` in `HorizDef.body`, not as a strict `Expr`.

**Context**: Z RM §3.8 allows the RHS of a horizontal definition to be any
*schema expression*, which includes `Delta S` and `Xi S` — decorated schema
references.  In txt2tex, `Delta S` and `Xi S` inside schema/axdef declaration
lists are represented as `SchemaInclusion` nodes (not `Expr` nodes) to preserve
semantic information about the decoration.

**Options considered**:

1. Add `SchemaInclusion` to the `Expr` union — rejected because `SchemaInclusion`
   carries list-of-`Expr` generics, making the union circular and causing cascading
   mypy narrowing failures throughout the existing codebase.

2. Represent `Delta S` on the RHS as a `BinaryOp` or custom node — rejected
   because it loses the structural information about the Delta/Xi decoration.

3. Type `HorizDef.body` as `Expr | SchemaInclusion` — accepted.  The generator
   handles both with a two-branch `isinstance` check; mypy and pyright are both
   satisfied.

**Inline schema text RHS**: The `SchemaText(declarations, predicates)` frozen
dataclass is added to the `Expr` union.  It is only produced by
`_parse_schema_text()` and only consumed in the `HorizDef` body slot; it does
not appear in other expression positions.  The generator converts it to the
bracket form `[ decl1; decl2 | pred1 \land pred2 ]`.

**Predicate separator in inline schema text**: Z RM §3.6 uses `;` to separate
predicates within a schema text.  The inline text parser accepts `;` as the
predicate separator; the generator joins predicates with `\land` (logical AND)
as a conservative choice, since fuzz parses both forms equivalently at the
type-checker level and `\land` is the standard mathematical rendering.

**`defs` as a prose-detection bypass**: The prose-detection heuristic for
one-letter identifiers like `A` at column 1 checks a hardcoded set of Z
keywords to decide whether the following token is an operator (not prose).
`defs` was added to that set so that `A defs B` at column 1 is tokenised
correctly rather than captured as a `TEXT` token.

## ADR: Relvar Set and Decoration-Outside-\mathrm Rule (Phase 2.1) — SUPERSEDED

> **SUPERSEDED** by "ADR: Remove relvars, Add pk Primary-Key Underlining
> (Phase 2.1 revised)" at the end of this document. The relvars feature
> was removed; the code described here no longer exists. This section is
> retained as historical record.

**Decision**: Implement the relvar typography via an O(N) pre-walk that
populates `relvar_set: frozenset[str]` before any LaTeX emission, then an O(1)
`name in self.relvar_set` check in `_generate_identifier`.

**Context**: The relational algebra convention uses `\mathrm{Name}` for relation names and default
italic for attribute names.  The `relvars` declaration paragraph marks which
identifiers are relvars.  Every occurrence of a declared name as an identifier —
in schema headers, type annotations, predicate expressions — must be wrapped.

**Decoration-outside rule**: Z-decorated names (`Class'`, `Class?`, `Class!`)
carry the decoration suffix baked into `Identifier.name` by the lexer.  When the
base name (after stripping `'`, `?`, `!` from the right) is in `relvar_set`,
the decoration is emitted *outside* `\mathrm{}`:

```text
Class   →  \mathrm{Class}
Class'  →  \mathrm{Class}'
Class_1'  →  \mathrm{Class}_1'   (subscript first, then decoration)
```

**Why decoration goes outside**: `'` is not valid inside `\mathrm{}` in
standard LaTeX and causes fuzz typechecker errors.  More importantly, the
decoration is semantically attached to the whole name token (Z RM §3.3), not
to the roman-type rendering — so placing it outside is both technically correct
and typographically consistent with handwritten notation.

**Subscript interaction — heuristic alignment**: The subscript check mirrors
the existing `_generate_identifier` heuristic for non-relvar identifiers:

| Suffix form | Example     | Relvar rendering          |
|-------------|-------------|---------------------------|
| 1-char      | `Class_1`   | `\mathrm{Class}_1`        |
| 2-char digit| `Class_12`  | `\mathrm{Class}_{12}`     |
| 2-char mixed| `Class_AB`  | normal path (no `\mathrm`) |
| 3+ chars    | `Class_test`| normal path (no `\mathrm`) |
| Multi-`_`   | `Class_x_y` | normal path (no `\mathrm`) |

Suffixes that the existing heuristic treats as multi-word identifiers (3+ chars,
or non-digit 2-char) fall through to the normal path without `\mathrm` wrapping.
The relvar property applies to the *relation name*, not to identifier fragments
derived from it.

**Duplicate relvars**: Multiple `relvars` paragraphs declaring the same name
are silently merged into the `relvar_set`.  A warning is appended to
`_overflow_warnings` (at most once per duplicate name, per `_collect_relvars`
call) to surface the issue via `emit_warnings()` or `get_warnings()`.

**REPL path**: `generate_fragment` mirrors `generate_document` by calling
`_collect_relvars` before emitting any LaTeX, ensuring relvar declarations in
interactive REPL input take effect immediately.

**Options considered**:

1. Emit decoration inside `\mathrm`: `\mathrm{Class'}` — rejected; `'` is not
   valid inside `\mathrm{}` and causes fuzz typechecker errors.

2. Infer relvars from capitalisation — explicitly forbidden by the mission.
   Declaration must be explicit to avoid false positives on single-letter
   type variables like `N`, `Z`, `X`.

3. Re-parse identifier in generator to split base + decoration — current
   approach: strip trailing `'`, `?`, `!` with a simple `while` loop.
   Simple, correct, O(decoration length).

**Performance**: The pre-walk is O(N) in document item count and runs once.
The per-identifier check is O(1) (frozenset membership).  The `relvar_set` is
empty for all existing documents, so the guard `if self.relvar_set:` short-
circuits the strip loop entirely, giving zero overhead to existing test suites.

**`relvars` paragraphs emit a comment**: The LaTeX output for a `relvars`
paragraph is `% relvars: Class, Ship, ...` — a comment, not a visible
environment.  This keeps the `.tex` source self-documenting while producing
no visible output.

## ADR: Relational Algebra Operator Syntax and Precedence (Phase 2.2)

**Decision**: Implement relational algebra in operator-form only.  No
keyword form `project ... from ...` — `from` is used as a Z field name
in existing corpus files.  Six forms:

```text
sigma[pred](R)         -- restriction    → \sigma_{pred}(R)
pi[A, B](R)            -- projection     → \pi_{A, B}(R)
rho[A as B, C as D](R) -- rename        → \rho_{A \to B, C \to D}(R)
R join S               -- natural join   → \mathrm{Join}(R, S)
R join [pred] S        -- theta-join     → \mathrm{Join}_{pred}(R, S)
R div S                -- division       → R \div S
```

> **Note (2026-05-19)**: `:=` (assignment) has been
> removed.  Use `==` instead.  `\bowtie` has been replaced by `\otimes`.
>
> **Note (2026-05-23)**: `bowtie` keyword has been renamed to `join`;
> `\otimes` emission replaced by `\mathrm{Join}(R, S)`.  See
> "ADR: Source keyword `bowtie` → `join`; emit `\mathrm{Join}` not `\otimes`".
>
> **Note (2026-05-23)**: `rho[A as B](R)` prefix rename has been retired;
> the postfix bracket form `R[NEW/OLD]` (Z RM §3.11, NEW first) replaces
> it.  `rho` now lexes as a plain identifier.  See "ADR: Relation Rename
> — adopt `R[NEW/OLD]`, retire `rho`".  Every mention of `rho` below
> describes the prior parser; that prefix is no longer accepted.
>
> **Note (2026-05-23)**: Project keyword emission changed from the brace
> form `\mathrm{Project}\{A, B\}(R)` to the subscript form
> `\mathrm{Project}_{A, B}(R)` to match the instructor's canonical
> vocabulary (#146).

**Operator levels** (lowest binds least):

| Level | Operator(s) | Grammar function | Binds |
|-------|-------------|-----------------|-------|
| union/override | `union`, `++` | `_parse_union` | loosest |
| setminus | `\` | `_parse_setminus` | |
| cross/join/div | `cross`, `join`, `div` | `_parse_cross` | |
| intersect | `intersect` | `_parse_intersect` | |
| prefix ops | `sigma`, `pi`, `rho` | `_parse_atom` | tightest |

The complete precedence chain from loosest to tightest:

```text
union / override (++)
    < setminus (\)
        < cross / join / div   [left-associative; same level]
            < intersect
                < sigma[...](R) / pi[...](R) / rho[...](R)   [atom]
```

`_parse_cross` calls `_parse_intersect` for each of its operands, so
`intersect` binds **tighter** than `join`/`div`/`cross` — it is resolved
first.  Consequence:

- `R join S union T` parses as `(R join S) union T` — `join` sits
  below `union` and is consumed first by `_parse_cross`.
- `R join S intersect T` parses as `R join (S intersect T)` — `intersect`
  is resolved inside `_parse_intersect` before `join` completes.
- `pi[a](R) join S` parses as `(pi[a](R)) join S` — `pi` is an atom.

**Why sigma/pi/rho at atom level**: They take explicit `[args](relation)`
syntax analogous to function calls.  Parsing them at atom level is consistent
with how `f(x)` is handled; it also means they can appear freely as operands
in any higher-level expression (`pi[a](R) join S`, `sigma[p](R union S)`).

**Why join and div at cross level**: The Codd/Date algebra treats join and
division as binary operators on relations, at the same conceptual tier as
Cartesian product.  Placing them alongside `cross` in `_parse_cross` avoids
a separate precedence level while preserving the expected left-to-right
associativity.

**Theta-join subscript parsing**: `R join [pred] S` — the `[` is consumed
inside `_parse_cross` when it immediately follows a `join` token.  A
separate `bracket_tok` is saved for error reporting; an empty bracket
(`join []`) raises "Expected predicate in join subscript".

**`as` keyword**: `as` is not a reserved keyword — it tokenizes as
`IDENTIFIER` with value `"as"`.  The rename-pair parser (`_parse_rename_pair`)
checks `self._current().value == "as"` after consuming the source attribute
name.  This avoids a reserved-word collision with any Z identifier named `as`
in other contexts.

**Kernel LaTeX only** *(SUPERSEDED 2026-05-19; see the Tier-2 Keyword Algebra ADR
for the current emission. The glyphs listed here reflect the original
Greek-letter rendering that has been replaced.)*
`\sigma`, `\pi`, `\rho`, `\div` are all standard LaTeX kernel
symbols. No preamble change is required; fuzz and pdflatex both accept
them without extra packages.

**Relvar wrapping in algebra**: Attribute names in `pi[class, country](R)`
are emitted through the same `Identifier` path as all other identifiers.
Since attribute names (lowercase) are typically not in `relvar_set`, they
stay italic.  If an attribute is also a declared relvar (unusual but valid),
it receives `\mathrm{}` wrapping — consistent with the general rule.

**Options rejected**:

1. `project A, B from R` / `select pred from R` keyword form — rejected;
   `from` appears as a Z field name in `examples/10_schemas/zed_blocks.txt`.
   Keyword-form would require a reserved word that conflicts with the corpus.

2. Separate precedence level for `join`/`div` above `cross` — rejected;
   the precedence difference between cross-product and join is not significant
   in algebra expressions at this stage, and a single level avoids one parser
   function.

3. `Assignment` as `Expr` — rejected; would allow nonsensical nesting like
   `sigma[T := R](S)`.  Statement-shaped constructs belong in `DocumentItem`.

> **Superseded (2026-05-19):** The `:=` operator and `Assignment` node have been
> removed entirely; the `\bowtie` emission has been replaced by `\otimes`.
> See "ADR: Keyword Algebra Alignment — Drop `:=`, `\bowtie` → `\otimes`" below.
>
> **Further superseded (2026-05-23):** `\otimes` was subsequently replaced by
> `\mathrm{Join}(R, S)` and the source keyword renamed `bowtie` → `join`.
> See "ADR: Source keyword `bowtie` → `join`; emit `\mathrm{Join}` not `\otimes`".

## ADR: Keyword Algebra Alignment — Drop `:=`, `\bowtie` → `\otimes`

> **SUPERSEDED (2026-05-23)**: The `\otimes` emit was itself incorrect —
> it denotes the degenerate Cartesian-product case, not the natural join.
> See "ADR: Source keyword `bowtie` → `join`; emit `\mathrm{Join}` not `\otimes`"
> for the current design.

**Decision**: Remove the `:=` assignment operator entirely and switch the
natural-join LaTeX emission from `\bowtie` to `\otimes`, aligning with
the keyword-algebra rendering convention reviewed 2026-05-19.

**Evidence**:

- The keyword-algebra convention uses `==` for naming a relation, not `:=`,
  for relational assignment. The operator `==` was already supported via
  the smart-`==` abbreviation committed in a8a02ae.
- The only `:=` use case reviewed was one SQL UPDATE trigger example —
  a SQL construct, not a relational algebra statement.
- Keyword algebra writes `A == ProperGroups ⊗ NewMembers` consistently
  across all algebra examples. LaTeX for `⊗` is `\otimes`, a kernel symbol
  present in fuzz and pdflatex without extra packages.

**Changes**:

- `TokenType.ASSIGN` removed from `tokens.py`.
- `:=` dispatch removed from `lexer.py`; a source line `T := R` now
  lexes as `T COLON EQUALS R` and the parser raises a
  "Expected ':' in declaration"-style error.
- `Assignment` dataclass removed from `ast_nodes.py`; removed from
  `DocumentItem` union.
- `_parse_assignment`, both ASSIGN dispatch sites, and the bare-ASSIGN
  guard removed from `parser.py`.
- `_generate_assignment` and its `@generate_document_item.register`
  removed from `latex_gen.py`.
- `_generate_natural_join` updated: emits `\otimes` / `\otimes_{p}`
  instead of `\bowtie` / `\bowtie_{p}`.
- All Assignment-related tests removed from
  `tests/test_14_relational_databases/test_algebra.py`; bowtie generator
  tests updated to expect `\otimes`.
- `docs/reference.tex`, `docs/tutorials/11_relational_databases.md`,
  `docs/guides/USER_GUIDE.md`, and
  `examples/14_relational_databases/algebra_basics.{txt,tex}` updated.

**Students who need the literal `:=` glyph** (e.g., for a SQL UPDATE
trigger example) can use a `TEXT:` or `LATEX:` block.

**Backward incompatibility**: Any existing `.txt` files that use `:=` will
fail to parse. Migrate to `==`.

**Options rejected**:

1. Keep `:=` as a deprecated synonym — rejected; the mission mandates full
   removal with no shims.

2. Keep `\bowtie` as an option/flag — rejected; a single canonical symbol
   per operator simplifies the output and matches the course materials.

## ADR: Z Binding Brackets and Context-Sensitive == (Phase 2.3)

**Decision**: Add `{| ... |}` binding literals per Z RM §3.7.  Render as
`\lblot ... \rblot`.  Reuse the existing `ABBREV` token for `==` inside
binding context.

**Forces**:

1. Relational-calculus exercises require binding-calculus expressions
   of the form `{ s : Ship | pred . {| name == s.name |} }`.
2. Z RM §3.7 specifies `\lblot a == e_1, b == e_2 \rblot`; the macros
   `\lblot` and `\rblot` exist in both `fuzz.sty` and the `zed-*` family
   (confirmed by jms round-1 verification at `fuzz.sty:275-276` and
   `zed-lbr.sty:222-223`/`zed-cm.sty:471-472`).
3. The `==` operator is already used for abbreviations (`Color == red | blue`);
   adding a second meaning requires disambiguation.
4. Components in Z RM §3.7 bindings use commas, not semicolons.

**Decision details**:

*Tokens.* Two new two-character tokens `LBIND` (`{|`) and `RBIND` (`|}`).
Lexer placement: `{|` check precedes the bare `{` branch; `|}` check follows
the existing `|)` branch (no conflict because no existing multi-char `|`
prefix peeks at `}`).

*== disambiguation.* The parser dispatches to `_parse_binding` when it
encounters `LBIND` at atom level.  Inside `_parse_binding_component`, `==`
is consumed as the label-equals operator.  No parser state flag is needed:
the context is implicitly established by being inside `_parse_binding`.

*AST.* `Binding(pairs: list[tuple[str, Expr]])` — a frozen dataclass added
to the `Expr` union.  Each pair is `(label_name, value_expression)`.

*Generator.* Labels are emitted via `_emit_attr_name` (the same helper used
by `pi` and `rho`), so a declared relvar appearing as a label receives
`\mathrm{}` wrapping.  Values are emitted with the full `generate_expr`
path.  Format: `\lblot label_1 == value_1, ..., label_n == value_n \rblot`.

*Field-projection in binding values.* The `_parse_postfix` `safe_followers`
set was extended to include `RBIND`, enabling `s.name` to parse as a
`TupleProjection` before `|}`.

*Multi-typed set comprehensions.* Multi-decl comprehension uses `{ s : Ship; c : Class | ... }`.
`SetComprehension` gained an `extra_declarations: list[tuple[str, Expr]] | None`
field (default `None`; backward-compatible).  The parser consumes optional
`;`-separated `var : Type` pairs after the first declaration.  The generator
emits them as `; var \colon Type` immediately after the first domain.
`_parse_set_expression` and the closing-`}` branch now skip leading newlines
to support multi-line comprehensions.

**Alternatives rejected**:

1. *New keyword for `==` in binding context* — unnecessary complexity;
   the disambiguation is local (position inside `{| ... |}`) and
   unambiguous.

2. *Angle-bracket or Unicode syntax* — `⟪ a == e ⟫` would require new
   Unicode input or macro definitions.  The `{| ... |}` form is the standard
   ASCII encoding in Z reference materials.

3. *`;` as component separator* — Z RM §3.7 explicitly uses commas.
   Semicolons are already the schema-declaration separator; mixing them into
   binding context would be confusing.

4. *Separate `decls` field in SetComprehension* — a `list[Declaration]`
   approach would be semantically cleaner but requires changing `Declaration`
   to support the single-variable-per-`:` form and updating all existing
   callers.  The `extra_declarations: list[tuple[str, Expr]]` field achieves
   the same result with a smaller diff.

## ADR: Schema Renaming Disambiguation — `/`-Detection in Brackets (Phase 3.1)

**Decision**: Disambiguate `S[a/b]` (schema rename, Z RM §3.11) from `S[X]`
(generic instantiation, Phase 1.1) by scanning the bracket contents at depth 0
before consuming anything.  If any `SLASH` token appears at depth 0 before the
matching `]`, parse as rename pairs; otherwise parse as a generic type list.

**Forces**:

1. Both `S[X]` and `S[a/b]` start identically: `IDENT`, `LBRACKET`.  A
   one-token lookahead is insufficient to decide.
2. The `/` character is already special in the lexer (`/=` → `NOT_EQUAL`,
   `/in` → `NOTIN`).  A bare `/` was previously an `LexerError`; Phase 3.1
   adds `SLASH` as a legal token.
3. Generic instantiation uses `_parse_postfix`'s while-loop.  Adding a branch
   inside the loop — without backtracking — requires knowing the branch before
   consuming the `[`.
4. The existing `_parse_postfix` loop cannot be extended by backtracking
   without introducing a position-save/restore mechanism; the forbidden list in
   the mission contract prohibits backtracking parsers.

**Decision details**:

*New token.* `SLASH` added to `TokenType` and to the lexer.  The lexer checks
`/=` and `/in` first (existing behavior), then falls through to `SLASH` for
any remaining bare `/`.

*New method `_parse_schema_rename_or_generic`.* Called from `_parse_postfix`
when the conditions for generic/rename bracket are met (same whitespace checks
as before).  Scans `_peek_ahead(offset)` tokens from offset 1 (the position
after the `[`), tracking bracket depth.  Returns on the first `SLASH` at depth
0 (rename) or on the matching `]` (generic).

*`_parse_generic_instantiation`.* Extracted from the old while-loop body.
Identical behavior; now called from `_parse_schema_rename_or_generic`.

*`_parse_schema_rename`.* New method that consumes `[`, then iterates:
`IDENTIFIER SLASH IDENTIFIER (COMMA IDENTIFIER SLASH IDENTIFIER)*`.  Raises
`ParserError` with message + line + column for every malformed case (missing
source, missing slash, missing target, trailing slash, trailing comma).

*AST.* `SchemaRename(schema: Expr, pairs: list[tuple[str, str]])` — frozen
dataclass added to `ast_nodes.py` and to the `Expr` union.

*Generator.* `_generate_schema_rename` emits `schema_repr[old/new, ...]`
using plain math-mode text.  No special LaTeX macro needed.

*Decoration interaction.* Per Z RM §3.11, decoration is tighter than
renaming: `S'[a/b]` renames the primed schema `S'`.  Because Phase 0's lexer
bakes decoration into the identifier value (`Identifier("S'")`), the rename
handler sees the base identifier already carrying the prime — no special
treatment required.

**Alternatives rejected**:

1. *Context flag in the parser* — flip a boolean when inside `[...]` and
   check for `/`.  Rejected: the flag would need to be set before the `[` is
   consumed, leaking state across unrelated parse calls.

2. *Distinct bracket syntax for rename* — e.g., `S{a/b}` or `S(a/b)`.
   Rejected: conflicts with Z RM §3.11 notation; fuzz typechecker expects `[`.

3. *Backtracking parser* — try generic, catch error, retry as rename.
   Rejected: explicitly forbidden in the mission contract and inconsistent with
   the project's no-backtracking discipline.

4. *Keyword prefix* — `rename S with [a/b]`.  Rejected: not Z RM notation.

**Known limitation — depth-tracking scan vs. two-token lookahead**: The
depth-0 scan in `_parse_schema_rename_or_generic` correctly handles all
current grammar forms.  A future grammar addition that places `/` at depth 0
inside brackets for a purpose other than rename (e.g., arithmetic division
inside a type expression) would require changing the disambiguation strategy.
The two-token lookahead alternative (check if the second token after `[` is
`/`) was considered and rejected: it handles only the single-pair case and
breaks on `S[a, b/c]` (multi-pair with a non-pair element first) or
`S[some_longer_name/target]`.  The depth-tracking scan is correct for all
current and planned Z notation within Phase 3.x scope.

## Future Enhancements

1. **Export formats**
   - Plain text (pretty-printed)

2. **LSP + IDE Integration**
   - Language Server Protocol implementation
   - VS Code extension (thin wrapper around LSP)
   - Live validation, autocomplete, syntax highlighting

3. **Handwritten image to LaTeX (OCR)**
   - Convert whiteboard/paper photos to txt2tex input
   - Recognize mathematical notation from handwriting
   - Challenging but high-value for real whiteboard workflows

## Deferred Designs

Designs that have been scoped against the Z RM and fuzz behaviour but
not implemented. Each entry has a standalone design document under
`docs/deferred/`; see those files for the full engine surface and the
references behind the decision.

- **User-defined operator names** — full engine surface for
  underscored operator templates (`_⊕_`, `_R_`, `op _`, `_ †`) as
  the LHS of an abbreviation or declaration, including the fuzz
  announce-before-define directive machinery and the operator-table
  state in the parser. See
  [docs/deferred/user-defined-operators.md](deferred/user-defined-operators.md)
  for the full scope. Author-side workaround until then is documented
  in
  [docs/guides/MISSING_FEATURES.md § User-Defined Operator Names](guides/MISSING_FEATURES.md#user-defined-operator-names).

## Appendix: Example Conversion

**Input (whiteboard.txt)**:

```text
** Solution 1 **

(a) forall x : N | x * x >= 0

TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T
```

**AST** (simplified):

```python
Document(
  sections=[
    Section(
      title=None,
      content=[
        Solution(
          number=1,
          parts=[
            Part(
              label="a",
              content=[
                Prose(
                  text="",
                  inline_math=[
                    Quantifier(
                      quantifier="forall",
                      variable="x",
                      domain=Identifier("N"),
                      body=BinaryOp(
                        op=">=",
                        left=Superscript(
                          base=Identifier("x"),
                          exponent=Number("2")
                        ),
                        right=Number("0")
                      )
                    )
                  ]
                )
              ]
            )
          ]
        ),
        TruthTable(
          headers=["p", "q", "p => q"],
          rows=[
            ["T", "T", "T"],
            ["T", "F", "F"],
            ["F", "T", "T"],
            ["F", "F", "T"]
          ]
        )
      ]
    )
  ]
)
```

**Output LaTeX** (with default fuzz package):

```latex
\documentclass{article}
\usepackage{fuzz}
\usepackage{amsmath}
\begin{document}

\bigskip
\noindent
\textbf{Solution 1}

(a) $\forall x : \nat \bullet x^{2} \geq 0$
\medskip

\begin{center}
\begin{tabular}{|c|c|c|}
$p$ & $q$ & $p \Rightarrow q$ \\
\hline
T & T & T \\
T & F & F \\
F & T & T \\
F & F & T \\
\end{tabular}
\end{center}

\end{document}
```

**Note**: With `--zed` flag, `\usepackage{fuzz}` becomes `\usepackage{zed-cm}` and `\usepackage{zed-maths}`.

## ADR: GROUP / UNGROUP `\mathop` Wrapping (Phase 4.1)

**Context.** Date's GROUP and UNGROUP operators are multi-letter operator
names written in all-caps (`GROUP`, `UNGROUP`, `AS`).  In LaTeX math mode,
a bare `\mathrm{GROUP}` renders as an upright roman word but with text-level
spacing — it does not behave as a math operator.  Using `\mathop{\mathrm{GROUP}}`
promotes the box to an ordinary binary math operator with correct inter-atom
spacing on both sides (`\thickmuskip` = `5mu plus 5mu`).

**Decision.** Per jms round-2 refinement, all three multi-letter
keywords — GROUP, UNGROUP, and AS — are wrapped with `\mathop`:

```latex
R \mathop{\mathrm{GROUP}} (\{A, B\} \mathop{\mathrm{AS}} alias)
R \mathop{\mathrm{UNGROUP}} alias
```

**Alternatives considered.**

1. *Bare `\mathrm{GROUP}`* — no operator spacing; GROUP and AS appear glued
   to adjacent atoms.  Rejected: visually ambiguous.
2. *`\operatorname{GROUP}`* (amsmath) — semantically correct but requires
   `amsmath` in the preamble.  Rejected: adds a dependency not present in
   the fuzz template and inconsistent with the kernel-only goal for relational
   algebra operators.
3. *`\text{GROUP}`* — text spacing, not math spacing.  Rejected: same problem
   as bare `\mathrm`.

**No `.sty` changes required.** `\mathrm` and `\mathop` are LaTeX kernel
primitives available in every LaTeX distribution.

**Implementation.** `_generate_group` and `_generate_ungroup` in
`src/txt2tex/latex_gen.py`.  Attribute and alias names pass through
`_emit_attr_name` (identity function after the relvar removal; see the next ADR).

## ADR: Remove relvars, Add pk Primary-Key PK-Line Annotation (Phase 2.1 revised)

**Decision**: Remove the `relvars` declaration feature entirely.  Replace it
with a `pk` prefix in **named schema bodies only**.  The generator emits a
plain-math PK statement after the schema box rather than using `\underline{}`
inside the box.

**Supersedes**: "ADR: Relvar Set and Decoration-Outside-\mathrm Rule (Phase 2.1)"
above, which is now historical record only.

**Context**: The original Phase 2.1 design added `relvars` to render relation
names in `\mathrm{}` (upright roman).  After further review of the relational
algebra materials and fuzz constraints:

1. Fuzz rejects `\mathrm{}` in schema title positions.
2. Fuzz also rejects `\underline{attrname}` in declaration-variable positions —
   the fuzz schema parser expects a plain identifier in the variable-name slot;
   any macro with a brace argument (`\underline{class}`) is a syntax error.
3. The only visible convention for primary keys is an annotation below the
   schema box, not inline markup.

**pk scope** — named schemas only:

`pk` is parsed and accepted in `_parse_schema` when `name is not None`.  It
raises `ParserError` in all other declaration contexts:

- `axdef` / `gendef` — "Primary-key annotation is only valid in schema bodies"
- Anonymous `schema ... end` — "Primary-key annotation requires a named schema"
- Inline schema text `[ pk a : T | ... ]` — "Primary-key annotation requires
  a named schema; inline schema text is anonymous"

**pk grammar** (named schema bodies only):

```text
pk_decl ::= 'pk' name (',' name)* ':' expr
```

`pk` before `Delta` or `Xi` is rejected: those tokens introduce schema
inclusions, not attribute declarations.

**What changed**:

- `TokenType.RELVARS` → `TokenType.PK`; keyword `"relvars"` → `"pk"`
- `Relvars` AST node removed from `ast_nodes.py` and `DocumentItem` union
- `Declaration` gains `is_primary_key: bool = False` (frozen dataclass default)
- Parser: `_parse_relvars` removed; `_parse_declaration_or_inclusion` gains a
  `pk`-prefix branch; `_parse_schema` adds PK dispatch (named only);
  `_parse_axdef`, `_parse_gendef`, `_parse_schema_text` raise ParserError on PK
- Generator: `_collect_relvars`, `relvar_set`, `wrap_relvar` parameter,
  `_generate_relvars` all removed; `_emit_attr_name` returns `name` unchanged;
  `_generate_schema` collects pk attribute names and appends the PK line after
  `\end{schema}` when the schema has a name and any pk attrs exist
- Tests: `test_relvars.py` deleted; test_algebra, test_bindings, test_group_ungroup
  updated; `test_primary_keys.py` added (32 tests)

**LaTeX emission** — after `\end{schema}`, if any pk attrs and schema is named:

```latex
\noindent$\mathrm{PK}(\mathrm{SchemaName}) = \{attr1, attr2\}$
```

This sits outside every Z environment: fuzz ignores it; pdflatex renders it in
upright math below the schema box.  For composite keys, all pk-marked attribute
names are comma-separated inside the set literal.

**Schema box is plain**: Declaration lines inside the schema box emit
`attrname : TypeExpr` with no markup on `attrname`, regardless of
`is_primary_key`.  This keeps fuzz happy.

**Options considered**:

1. *Keep relvars, add pk* — rejected: relvars is incorrect (fuzz type errors
   in schema titles) and the relational algebra convention does not use upright
   relation names.
2. *`\underline{attrname}` inside schema box* — attempted; rejected: fuzz
   rejects any braced macro in the variable-name position of a schema
   declaration.  The PK-line approach is the only fuzz-compatible alternative.
3. *Custom fuzz macro* — rejected: would require modifying `fuzz.sty`, which
   is a third-party asset under its own license.
4. *Capitalisation heuristic* — rejected: single-letter type variables (`N`,
   `Z`, `X`) are uppercase but not relation names; explicit declaration is
   required.

## ADR: WYSIWYG Line Breaks for Algebra and Set Operators

**Date:** 2026-05-19
**Status:** Accepted

**Context.** Long relational-algebra and set expressions overflow the page.
A multi-join chain is representative:

```text
pi[winner, venue, tier](Tournament bowtie Match bowtie
  rho[tournament as id](pi[tournament](sigma[venue = 'Centre Court'](Match))))
```

That expression is approximately 145 characters on one line. The existing
line-break mechanism (`\` continuation and natural newline after operator)
already worked for logical operators (`land`, `lor`), comparisons, equality,
and quantifier separators (`@`, `|`). The algebra and set operators
(`bowtie`, `cross`, `div`, `intersect`, `union`, `setminus`, `++`,
`group`, `ungroup`) were not included, so any attempt to break them across
lines silently failed or produced malformed LaTeX.

**Decision.** Extend the same line-break mechanism to all algebra and set
operators. The parser recognises a natural newline or an explicit `\`
continuation after any of these tokens and sets a `line_break` flag on
the resulting AST node. The generator dispatches on context:

- **Display position** (outside any environment body): the chain wraps in
  `\begin{array}{l}...\end{array}` with `\\` between continuations.
- **Inside `where` predicate** (`schema`, `axdef`, `zed`): `\\` is emitted
  inline, with no array wrapper. This matches the existing `land`/`lor`
  behaviour and is the form fuzz type-checks correctly (per jms guidance).

Z-semantic neutrality confirmed by jms: no operator's parse tree changes —
only presentation. The same expression tree is produced whether or not the
author inserts line breaks.

**Alternatives considered.**

1. *`adjustbox` auto-shrink everywhere* — applied globally, this shrinks
   content past the ~70% threshold where subscripts become illegible.
   Rejected: adjustbox is retained for ARGUE/EQUIV/PROOF blocks where
   the author has no natural break points; it is not appropriate as a
   fallback for structured algebra expressions.

2. *Automatic line-breaking by the generator* — the generator could insert
   breaks at every operator boundary when the estimated line length exceeds
   a threshold.  Rejected: the author controls where breaks are meaningful
   (e.g., between major sub-expressions, not inside arguments to `sigma`).
   Forced breaks obscure proof structure.

3. *Named-relation abbreviation via `==`* — introduce an abbreviation for
   each sub-expression to shorten the outermost line.  Valid as a Z
   technique, and still recommended for very deeply nested expressions.
   Rejected as the sole mechanism because it forces schema-level names for
   transient query fragments, polluting the specification namespace.

**Caveat: `setminus` and the `\` token.** The `setminus` keyword renders
as `\setminus`, but the continuation marker is also the character `\`. The
lexer rule is: `\` at end of line → `CONTINUATION`; `\` followed by any
non-newline character → `SETMINUS`. This means a continuation cannot be
placed immediately after `setminus` — break before `setminus` instead, or
use parentheses to group.

**Implementation.** Parser changes in `src/txt2tex/parser.py`; generator
changes in `src/txt2tex/latex_gen.py`. No new AST nodes; `line_break: bool`
field added to the affected binary-operator dataclasses.

---

## ADR: Tier-2 Keyword Algebra Rendering (Phase 2.2 revised)

**Date:** 2026-05-19
**Status:** Accepted

### Context

The initial Phase 2.2 implementation emitted relational algebra in
Codd/Date Greek-letter form: `\sigma_p(R)`, `\pi_{A}(R)`, `\rho_{A \to B}(R)`,
`R \otimes_p S`. These glyphs came from Date's textbook chapters, which use
the Greek-letter convention. The keyword-algebra convention consistently
uses the keyword form — `Restrict`, `Project`, `Rename`, `Join` — written upright
(`\mathrm`), with theta-join in function-call form rather than infix.

### Decision

Adopt **Tier 2** keyword emission for relational algebra. Source keywords
(`sigma`, `pi`, `rho`, `join`, `div`) and AST nodes (`Restrict`, `Project`,
`Rename`, `NaturalJoin`, `Divide`) remain unchanged. Only the LaTeX *output*
of the generator changes.

| Source | Before (Greek) | After (keyword form) |
|--------|----------------|----------------------|
| `sigma[p](R)` | `\sigma_{p}(R)` | `\mathrm{Restrict}_{p}(R)` |
| `pi[A, B](R)` | `\pi_{A, B}(R)` | `\mathrm{Project}\{A, B\}(R)` |
| `rho[A as B](R)` | `\rho_{A \to B}(R)` | `\mathrm{Rename}_{A \to B}(R)` |
| `R join S` | `R \otimes S` | `\mathrm{Join}(R, S)` |
| `R join [p] S` | `R \otimes_{p} S` | `\mathrm{Join}_{p}(R, S)` |
| `R div S` | `R \div S` | `R \div S` — unchanged |

> **Note (2026-05-23)**: The `bowtie` keyword was renamed to `join` and the
> natural-join emit changed from `\otimes` to `\mathrm{Join}(R, S)`. See
> "ADR: Source keyword `bowtie` → `join`; emit `\mathrm{Join}` not `\otimes`".
>
> **Note (2026-05-23)**: Project emission changed from the brace form
> `\mathrm{Project}\{A, B\}(R)` to the subscript form
> `\mathrm{Project}_{A, B}(R)` (#146).  The row above for `pi[A, B](R)`
> now emits `\mathrm{Project}_{A, B}(R)`.
>
> **Note (2026-05-23)**: The `rho[A as B](R)` prefix keyword has been
> retired (#147); relation rename now uses the postfix bracket form
> `R[NEW/OLD]` and emits as a literal pass-through `R[B/A]` (no
> `\mathrm{Rename}` macro).  The row above for `rho[A as B](R)` no
> longer parses.  See "ADR: Relation Rename — adopt `R[NEW/OLD]`,
> retire `rho`".

Two shape changes merit attention:

1. **Project uses literal braces**, not subscript. The keyword-algebra convention writes
   `Project{username, job}(Members)` with `\{...\}` around the attribute list.
   Restrict and Rename keep subscript form.

2. **Both join forms use function-call form**: `R join S` emits
   `\mathrm{Join}(R, S)` and `R join [p] S` emits `\mathrm{Join}_{p}(R, S)`.
   The NaturalJoin AST node carries `subscript: Expr | None`; the generator
   dispatches on that field.

### Rejected alternative: Tier 3 render-mode flag

A `use_trigoni_style` CLI flag toggling between Greek and keyword emission was
considered. Rejected because:

- Greek glyphs were never specified by Z or by any txt2tex consumer outside
  the keyword-algebra convention. They came from Date's textbook and are not
  used in the keyword form adopted here.
- A flag doubles the test surface and adds CLI plumbing for a feature with one
  user and one mode.
- If a future user needs Greek-letter rendering, the flag can be added as a
  one-edit-site change without rework.

### Provenance

Keyword-algebra style observed in reviewed materials:

- `Restrict`, `Project`, `Rename` used consistently for the sigma/pi/rho operators.
- `Join_p(R, S)` function-call form for theta-join (infix `\otimes_p` rejected).
- Natural join: as of 2026-05-23, emits `\mathrm{Join}(R, S)` (not `\otimes`).
  See "ADR: Source keyword `bowtie` → `join`; emit `\mathrm{Join}` not `\otimes`".

---

## ADR: Dependent-domain detection in Spivey-form quantifier collapse

**Date:** 2026-05-20
**Status:** Accepted

### Context

The Spivey-form generator (Phase 3.1) collapses nested same-quantifier
chains into a single Z schema-text argument: `\forall x : A; y : B @ P`
instead of `\forall x : A @ \forall y : B @ P`. Z RM §3.5 specifies that
schema-text declarations are *sequentially scoped* — a later declaration's
domain may reference a name bound by an earlier one (e.g., `y : 1..x`
where `x` is already declared). Fuzz, however, *parallel-binds* all
declarations in one schema text: names introduced by one declaration are
not in scope for co-declarations' domains. Collapsing a dependent chain
therefore produces output fuzz rejects.

The same structural issue applies to `lambda` chains via
`_collect_lambda_chain`, and to set comprehensions via
`_generate_set_comprehension`.

### Decision

Thread a free-variable analysis through the chain helpers. A new module,
`src/txt2tex/free_vars.py`, exports `expr_free_vars(expr) → frozenset[str]`
with an explicit branch for every `Expr` member (38 total). Binders subtract
their bound names before recursing into body/expression but do *not* subtract
from domain analysis (correct: the domain is in the outer scope).

`Binding` nodes raise `NotImplementedError` rather than falling through
to a generic case (#141, djb 2026-05-22 INFO).  A `Binding` reaching
this code path indicates a generator bug; silent fall-through would
return an empty free-variable set and mask the upstream defect.

At each step in `_collect_quantifier_chain` and `_collect_lambda_chain`, the
helper checks whether the next declaration's domain mentions any name already
accumulated by prior declarations. On a dependency, it stops the collapse,
emits the independent prefix as a partial Spivey schema text, and recurses on
the remaining tail — the split-identity of Z RM §3.9 (`\forall D_1 @ \forall D_2 @ P`
≡ `\forall D_1; D_2 @ P` only when D₂'s domain is free of D₁'s names).

For set comprehensions, no analogous split identity exists in Z RM §3.10.
`_generate_set_comprehension` raises `ValueError` with a clear message when
a dependent extra declaration is detected, directing the user to rewrite.

### Alternatives rejected

1. **Fuzz-style parallel-binding semantics in the parser.** Changing the
   parser to treat schema-text declarations as parallel-bound would be
   semantically incorrect — Z is sequentially scoped. Invasive and wrong.
2. **Speculative parse-then-backtrack.** Generate collapsed form, run fuzz,
   backtrack on rejection. Adds latency, couples the generator to the fuzz
   binary, and produces misleading error attribution.
3. **All-or-nothing collapse.** Disable collapse whenever any declaration in
   the chain references a prior name. Correct but forfeits the Spivey benefit
   on the independent prefix, which is often the majority of the chain.
4. **New AST node `MixedQuantifierChain`.** Distinguishing dependent and
   independent sub-chains at the AST level is over-engineering for what is a
   private generator helper concern.

### Consequences

- Fuzz-clean output in both shapes: Spivey collapsed form for independent
  chains; nested form for dependent chains.
- `expr_free_vars` is reusable for future generator work (capture analysis
  for substitution, occurrence checking, etc.).
- `sem/solutions-corrected.txt` — the Phase 3 regression input — now
  fuzz-typechecks without the v2 workaround conjunct that was required before
  this fix.
- 11 xfail tests in `tests/test_spivey_dependent_domain.py` flipped to PASS.

### Z RM citations

- §3.5 — schema-text sequential scoping
- §3.9 — forall/exists split identity (valid only for independent declarations)
- §3.10 — set comprehension (no split identity; dependent case is a user error)
- §3.12 — lambda domain rule

**Test count delta**: 3893 → 3925 (32 new pk tests; relvars tests deleted).

## ADR: Schema-text Quantification — Extend Quantifier, Not New Node (Z RM §3.10)

### Context

Z RM §3.10 permits schemas to appear directly as quantifier bindings:

```text
∃ ΔS • P     ∃ ΞS • P     ∃ S • P     ∃ S' • P
```

and the same for `∀` and `∃₁`.  Before this change, txt2tex rejected all
four forms with "Expected variable name or tuple pattern after exists".
The SBM coursework exercises (Ex 21, 24, 26) fell back to `LATEX:` blocks,
defeating the engine's purpose.

### Decision

**Extend the existing `Quantifier` node** with a `schema_binding` field
(`SchemaBinding | None`) rather than introducing a separate
`SchemaQuantifier` node.

jms reasoning (2026-05-21): "The variation lives in the *declaration*, not
in the quantifier.  A `\forall` is a `\forall` regardless of whether its
binding is a variable list or a schema name.  Separating them into two AST
nodes would either require the generator to dispatch twice on the same
semantic concept, or force every visitor to handle both nodes for what is
really one idea."

`SchemaBinding` is a frozen dataclass with four fields:

```python
@dataclass(frozen=True)
class SchemaBinding(ASTNode):
    decoration: Literal["Delta", "Xi", "None", "Prime"]
    schema_name: str  # raw lexer value, e.g. "BoxOffice", "S'"
```

When `Quantifier.schema_binding is not None`, the `variables`, `domain`,
and `tuple_pattern` fields are unused (`[]` / `None`).

### Alternatives rejected

1. **Separate `SchemaQuantifier` node.** Would duplicate all quantifier
   generator logic (paren wrapping, depth tracking, `_quantifier_needs_parens`)
   and require every caller that handles `Quantifier` to also handle
   `SchemaQuantifier`.  jms rejected this directly.

2. **Desugar in the engine** (expand `ΔS` into its component variables).
   Requires knowing schema signatures at parse time, which would couple the
   parser to a schema symbol table.  Also wrong semantically: fuzz's own
   `\Delta` macro does the expansion; the engine should emit the schema
   reference and let fuzz handle it.  jms ruling: "emit literally, let fuzz
   expand".

3. **Treat all uppercase-identifier-without-`:` as schema binding.**
   Would break `exists N | P` where `N` is a variable of a known type used
   without a domain annotation.  The uppercase-initial heuristic is correct
   for Z convention (schema names are capitalised; variables are not) and
   matches the disambiguation specified in jms's ruling.

### Disambiguation rule

After consuming the quantifier keyword, the parser inspects the next token:

- `DELTA` or `XI` token → schema binding (explicit decoration).
- `IDENTIFIER` with uppercase initial, followed by a token that is
  NOT `:` or `,` → schema binding (bare or primed schema).
- Anything else → value-binding path (existing behaviour unchanged).

The `:` test preserves `exists S : T | P` as a value binding where `S`
happens to start with uppercase.

### LaTeX emission (jms ruling 2026-05-21)

No thin-space (`\,`) between decoration and schema name.  fuzz's `\Delta`
macro bonds lexically to the following identifier.  Emit:

```text
\exists \Delta S @ P     (fuzz mode; @ is the spot/bullet)
\exists \Xi S @ P
\exists S @ P
\exists S^{\prime} @ P   (prime as superscript, not a raw apostrophe)
```

Prime handling: strip trailing `'` from the raw identifier, emit
`^{\prime}` for each one.  fuzz recognises this as a decoration.

### Consequences

- `_generate_schema_quantifier` routes at the top of `_generate_quantifier`
  before the lambda and chain-collapse branches — no interference.
- `_quantifier_needs_parens` works unchanged: it inspects `node.body` and
  `node.expression`, not `node.variables`.
- The fuzz round-trip tests (Counter/IncrCounter miniature promotion) pass,
  confirming fuzz accepts `\exists \Delta Counter @ true` and
  `\exists \Delta Counter @ IncrCounter`.

**Test count delta**: 4230 → 4257 (27 new schema-text quantifier tests).

## ADR: Multi-line `LATEX:` block (issue #137, commit `3b80a19`)

### Context

Each single-line `LATEX:` directive becomes its own paragraph and strips
leading whitespace, so multi-line listings — manual bibliographies, tikz
diagrams, multi-line environments — rendered double-spaced and de-indented.
Wrapping in `\begin{verbatim}` is no help: the paragraph breaks are
inserted before LaTeX sees the body.

### Decision

Add an **additive** multi-line block form parallel to the existing
single-line directive.  A line that is exactly `LATEX:` followed by only
optional whitespace before its newline opens the block; a column-0 `END`
on its own line closes it.  The body is captured verbatim by the lexer
and emitted directly to the `.tex` output with no escaping, no wrapper,
and no paragraph breaks between lines.

Single-line `LATEX: <content>` semantics are unchanged.  The
disambiguation is lexical: if a non-whitespace character follows the
colon on the same line, the directive is single-line.

### Alternatives rejected

1. **Modify consecutive single-line `LATEX:` to coalesce into one block.**
   Would silently change the rendering of existing documents — manual
   `thebibliography` entries rely on the per-line `\par` to separate
   `\bibitem` entries.
2. **Add an escape syntax (`LATEX_BLOCK:` or `LATEX{`).**  Two distinct
   keywords with overlapping purpose multiplies surface area; the
   alone-on-a-line / `END` rule is unambiguous and mirrors `B:`.

### Consequences

- The user guide documents both forms side-by-side; reference.tex
  documents them as one entry with two syntaxes.
- 9 regression tests in `tests/test_multiline_latex.py`.

## ADR: `B:` block for B-machine verbatim listings (issue #138)

### Context

B-Method / Atelier-B machine listings need fixed-width font and
literal-character rendering — backslashes, braces, percent signs appear
exactly as typed.  `LATEX:` does not provide that: its body is emitted
as live LaTeX, so `\` triggers macro expansion and `{` opens a group.

### Decision

Introduce a dedicated `B:` block.  The lexer slurps the body verbatim
until a column-0 `END`; the generator wraps the body in
`\begin{verbatim}…\end{verbatim}`.  The block rejects a literal
`\end{verbatim}` in the body (djb 2026-05-22 security review): inside
LaTeX `\begin{verbatim}` there is no in-band escape sequence, so a
literal terminator would close the environment and allow arbitrary
LaTeX to follow.

### Alternatives rejected

1. **A `--raw` flag on `LATEX:`.**  Overloads one keyword with
   incompatible semantics (interpreted vs verbatim).  The two
   constructs render fundamentally differently — fixed-width vs body
   font, literal vs interpreted — and a flag obscures that.
2. **Generic `VERBATIM:` block.**  `B:` makes the intent explicit
   (B-machine listings) and keeps the door open for other
   domain-specific verbatim forms if needed.

### Consequences

- B-method coursework can embed machines without escaping; cf.
  `examples/05_sets/bags.txt` and the SBM coursework.
- The bare `B` identifier subsequently regressed (see the next ADR);
  the regression was fixed by lexing `B:` from the two-character
  sequence rather than reserved-word membership.

## ADR: Bare-`B` identifier preserved alongside `B:` block keyword

### Context

The `B:` block (#138) added `"B"` to `RESERVED_WORDS` in the lexer, on
the assumption that a one-letter reserved word would not collide with
identifier use.  The all-courseware regression sweep surfaced SBM
ex14, which declares `B! : P BookingId` — an output-state variable
literally named `B`.  The lexer raised
`Cannot decorate reserved keyword 'B'`, breaking a valid Z
declaration (commit `772861d` ships the fix).

### Decision

Remove `"B"` from `RESERVED_WORDS`.  The `B:` block trigger at
`lexer.py:1347` is the literal two-character comparison
`value == "B" and self._current_char() == ":"`; it does **not**
require `B` to be in the reserved-words set.  Bare `B` is once again
a usable identifier with the full `' ? !` decoration set.

### Alternatives rejected

1. **Forbid `B` as an identifier name.**  Too aggressive for Z's free-
   name convention; users may pick any one-letter name in any binding.
2. **Reserve `B` only when followed by `:` at column 0.**  The lexer
   already does this implicitly via the two-character trigger; no
   additional reservation is needed.

### Consequences

- 4 regression tests in `tests/test_b_decoration.py` lock in both
  behaviours: `B!`/`B'`/`B?` lex as decorated identifiers; `B:` at
  line start still opens the block.
- The all-courseware regression sweep moved from 95/96 to 96/96.

## ADR: GROUP aggregate form (issue #140)

### Context

The relational `group` operator originally supported only the regroup
form `R group ({attrs} as alias)`, which bundles attribute values into
a nested relation.  Computing summary statistics required a manual
`LATEX:` workaround for every column, defeating the engine's typed-AST
benefits and making per-column changes a passthrough edit.

### Decision

Add a second, **mutually exclusive** form to the parser:
`R group (Count(attr) as alias)`, with six aggregator keywords
recognised as reserved tokens — `Count`, `Sum`, `Avg`, `Min`, `Max`,
`Median`.  Multiple aggregators may be comma-separated.  Mixing the
regroup form (`{attrs}`) with aggregate form within the same `group`
RHS is a parse error.  The `as` keyword is reserved (`TokenType.AS`)
so the alias position is unambiguous.

Each aggregator emits
`\mathrm{Aggregator}(attr)~\mathrm{as}~alias`, matching the
rendering style of the other relational-algebra operators
(`\mathrm{Project}`, `\mathrm{Restrict}`, `\mathrm{Rename}`, etc.).

> **Note (2026-05-23)**: `\mathrm{Rename}` was retired by #147; relation
> rename now emits as a literal pass-through `R[NEW/OLD]`.  The example
> list above is from the pre-#147 era and is preserved as written.

### Alternatives rejected

1. **Separate `groupby` keyword for the aggregate form.**  Forks the
   relational-algebra surface and creates two operators users must
   remember.  `group` is the conceptual operation; aggregate vs
   regroup is a sub-form.
2. **Allow both forms in the same RHS** (e.g. `group ({a} as b,
   Count(c) as d)`).  Z RM has no canonical semantics for the mix;
   forcing a choice keeps the engine pre-canonical.

### Consequences

- DAT sheet 1 question 3 and sheet 2 question 5 use the aggregate form
  natively; both were previously `LATEX:` passthrough.
- 33 tests in `tests/test_group_aggregators.py`.

## ADR: Prefix-operator atomic-argument paren wrap (issue #133, jms ruling 2026-05-22)

### Context

Z RM §3.7 (and the operator table in §3.10) makes every prefix-generic
operator — `\power`, `\seq`, `\seq_1`, `\iseq`, `\bag`, `\dom`,
`\ran`, `\bigcup`, `\bigcap`, `\#`, `\id`, `\inv` — parse with the
*atomic* expression to its immediate right.  The grammar production is
`PrefixOp Expression0`, where `Expression0` is an atom: an identifier,
a `(…)`-group, a `{…}`-set, or a `[…]`-binding.  A prefix application
is **not** itself `Expression0`.

txt2tex's emitter previously special-cased only `bigcup`/`bigcap` for
this — `\bigcup (\ran s)` worked, but `\seq \power X` and
`\ran \bigcup (\ran s)` did not, and fuzz rejected them.

### Decision

Generalise the wrap condition.  When the outer prefix-generic operator
is in `_FUZZ_FUNCTION_LIKE_UNARY` *and* its operand is also a prefix
application from that set, wrap the operand in parens.  A single
condition replaces several special cases.

jms ruling (2026-05-22): "Parentheses around a prefix application are
semantically transparent — `(\power X)` and `\power X` denote the same
set.  You cannot over-parenthesise this class.  Wrap the operand
whenever it is another prefix application."

### Alternatives rejected

1. **Require users to write the parentheses themselves.**  Leaks fuzz's
   atomicity quirks into the surface notation.  The whole point of the
   engine is to keep the input close to whiteboard form.
2. **Wrap unconditionally** (always emit `\seq (X)`).  Over-parens
   that, while harmless to fuzz, clutter the rendered output and
   contradict Z RM convention for atomic right-operands.

### Consequences

- 8 regression tests in `tests/test_prefix_paren_wrap.py` (`seq (P X)`,
  `ran (bigcup (ran s))`, `P (P X)`, etc.).
- The all-courseware sweep emits these forms in the byte-identical
  shape fuzz accepts.

## ADR: `GroupAggregate` abbreviation routes to inline math (issue #142)

### Context

`Name == <expr>` is two different things to the engine depending on
the RHS shape:

- **Z paragraph** (the default): wrapped in `\begin{zed}…\end{zed}`,
  which fuzz typechecks.
- **Inline math** (relational-algebra family): emitted as
  `\noindent $Name == \mathrm{...}$`, which fuzz does *not* typecheck,
  because the `\mathrm{Project}(...)`, `\mathrm{Restrict}(...)`,
  `\mathrm{Group}(...)` labels are not Z paragraph syntax.

The choice is made by checking the RHS AST against
`_DAT_EXPRESSION_TYPES`, a tuple of node classes that route to inline
math.  Before #142, `GroupAggregate` was missing from that tuple, so
`B == R group (Count(x) as t)` routed to `\begin{zed}` and fuzz
rejected the body.

### Decision

Add `GroupAggregate` to `_DAT_EXPRESSION_TYPES` (single-line change at
`latex_gen.py:5154`).  All six relational-algebra families are now
treated uniformly: `Restrict`, `Project`, `Rename`, `NaturalJoin`,
`Divide`, `Binding`, `Group`, `GroupAggregate`, `Ungroup`.

### Alternatives rejected

1. **Emit the aggregate as a Z paragraph and add corresponding
   `\Group`, `\Count`, … macros to a custom `.sty` file.**  Would
   require shipping a patched fuzz stylesheet and re-coordinating with
   any future fuzz upgrade.  The inline-math route exists precisely
   for engine-internal labels that don't map to fuzz's Z grammar.
2. **Move the routing decision into a `routes_to_inline_math` method
   on each AST node.**  Spreads the policy across 50+ classes when
   today the policy is a single small tuple.  A tuple is the right
   data structure until the count of "yes"-classes exceeds the count
   of "no"-classes.

### Consequences

- DAT s2q5 (c) algebra chain — three abbreviation lines using
  `Count(...)` and a `rho`/`join`/`pi` composition — fuzz-typechecks
  and renders cleanly without any `LATEX:` passthrough.
- 1 regression test in `tests/test_group_aggregators.py`
  (`test_abbreviation_aggregator_routes_to_inline_math`).

## ADR: Source keyword `bowtie` → `join`; emit `\mathrm{Join}` not `\otimes`

### Context

The original engine used:

- Source keyword: `bowtie` (a LaTeX symbol name, not an English word)
- Natural-join emit: `R \otimes S`  (the ⊗ tensor-product symbol)
- Theta-join emit: `\mathrm{Join}_{p}(R, S)` (already correct)

The instructor's canonical vocabulary, confirmed in slides/topic02.pdf page 45, is:

> "We write Join(r, s). This kind of join is commonly referred to as a
> 'natural join'. Note that if r and s have nothing in common then
> Join(r, s) degenerates to r ⊗ s."

Two problems followed:

1. **Wrong symbol.** `⊗` denotes the *degenerate* Cartesian-product case
   (no common attributes), not the natural join. Emitting `\otimes` for
   every natural join was semantically incorrect.
2. **Wrong keyword.** `bowtie` names a LaTeX macro, not an English operator.
   The course uses `Join` consistently. Students who read the slides then
   write `R join S` in their `.txt` files got a parse error.

jms confirmed (prior to this change) that `\mathrm{Join}(R, S)` (no
subscript) is fuzz-compatible: fuzz parses `\mathrm{...}` as an identifier,
and a subscript-less form is a strict subset of the already-accepted
`\mathrm{Join}_{p}(R, S)`.

### Decision

1. Rename the source keyword `bowtie` → `join` (hard rename; no alias).
2. Rename `TokenType.BOWTIE` → `TokenType.JOIN` in `tokens.py`.
3. Change the natural-join emit: `R \otimes S` → `\mathrm{Join}(R, S)`.
4. Preserve theta-join emit: `R join [p] S` → `\mathrm{Join}_{p}(R, S)`.
5. Migrate all source `.txt` files in `examples/` and
   `course-ox-dat/exercises-worked/` (sbm/sem had no join usage).

The AST class `NaturalJoin` retains its name for internal clarity; only
the source-level keyword and token type rename.

### Rejected alternatives

1. **Keep `bowtie` as a deprecated alias.** Rejected — the mission mandates
   a hard rename with no shims. Aliases accumulate forever and confuse
   error messages.

2. **Keep `\otimes` and just rename the keyword.** Rejected — `\otimes`
   is semantically wrong per the slides. The symbol denotes the degenerate
   case; using it for the general case is a lie to fuzz-trained readers.

3. **Use the bowtie Unicode symbol ⋈ as an alternate emit.** Rejected —
   fuzz does not define `\bowtie` as a Z operator; ⋈ requires an
   extra LaTeX package and is not in fuzz.sty.

### Consequences

- Any `.txt` file using `bowtie` must be migrated to `join` — the old
  keyword lexes as an IDENTIFIER, so parsers won't silently misinterpret it;
  they produce a type error at the expression level.
- Natural join now reads `\mathrm{Join}(R, S)`, matching the instructor's
  slides and the theta-join form, giving a consistent vocabulary:
  `Join`, `Restrict`, `Project`, `Rename`.
- `\otimes` is gone from all generated output; the symbol is now available
  for its correct Z-algebra meaning (degenerate cross-product), should a
  future operator need it.
- 5 new regression tests in `tests/test_14_relational_databases/test_algebra.py`
  (`TestJoinRenameRegression`) confirm the rename end-to-end.

---

## ADR: Relation Rename — adopt `R[NEW/OLD]`, retire `rho` (issue #147)

### Context

The original engine used a prefix keyword `rho[A as B](R)` to express relation
renaming, emitting `\mathrm{Rename}_{A \to B}(R)`.  This has three problems:

1. **Not Z RM.** Z RM §3.11 writes `R[b/a]` as postfix syntax on an expression,
   not a prefix function call.  The `rho` keyword was an invention with no
   grounding in Spivey or the course slides.

2. **Fuzz rejects it in Z paragraphs.** `\mathrm{Rename}_{...}(...)` is not
   part of fuzz's Z grammar.  Any attempt to use rename inside a Z block fails.

3. **Direction inversion.** The old implementation stored pairs as
   `(old, new)` internally but the Z RM convention is `(new, old)` — `b/a`
   means rename `a` to `b`, so `b` (the new name) appears first.

jms ruling (2026-05-23):

> "`R[b/a]` on a relation is NEVER valid Z in any paragraph context; fuzz
> rejects `/` in bracket position.  Emit `R[NEW/OLD]` literally as a
> pass-through.  Do not call it `\mathrm{Rename}` anywhere."

### Decision

1. **Retire `rho`.** Remove `TokenType.RHO` from `tokens.py`; remove `"rho"`
   from `KEYWORD_TO_TOKEN` and `RESERVED_WORDS` in `lexer.py`.  `rho` now
   lexes as a plain `IDENTIFIER`.

2. **New AST node `RelationRename`.** Replace the `Rename` dataclass.
   - `relation: Expr` — accepts any expression as base (compound operands).
   - `pairs: list[tuple[str, str]]` — `(new_name, old_name)` per Z RM §3.11.

3. **Postfix parsing via `_in_relational_context`.** A parser flag
   `_in_relational_context` is set `True` inside `sigma`/`pi` relation
   arguments and the right operand of `join`/`div`.  Inside that context,
   `_parse_postfix` inspects the next `[...]` group; if it contains `/` at
   depth 0, it produces a `RelationRename`.  Outside that context, `[...]` on
   an `Identifier` continues to produce `SchemaRename`.

4. **Compound-base support.** A second block in `_parse_postfix` handles
   non-Identifier/GenericInstantiation bases in relational context.  The
   adjacency check (`column <= last_token_end_column`) ensures `R [b/a]` with
   a space is not treated as postfix.

5. **Generator emits literal pass-through.** `_generate_relation_rename`
   emits `R[NEW/OLD]` with no `\mathrm` wrapper.  Compound bases are wrapped
   in parentheses: `(pi[x](R))[b/a]`.

6. **`RelationRename` in `_DAT_EXPRESSION_TYPES`.** This routes every
   abbreviation containing a relation rename through inline math
   (`\noindent$...$`), so fuzz never sees the `/`.

7. **`SchemaRename` docstring corrected.** The existing `SchemaRename`
   docstring had the pair direction as `(old_name, new_name)`.  Z RM §3.11
   puts the new name first; corrected to `(new_name, old_name)`.

### Rejected alternatives

1. **`\mathrm{Rename}` with a new name.** Rejected — jms ruling is
   unambiguous: "Do not call it `\mathrm{Rename}` anywhere."

2. **Keep `rho` as a deprecated alias.** Rejected — aliases accumulate; the
   old form was non-standard and there is no use case for teaching it.

3. **Require parentheses `(R)[b/a]` even for simple names.** Rejected —
   `R[b/a]` is the Z RM canonical form; requiring extra parens departs from
   the standard needlessly.

4. **Set `_in_relational_context` for abbreviation RHS unconditionally.**
   Rejected (jra decision A) — an abbreviation RHS like `S[a/b]` is
   legitimately a `SchemaRename`.  Forcing relational context would break
   all existing schema-rename abbreviations.  The contract is: wrap in a
   projection when a relational rename is needed at top level.

### Consequences

- All `.txt` files using `rho[A as B](R)` must be migrated to `R[B/A]`
  inside a relational context, or wrapped in `pi[all attrs](R[B/A])`.
- Generated output changes: `\mathrm{Rename}_{A \to B}(R)` → `R[B/A]`.
- fuzz acceptance: unchanged (relational expressions already routed through
  inline math; fuzz never processed them).
- 6 new parser tests (`TestRelationRenameParser`) and 2 generator tests
  (`TestRelationRenameGenerator`) in `test_algebra.py` cover the new form.
