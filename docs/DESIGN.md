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

*"Make the simple things invisible, the complex things explicit."*

Users write natural whiteboard notation, but the generated LaTeX should be recognizable and teachable. A student who learns txt2tex should be 70%+ prepared to write LaTeX with fuzz directly.

**Application**:
- ✅ **Automatic smart defaults**: Add `\quad` for indentation when users break lines
- ✅ **Automatic line breaks**: Convert newlines to `\\` in appropriate contexts
- ✅ **Automatic spacing**: Insert `~` in set comprehensions, function application
- ❌ **Don't hide LaTeX structure**: Keep environment boundaries clear (`schema...end`, not implicit)
- ❌ **Don't invent new operators**: Use Z notation conventions or ASCII approximations

### Principle 2: Align Notation with Z Standards

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

```
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

    # Operators (with context)
    AND = "and"
    OR = "or"
    NOT = "not"
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
- **Context awareness**: Same text ("or") can be operator or English word
- **Line tracking**: Maintain line numbers for error messages
- **Lookahead**: Support for multi-character operators (<=>)

**Lexer State Machine**:

```
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

**Whitespace-Sensitive Operator Disambiguation**

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
```
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
    op: str              # "and", "or", "=>", etc.
    left: MathExpr
    right: MathExpr
    explicit_parens: bool = False  # Preserves user-written parentheses

@dataclass
class UnaryOp(MathExpr):
    op: str              # "not"
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
```
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
```
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

**Word Boundary Detection**:

Critical for distinguishing "or" in "De Morgan" vs "p or q":

```python
def is_operator_context(self, token: Token) -> bool:
    """Check if this token is in an operator context."""
    # Look at surrounding tokens
    prev = self.previous_token()
    next = self.next_token()

    # "or" is operator if preceded/followed by identifier, paren, or operator
    if prev.type in [TokenType.IDENTIFIER, TokenType.RPAREN]:
        if next.type in [TokenType.IDENTIFIER, TokenType.LPAREN]:
            return True

    return False
```

### 3. Semantic Analyzer

**Responsibility**: Validate and annotate the AST with type/context information.

**Tasks**:
1. **Identifier resolution**: Track declared variables, types
2. **Type inference**: Determine types of expressions where possible
3. **Scope checking**: Ensure variables are in scope
4. **Operator validation**: Check operators are used correctly
5. **Z notation validation**: Verify schema/axdef structure

**Example**:

```python
class SemanticAnalyzer:
    def __init__(self, ast: Document):
        self.ast = ast
        self.symbol_table = SymbolTable()
        self.errors = []

    def analyze(self) -> AnnotatedAST:
        self.visit(self.ast)
        if self.errors:
            raise SemanticError(self.errors)
        return self.ast

    def visit_quantifier(self, node: Quantifier):
        # Add variable to scope
        self.symbol_table.enter_scope()
        self.symbol_table.define(node.variable)

        # Analyze body with variable in scope
        self.visit(node.body)

        self.symbol_table.exit_scope()

    def visit_identifier(self, node: Identifier):
        if not self.symbol_table.lookup(node.name):
            self.errors.append(
                f"Line {node.line}: Undefined variable '{node.name}'"
            )
```

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

```
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

```
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

```
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

**Python 3.10+**
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

```
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

## Future Enhancements

1. **LSP (Language Server Protocol)**
   - Live validation in text editor
   - Autocomplete for operators
   - Inline error messages

2. **Incremental compilation**
   - Cache parsed AST
   - Only regenerate changed sections

3. **Interactive mode**
   - REPL for testing expressions
   - Live preview

4. **IDE Integration**
   - VS Code extension
   - Syntax highlighting

5. **Export formats**
   - Markdown with MathJax
   - HTML with KaTeX
   - Plain text (pretty-printed)

6. **Import from LaTeX**
   - Reverse conversion
   - Useful for editing existing documents

## Appendix: Example Conversion

**Input (whiteboard.txt)**:
```
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
