# txt2tex: Software Design Document

## Executive Summary

**Goal**: Convert whiteboard-style mathematical notation to typechecked, high-quality LaTeX.

**Core Philosophy**: Parse, don't pattern-match. Understand structure semantically, then generate LaTeX with confidence.

**Key Features**:
1. Lexical analysis and parsing for robust conversion
2. Context-aware formatting (math vs prose vs Z notation)
3. fuzz validation integration
4. High-quality PDF generation

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
8. Multiplication (*, /)
9. Exponentiation (^)
10. Function application
11. Atoms (identifiers, numbers, parenthesized expressions)
```

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
        if self.options.use_fuzz:
            self.output.append(r'\usepackage{fuzz}')
        else:
            self.output.append(r'\usepackage{zed-cm}')
            self.output.append(r'\usepackage{zed-maths}')
            # ... other zed packages
        self.output.append(r'\usepackage{amsmath}')
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
        self.output.append(text)
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
  (a) This is true: forall x in N, x^2 >= 0
                          ^
Expected '|' or '.' after domain specification
Did you mean: forall x : N | x^2 >= 0
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
   - All bugs fixed from txt2tex_v3.py
   - Edge cases discovered during development

4. **Golden Tests**
   - Compare against reference output (solutions.pdf)
   - Pixel-perfect or text-diff comparison

### Test Structure

```
tests/
├── lexer/
│   ├── test_operators.py
│   ├── test_structural.py
│   └── test_unicode.py
├── parser/
│   ├── test_expressions.py
│   ├── test_znotation.py
│   ├── test_errors.py
│   └── test_precedence.py
├── semantic/
│   ├── test_scope.py
│   └── test_validation.py
├── generator/
│   ├── test_latex_output.py
│   └── test_formatting.py
├── integration/
│   ├── test_pipeline.py
│   └── test_errors.py
├── golden/
│   ├── inputs/
│   │   ├── simple.txt
│   │   ├── truth_tables.txt
│   │   ├── proofs.txt
│   │   └── znotation.txt
│   └── expected/
│       ├── simple.tex
│       ├── truth_tables.tex
│       ├── proofs.tex
│       └── znotation.tex
└── fixtures/
    └── solutions_complete.txt  # From parent directory
```

## Configuration

### Options

```python
@dataclass
class Options:
    # Input
    input_file: str

    # Output
    output_pdf: Optional[str]
    output_latex: Optional[str]
    keep_intermediate: bool = False

    # LaTeX packages
    use_fuzz: bool = True           # vs zed-* packages

    # Validation
    run_fuzz_validation: bool = True
    strict_validation: bool = False  # Treat warnings as errors

    # Formatting
    latex_indent: int = 2
    wrap_width: int = 80             # For generated LaTeX

    # Debugging
    debug_tokens: bool = False
    debug_ast: bool = False
    verbose: bool = False
```

### Configuration File

Optional `.txt2texrc` (YAML or JSON):

```yaml
use_fuzz: true
run_fuzz_validation: true
strict_validation: false

operator_aliases:
  implies: ["=>", "→", "⇒"]
  iff: ["<=>", "↔", "⇔"]
  and: ["and", "∧", "&"]
  or: ["or", "∨", "|"]
  not: ["not", "¬", "~"]

formatting:
  latex_indent: 2
  wrap_width: 80
```

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

1. Set up project structure
2. Implement basic lexer (operators, structural markers)
3. Implement basic parser (expressions, precedence)
4. Implement basic LaTeX generator
5. Test: Simple expressions → LaTeX

**Deliverable**: Convert `p and q => r` to LaTeX

### Phase 2: Structural Elements (Week 2)

1. Add solution/section parsing
2. Add truth table parsing
3. Add equivalence chain parsing
4. Add prose handling with inline math

**Deliverable**: Convert complete solution with truth table

### Phase 3: Z Notation (Week 3)

1. Add Z notation tokens/parsing
2. Add schema/axdef support
3. Add type definitions
4. Test with fuzz validation

**Deliverable**: Convert Z notation examples from test.tex

### Phase 4: Advanced Features (Week 4)

1. Add proof tree parsing (indentation-based)
2. Add semantic analysis
3. Add source mapping for errors
4. Improve error messages

**Deliverable**: Full pipeline with validation

### Phase 5: Polish (Week 5)

1. Comprehensive test suite
2. Documentation
3. Performance optimization
4. User testing with solutions_complete.txt

**Deliverable**: Production-ready tool

## Technology Choices

### Language

**Python 3.10+**
- Already used in txt2tex_v3.py
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
│   ├── simple.txt
│   ├── truth_tables.txt
│   └── solutions_complete.txt
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

## Open Questions

1. **Package choice**: Support both fuzz and zed-* packages, or choose one?
   - **Recommendation**: Support both, make it configurable

2. **Proof tree syntax**: Keep indentation-based or require explicit structure?
   - **Recommendation**: Start with indentation, add explicit syntax later

3. **Unicode operators**: Accept only, or convert on output?
   - **Recommendation**: Accept both ASCII and Unicode on input

4. **Justification syntax**: Keep `[...]` or change?
   - **Recommendation**: Keep it, users are familiar

5. **Error recovery**: Try to continue parsing after error?
   - **Recommendation**: Stop at first error initially, add recovery later

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

## Success Criteria

1. ✅ Convert solutions_complete.txt to PDF matching reference
2. ✅ Pass fuzz validation without errors
3. ✅ Handle all constructs from txt2tex_v3.py correctly
4. ✅ Clear error messages for malformed input
5. ✅ Fast enough for interactive use (<1s for typical document)
6. ✅ Clean, maintainable codebase
7. ✅ Comprehensive test coverage (>90%)
8. ✅ User documentation with examples

## Appendix: Comparison with txt2tex_v3.py

| Feature | v3 (Regex) | v4 (Parser) |
|---------|------------|-------------|
| Operator detection | String replacement | Token-based |
| Context awareness | None | Full context tracking |
| Error messages | Generic | Line/column specific |
| Extensibility | Hard (regex conflicts) | Easy (add tokens/rules) |
| Correctness | Fragile | Robust |
| Performance | Fast | Fast enough |
| Code complexity | Growing | Structured |
| Testing | Hard to test | Easy to unit test |
| Maintainability | Low | High |

## Appendix: Example Conversion

**Input (whiteboard.txt)**:
```
** Solution 1 **

(a) forall x : N | x^2 >= 0

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

**Output LaTeX**:
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
