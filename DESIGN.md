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
            # Default: zed-* packages (instructor's preference)
            self.output.append(r'\usepackage{zed-cm}')
            self.output.append(r'\usepackage{zed-maths}')
            if self.has_proof_trees:  # Detected during parsing
                self.output.append(r'\usepackage{zed-proof}')
            if self.has_floats:
                self.output.append(r'\usepackage{zed-float}')
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
    use_fuzz: bool = False          # True=fuzz, False=zed-* packages (default)

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
# LaTeX package choice
use_fuzz: false  # false = zed-* packages (default), true = fuzz

# Validation
run_fuzz_validation: true
strict_validation: false

# Operator aliases (both ASCII and Unicode accepted)
operator_aliases:
  implies: ["=>", "→", "⇒"]
  iff: ["<=>", "↔", "⇔"]
  and: ["and", "∧", "&"]
  or: ["or", "∨", "|"]
  not: ["not", "¬", "~"]

# Formatting
formatting:
  latex_indent: 2
  wrap_width: 80
```

## Implementation Plan

### Phased End-to-End Approach

Each phase delivers a working end-to-end system that is immediately useful for a subset of problems. This allows incremental development with regular user testing and feedback.

### Phase 0: Minimal Viable Product (MVP)
**Timeline**: 2-3 hours
**Goal**: Convert simple propositional logic to LaTeX

**Features**:
- Basic operators: `and`, `or`, `not`, `=>`, `<=>`
- Simple expressions: `p and q => r`
- Prose paragraphs with inline math
- Document structure (minimal preamble/postamble)

**Components**:
- Basic lexer (operators, identifiers, whitespace)
- Expression parser (precedence: `<=>` < `=>` < `or` < `and` < `not`)
- Simple LaTeX generator
- CLI wrapper

**Use Case**:
```
Input:  "The formula p and q => r is valid."
Output: "The formula $p \land q \Rightarrow r$ is valid."
```

**Deliverable**: Can process simple logic statements
**Test**: Convert a single paragraph with 3-5 expressions
**Quality Gates**: All 5 commands pass (type, lint, format, test, test-cov)

---

### Phase 1: Document Structure + Truth Tables
**Timeline**: 2-3 hours
**Goal**: Complete solutions with truth tables

**Add**:
- `=== Section ===` headers
- `** Solution N **` markers
- `(a)`, `(b)`, `(c)` part labels
- `TRUTH TABLE:` environment
- Proper spacing (`\bigskip`, `\medskip`)

**Use Case**:
```
** Solution 1 **

(a) Construct a truth table for p => q

TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T
```

**Deliverable**: Can process complete homework solutions with truth tables
**Test**: Convert solutions 1-3 from test file
**Quality Gates**: All 5 commands pass

---

### Phase 2: Equivalence Chains + Justifications
**Timeline**: 1-2 hours
**Goal**: Step-by-step proofs with justifications

**Add**:
- `EQUIV:` environment
- Justifications in `[brackets]`
- Multi-step equivalence chains
- Operator handling in justifications

**Use Case**:
```
EQUIV:
p and q
<=> q and p [commutative]
<=> q and p [idempotent]
```

**Deliverable**: Can process equivalence proofs
**Test**: Convert solutions with EQUIV blocks
**Quality Gates**: All 5 commands pass

---

### Phase 3: Quantifiers + Subscripts/Superscripts
**Timeline**: 2-3 hours
**Goal**: Predicate logic and mathematical notation

**Add**:
- `forall x : Domain | predicate` syntax
- `exists` quantifier
- Superscripts: `x^2`, `2^n`
- Subscripts: `a_1`, `x_i`
- Set operators: `in`, `subset`, `union`, `intersect`

**Use Case**:
```
forall x : N | x^2 >= 0
exists n : N | n > 10
```

**Deliverable**: Can process predicate logic problems
**Test**: Convert solutions with quantified formulas
**Quality Gates**: All 5 commands pass

---

### Phase 4: Z Notation Basics
**Timeline**: 3-4 hours
**Goal**: Type definitions and schemas

**Add**:
- `given A, B` (given types)
- `Type ::= branch1 | branch2` (free types)
- `abbrev == expression` (abbreviations)
- `axdef ... where ... end` blocks
- `schema Name ... where ... end` blocks

**Use Case**:
```
given Person, Company

Employment ::= employed | unemployed

axdef
  population : N
where
  population > 0
end
```

**Deliverable**: Can process Z notation exercises
**Test**: Convert Z notation definitions
**Quality Gates**: All 5 commands pass

---

### Phase 5: Proof Trees (Advanced)
**Timeline**: 4-5 hours
**Goal**: Natural deduction proofs

**Add**:
- `PROOF:` environment
- Indentation-based tree structure
- Justifications/rule names
- Optional: `\infer` syntax generation for zed-proof

**Use Case**:
```
PROOF:
  p and q
    p [and-elim-1]
    q [and-elim-2]
```

**Deliverable**: Can process proof tree exercises
**Test**: Convert natural deduction proofs
**Quality Gates**: All 5 commands pass

---

---

### Phase 5b: Proof Tree Improvements ✅ COMPLETED
**Timeline**: 2-3 hours
**Goal**: Fix nested assumptions and improve proof tree rendering

**Added**:
- Boxed assumption notation: `⌜expr⌝[n]` for assumption references
- Proper handling of "from N" references
- Independent nested assumption rendering
- Consistent spacing across all proof environments
- Centered proof trees in display math mode

**Deliverable**: Natural deduction proofs with correct assumption scope and discharge notation
**Test**: Solutions 13-18 with complex nested assumptions
**Quality Gates**: All 5 commands pass
**Status**: ✅ Completed (tagged as phase5b)

---

## Coverage Assessment (As of Phase 17)

### Currently Supported ✅
- **Propositional Logic**: Truth tables, equivalence chains, basic operators (and, or, not, =>, <=>)
- **Document Structure**: Sections, solutions, part labels, proper spacing, explicit TEXT paragraphs
- **Text Paragraphs**: Explicit `TEXT:` keyword captures raw line content with operator conversion
- **Proofs**: Natural deduction with all major inference rules (=>-intro, =>-elim, and-intro, and-elim, or-intro, or-elim, false-intro, false-elim)
- **Proof Features**: Nested assumptions, discharge notation, case analysis (or-elim), boxed assumption notation
- **Quantifiers**: forall, exists, exists1, mu-operator with multi-variable support
- **Subscripts/Superscripts**: `x_i`, `x^2`, `2^n`
- **Set Operations**: in, notin, subset, union, intersect, cross (×), setminus (\), P (power set), P1, # (cardinality)
- **Set Comprehension**: `{ x : X | predicate }`, `{ x : X | predicate . expression }`, multi-variable, optional domain
- **Set Literals**: Including maplets `{1 |-> a, 2 |-> b, 3 |-> c}`
- **Tuple Expressions**: `(a, b, c)` in set comprehensions and expressions
- **Equality**: =, != in predicates and equivalence chains
- **Arithmetic**: +, *, mod, -, unary minus operators
- **Relations**: Relation type (<->), maplet (|->), domain restriction (<|), range restriction (|>), domain/range subtraction (<<|, |>>), composition (comp, ;, o9), inverse (~), transitive closure (+, *), dom, ran, inv, id, relational image (R(| S |))
- **Functions**: All function types (partial, total, injection, surjection, bijection), lambda expressions
- **Generic Parameters**: Generic definitions with [X] prefix, generic type instantiation (Type[A, B], emptyset[N], seq[N], P[X])
- **Z Notation**: Given types, free types (::=) with recursive constructors and parameters, abbreviations (==), axiomatic definitions (axdef), schemas (schema)
- **Sequences**: Sequence literals `<>`, `<a, b>`, concatenation `^`, ASCII bracket alternatives
- **Identifiers**: Multi-word identifiers with underscores (cumulative_total, not_yet_viewed)
- **Conditionals**: if/then/else expressions with proper nesting

### Coverage Statistics
- **Solutions fully working**: 36 of 52 (69.2%)
- **Solutions 1-36**: All working (propositional logic, quantifiers, equality, proofs, sets, relations, functions)
- **Solutions 37-43**: PARTIALLY IMPLEMENTED (sequences basic support, need state machines)
- **Solutions 44-47**: VERIFIED WORKING (recursive free types with constructor parameters)
- **Solutions 48-52**: NOT YET TESTED (advanced features)
- **Topics covered**: Complete coverage through function theory, generic parameters, and recursive free types
- **Topics remaining**: Full sequence operations (Phase 12), state machines (Phase 13), pattern matching

---

## Remaining Implementation (Phases 6-14)

### ⚡ Immediate Homework Needs

**User's next homework requires:**
1. **Set comprehensions** → Phase 8
2. **Relational composition** → Phase 10
3. **Generic functions** → Phase 9 + Phase 11 (partial)

**Recommended implementation order for homework:**
1. ✅ Phase 6 (Quantifiers) - foundation for set comprehensions
2. ✅ Phase 8 (Sets) - **set comprehensions needed**
3. ✅ Phase 9 (Z Definitions) - **generic syntax needed**
4. ✅ Phase 10 (Relations) - **relational composition needed**
5. ✅ Phase 11 (Functions, partial) - function types for generic functions

**Estimated time to homework readiness**: 21-31 hours
- Phase 6: 4-6h
- Phase 8: 6-8h
- Phase 9: 4-5h
- Phase 10: 8-10h (can start earlier if needed)
- Phase 11 (minimal): ~2-3h (just function signatures and type syntax)

---

### Phase 6: Quantifiers with Complex Domains
**Timeline**: 4-6 hours
**Goal**: Predicate logic with typed quantification
**Priority**: ⚡ CRITICAL (foundation for Phase 8, needed for Solutions 5-8)

**Add**:
- Quantifier syntax with domains: `forall x : Domain | predicate`
- Multi-variable quantification: `forall x, y : N | predicate`
- Nested quantifiers: `exists d : Dog | forall t : Trainer | predicate`
- Bullet operator in quantified predicates: `forall x : N | x > 0`
- Domain restrictions and type annotations

**Input Format**:
```
forall x : N | x^2 >= 0
exists d : Dog | gentle(d) and well_trained(d)
forall x, y : N | x + y = 4 and x < y
```

**LaTeX Output**:
```latex
$\forall x : \nat \bullet x^{2} \geq 0$
$\exists d : Dog \bullet gentle(d) \land well\_trained(d)$
$\forall x, y : \nat \bullet x + y = 4 \land x < y$
```

**Test Coverage**: Solutions 5-8
**Deliverable**: Can process predicate logic with typed quantification

---

### Phase 7: Equality and Special Operators
**Timeline**: 3-4 hours
**Goal**: One-point rule, µ-operator, unique existence
**Priority**: HIGH (needed for Solutions 9-12)

**Add**:
- Equality in equivalence chains: `x = y`, `x ≠ y`
- One-point rule applications in EQUIV blocks
- µ-operator (definite description): `(mu x : X | predicate)`
- ∃₁ (unique existence): `exists1 x : X | predicate`
- Set membership in predicates: `in`, `notin`
- Arithmetic in predicates

**Input Format**:
```
EQUIV:
exists y : N | y in {0, 1} and y != 1 and x != y
<=> exists y : N | y = 0 and x != y [arithmetic]
<=> 0 in N and x != 0 [one-point rule]
<=> x != 0
```

**LaTeX Output**:
```latex
\begin{align*}
\exists y : \nat \bullet y \in \{0, 1\} \land y \neq 1 \land x \neq y \\
&\Leftrightarrow \exists y : \nat \bullet y = 0 \land x \neq y && \text{[arithmetic]} \\
&\Leftrightarrow 0 \in \nat \land x \neq 0 && \text{[one-point rule]} \\
&\Leftrightarrow x \neq 0
\end{align*}
```

**Test Coverage**: Solutions 9-12
**Deliverable**: Can process equality reasoning and special quantifiers

---

### Phase 8: Sets and Set Theory
**Timeline**: 6-8 hours
**Goal**: Set operations, comprehensions, and set theory proofs
**Priority**: ⚡ CRITICAL (needed for upcoming homework + Solutions 19-23)

**Add**:
- Set membership: `in`, `notin`, `subset`, `subseteq`
- Set operations: `cap` (∩), `cup` (∪), `setminus` (\)
- Power sets: `P`, `P1` (non-empty power set)
- Cartesian products: `x` (×)
- Set comprehensions: `{ x : X | predicate }`, `{ x : X | predicate . expression }`
- Cardinality: `#` (as prefix operator)
- Empty set: `emptyset` or `{}`
- Set literals: `{1, 2, 3}`

**Input Format**:
```
1 in {4, 3, 2, 1}
{1} x {2, 3} = {(1, 2), (1, 3)}
{ z : Z | 0 <= z and z <= 100 }
{n : N | n <= 4 . n^2}
{n : P {0, 1} . (n, # n)}

EQUIV:
x in a cap b
<=> (x in a and x in b) [intersection]
<=> (x in a) [idempotence of and]
<=> x in a
```

**LaTeX Output**:
```latex
$1 \in \{4, 3, 2, 1\}$
$\{1\} \times \{2, 3\} = \{(1, 2), (1, 3)\}$
$\{ z : \mathbb{Z} \mid 0 \leq z \land z \leq 100 \}$
$\{n : \nat \mid n \leq 4 \bullet n^{2}\}$
$\{n : \mathbb{P} \{0, 1\} \bullet (n, \# n)\}$
```

**Test Coverage**: Solutions 19-23
**Deliverable**: Can process set theory exercises and proofs

---

### Phase 9: Z Notation Definitions (Complete)
**Timeline**: 4-5 hours
**Goal**: Full Z notation definition support
**Priority**: ⚡ CRITICAL (needed for upcoming homework generic functions + Solutions 24-26)

**Add**:
- Given types (basic types): `[Person]`, `[Dog]`
- Abbreviation definitions: `Name == Expression`
- Axiomatic definitions with schema boxes (proper rendering)
- Generic definitions: `[X]` with generic parameters
- Type constraints in predicates
- Schema boxes with proper formatting

**Input Format**:
```
given Person, Company

Pairs == Z x Z

StrictlyPositivePairs == { m, n : Z | m > 0 and n > 0 . (m, n) }

Couples == { s : P Person | # s = 2 }

axdef
  notin[X] : (X <-> P X)
where
  forall x : X; s : P X | x notin s <=> not (x in s)
end
```

**LaTeX Output**:
```latex
\begin{zed}
[Person, Company]
\end{zed}

\begin{zed}
Pairs == \mathbb{Z} \times \mathbb{Z}
\end{zed}

\begin{axdef}[X]
\_ \not\in \_ : (X \rel \power X)
\where
\forall x : X; s : \power X \bullet
  x \not\in s \iff \lnot (x \in s)
\end{axdef}
```

**Test Coverage**: Solutions 24-26
**Deliverable**: Can process Z notation definitions and axiomatic descriptions

---

### Phase 10: Relations
**Timeline**: 8-10 hours
**Goal**: Relational operators and relation calculus
**Priority**: ⚡ CRITICAL (needed for upcoming homework relational composition + Solutions 27-32)

**Add**:
- Relation type: `X <-> Y`
- Maplet: `x |-> y`
- Domain/range: `dom R`, `ran R`
- Domain/range restriction: `A <| R`, `R |> B`
- Domain/range subtraction: `A <<| R`, `R |>> B`
- Relational composition: `R comp S` or `R ; S`
- Forward/backward composition: `R o9 S`
- Relational inverse: `R~` or `inv R`
- Transitive closure: `R+`, `R*`
- Identity relation: `id[X]`
- Relational image: `R(| S |)`

**Input Format**:
```
dom R = {0, 1, 2}
ran R = {1, 2, 3}
{1, 2} <| R = {1 |-> 2, 1 |-> 3, 2 |-> 3}
R |>> {1, 2} = {0 |-> 3, 1 |-> 3, 2 |-> 3}

parentOf == childOf~
siblingOf == (childOf o9 parentOf) \ id[Person]
ancestorOf == parentOf+

EQUIV:
x |-> y in A <| (B <| R)
<=> x in A and x |-> y in (B <| R) [domain restriction]
<=> x in A and x in B and x |-> y in R [domain restriction]
<=> x in A cap B and x |-> y in R [intersection]
<=> x |-> y in (A cap B) <| R [domain restriction]
```

**LaTeX Output**:
```latex
$\dom R = \{0, 1, 2\}$
$\ran R = \{1, 2, 3\}$
$\{1, 2\} \dres R = \{1 \mapsto 2, 1 \mapsto 3, 2 \mapsto 3\}$
$R \nrres \{1, 2\} = \{0 \mapsto 3, 1 \mapsto 3, 2 \mapsto 3\}$

$parentOf == childOf^{\sim}$
$siblingOf == (childOf \comp parentOf) \setminus id[Person]$
$ancestorOf == parentOf^{+}$
```

**Test Coverage**: Solutions 27-32
**Deliverable**: Can process relation theory and relational calculus

---

### Phase 11: Functions
**Timeline**: 5-6 hours (2-3h minimal for homework)
**Goal**: Function types and function operators
**Priority**: ⚡ CRITICAL (partially needed for upcoming homework generic functions + Solutions 33-36)

**Add**:
- Partial functions: `X +-> Y`
- Total functions: `X -> Y`
- Partial injections: `X >+> Y`
- Total injections: `X >-> Y`
- Partial surjections: `X +->> Y`
- Total surjections: `X -->> Y`
- Bijections: `X >->> Y`
- Function application: `f x`, `f(x)`
- Function override: `f oplus {x |-> y}`
- Lambda expressions: `lambda x : X . expression`
- Relational image: `R(| S |)`

**Input Format**:
```
children : Person -> P Person
children = {p : Person . p |-> parentOf(| {p} |)}

number_of_grandchildren : Person -> N
number_of_grandchildren =
  {p : Person . p |-> # (parentOf o9 parentOf)(| {p} |)}

f : (Drivers <-> Cars) -> (Cars -> N)
forall r : Drivers <-> Cars |
  f(r) = {c : ran r . c |-> #{d : Drivers | d |-> c in r}}
```

**LaTeX Output**:
```latex
\begin{axdef}
children : Person \fun \power Person \\
children = \{p : Person \bullet p \mapsto parentOf(\limg \{p\} \rimg)\}
\end{axdef}

\begin{axdef}
number\_of\_grandchildren : Person \fun \nat \\
number\_of\_grandchildren = \\
\t1 \{p : Person \bullet p \mapsto \# (parentOf \comp parentOf)(\limg \{p\} \rimg)\}
\end{axdef}
```

**Test Coverage**: Solutions 33-36
**Deliverable**: Can process function theory and function specifications

---

### Phase 11.9: Generic Type Instantiation ✅ COMPLETED
**Timeline**: 6-8 hours actual
**Goal**: Generic type parameters for Z notation
**Priority**: CRITICAL (needed for Solutions 25, 26)
**Status**: ✅ Completed (69.2% coverage achieved - Solutions 1-36 fully working)

**Added**:
- Generic type instantiation: `Type[A, B]`, `emptyset[N]`, `seq[N]`, `P[X]`
- Whitespace-sensitive parsing: distinguishes `Type[X]` from `p [justification]`
- Token position tracking in parser for accurate whitespace detection
- Support for nested generics: `Type[List[N]]`
- Support for chained generics: `Type[N][M]`
- Support for complex type parameters: `emptyset[N cross N]`
- Generic types in quantifier/set comprehension domains: `forall x : P[N] | ...`

**Input Format**:
```
emptyset[N]
seq[N cross N]
P[X]
Type[A, B, C]
Type[List[N]]
Type[N][M]

{ s : P[N] | s = emptyset[N] }
forall x : seq[N] | # x > 0
```

**LaTeX Output**:
```latex
$emptyset[N]$
$seq[N \cross N]$
$P[X]$
$Type[A, B, C]$
$Type[List[N]]$
$Type[N][M]$

$\{ s : P[N] \mid s = emptyset[N] \}$
$\forall x : seq[N] \bullet \# x > 0$
```

**Implementation Details**:
- Added `GenericInstantiation` AST node with `base` and `type_params` fields
- Parser tracks `last_token_end_column` and `last_token_line` to detect whitespace
- Handles special case: `P[X]` where `P` is lexed as POWER token but treated as identifier for generics
- Updated domain parsing in quantifiers and set comprehensions to use `_parse_postfix()` instead of `_parse_atom()`

**Test Coverage**: Solutions 25, 26 + comprehensive test suite (16 tests in test_generic_instantiation.py)
**Deliverable**: Can process generic type specifications in Z notation
**Result**: Achieved 69.2% solution coverage (36/52 solutions fully working, Solutions 37-52 require additional features)

---

### Phase 14: ASCII Sequence Brackets and Pattern Matching ✅ COMPLETED
**Timeline**: 3-4 hours actual
**Goal**: ASCII alternatives for sequence notation and pattern matching support
**Priority**: CRITICAL (preparation for Phase 12, unblocks Solutions 40-43)
**Status**: ✅ Completed (571 tests passing)

**Added**:
- ASCII sequence brackets: `<>` as alternative to Unicode `⟨⟩`
- ASCII concatenation: `^` as alternative to Unicode `⌢`
- Whitespace-based disambiguation for `<` and `>` operators
- Context-sensitive `^` operator (concatenation after sequences, superscript elsewhere)
- Pattern matching support for recursive functions on sequences

**Key Features**:
- Lookahead for `<`: recognizes `<>`, `<x>`, `<(expr)>`, `<<nested>>`
- Whitespace check for `>`: `<x>` (no space) vs `x > y` (space before `>`)
- Lookback for `^`: `<x> ^ s` (concatenation) vs `x^2` (superscript)

**Input Format**:
```
<>                      # Empty sequence
<a, b, c>              # Sequence literal
<x> ^ s                # Concatenation
f(<>)                  # Pattern matching - empty case
f(<x> ^ s)             # Pattern matching - cons case
total(<>) = 0          # Recursive function base case
total(<x> ^ s) = x + total(s)  # Recursive function inductive case
```

**LaTeX Output**:
```latex
$\langle \rangle$
$\langle a, b, c \rangle$
$\langle x \rangle \cat s$
$f(\langle \rangle)$
$f(\langle x \rangle \cat s)$
$total(\langle \rangle) = 0$
$total(\langle x \rangle \cat s) = x + total(s)$
```

**Implementation Details**:
- Lexer: Whitespace-sensitive recognition of `<`, `>`, and `^` tokens
- Parser: Reuses `SequenceLiteral` AST node (from Phase 12)
- LaTeX: Maps both Unicode and ASCII to same LaTeX commands
- Disambiguation heuristics prevent conflicts with comparison operators

**Test Coverage**: 21 tests in test_phase14.py covering:
- ASCII sequence brackets (empty, single, multiple elements, nested)
- ASCII concatenation (after sequences, chaining, with empty)
- Pattern matching (empty pattern, cons pattern, equations)
- Comparison operator disambiguation
- Mixed Unicode/ASCII usage

**Deliverable**: Can write sequences using ASCII or Unicode syntax
**Unblocks**: Solutions 40-43 (pattern matching on sequences)

---

### Phase 15: Underscore in Identifiers ✅ COMPLETED
**Timeline**: 2-3 hours actual
**Goal**: Support multi-word identifiers with underscores
**Priority**: CRITICAL (needed for Solutions 40-52)
**Status**: ✅ Completed (571 tests passing)

**Problem**: Previously, `_` was a subscript operator, so `cumulative_total` tokenized as three separate tokens: `cumulative`, `_`, `total`. Solutions 40-52 use multi-word identifiers extensively.

**Solution**: Include underscore in identifiers at lexer level, handle subscript rendering in LaTeX generation.

**Added**:
- Underscore now part of identifier characters in lexer
- Removed UNDERSCORE token type
- Smart underscore rendering in LaTeX generator

**LaTeX Rendering Heuristics**:
1. **No underscore**: `x` → `x`
2. **Simple subscript** (single char after `_`): `a_i` → `a_i`, `x_0` → `x_0`
3. **Multi-char subscript** (2-3 chars after `_`): `a_max` → `a_{max}`
4. **Multi-word identifier** (long words or multiple `_`): `cumulative_total` → `\mathit{cumulative\_total}`

**Heuristic**: If any part is > 3 chars or multiple underscores, treat as multi-word identifier and use `\mathit{}` with escaped underscores.

**Input Format**:
```
x_i                    # Simple subscript
a_max                  # Multi-char subscript
cumulative_total       # Multi-word identifier
not_yet_viewed         # Multi-word identifier (3 underscores)
```

**LaTeX Output**:
```latex
$x_i$
$a_{max}$
$\mathit{cumulative\_total}$
$\mathit{not\_yet\_viewed}$
```

**Backward Compatibility**:
- Solutions 1-39 still work (subscripts like `a_i`, `x_n`)
- Simple subscripts render identically
- Only affects multi-char suffixes and long identifiers

**Implementation Details**:
- Lexer: Changed `_scan_identifier()` to include underscore in character loop
- Lexer: Removed underscore token generation
- LaTeX: Added smart heuristic in `_generate_identifier()`
- Updated 6 tests to reflect new behavior

**Test Coverage**: Existing tests + verification tests
- Simple subscripts: `a_i`, `x_0`
- Multi-char subscripts: `a_max`
- Multi-word identifiers: `cumulative_total`, `not_yet_viewed`
- In equations: `cumulative_total = x + y`

**Deliverable**: Can use multi-word identifiers in Z specifications
**Unblocks**: Solutions 40-52 (all use multi-word identifiers)

---

### Phase 16: Conditional Expressions (if/then/else) ✅ COMPLETED
**Timeline**: 3-4 hours actual
**Goal**: Support conditional expressions in mathematical notation
**Priority**: CRITICAL (needed for Solutions 40-52)
**Status**: ✅ Completed (590 tests passing)

**Problem**: Conditional expressions (`if condition then expr1 else expr2`) are commonly used in recursive function definitions and specifications, especially for pattern matching on sequences and free types.

**Solution**: Add conditional expression syntax with proper precedence and LaTeX rendering.

**Added**:
- Conditional expression tokens: IF, THEN, ELSE, OTHERWISE
- Conditional AST node with condition, then_expr, else_expr fields
- Conditional parsing at expression entry level (before iff) for low precedence
- Nested conditional support in then/else branches
- MINUS token for arithmetic subtraction/negation
- Unary minus operator (Phase 16 dependency)

**Precedence**: Conditionals bind very loosely (lower than iff), allowing arbitrary expressions in condition but allowing conditionals in then/else branches for nesting.

**Parsing Strategy**:
- Condition: parsed with `_parse_iff()` (no quantifiers/lambdas/conditionals)
- Then/else branches: parsed with `_parse_expr()` (allows nested conditionals)
- Conditionals can appear as operands in arithmetic expressions

**Input Format**:
```
if x > 0 then x else -x
if s = <> then 0 else head s
if x > 0 then 1 else if x < 0 then -1 else 0  # Nested
abs(x) = if x > 0 then x else -x
max(x, y) = if x > y then x else y
y + if x > 0 then 1 else 0  # As operand
```

**LaTeX Output**:
```latex
$(\text{if } x > 0 \text{ then } x \text{ else } -x)$
$(\text{if } s = \langle \rangle \text{ then } 0 \text{ else } \head s)$
$(\text{if } x > 0 \text{ then } 1 \text{ else } (\text{if } x < 0 \text{ then } -1 \text{ else } 0))$
$abs(x) = (\text{if } x > 0 \text{ then } x \text{ else } -x)$
$max(x, y) = (\text{if } x > y \text{ then } x \text{ else } y)$
$y + (\text{if } x > 0 \text{ then } 1 \text{ else } 0)$
```

**MINUS Token Implementation**:
- Added MINUS to TokenType enum
- Lexer recognizes standalone `-` (separate from multi-char operators like `->`, `-->>`)
- Parser handles MINUS as both unary prefix (negation) and binary infix (subtraction)
- LaTeX generator maps `-` to `-` for both contexts (no space for unary)

**Implementation Details**:
- Lexer: Added IF/THEN/ELSE/OTHERWISE keyword recognition
- Lexer: Added standalone minus token handling
- Parser: Added `_parse_conditional()` method at expression entry point
- Parser: Added MINUS to unary operators and additive operators
- Parser: Added IF and MINUS to `_is_operand_start()` for lookahead
- LaTeX: Inline rendering with `\text{}` keywords, wrapped in parentheses
- LaTeX: Unary minus renders without space (`-x` not `- x`)

**Test Coverage**: 19 tests in test_phase16.py covering:
- Simple conditionals (if x > 0 then x else -x)
- Conditionals with comparisons (if s = <> then 0 else 1)
- Nested conditionals (in then branch, in else branch)
- Conditionals in binary operations (y + if x > 0 then 1 else 0)
- LaTeX generation with proper formatting
- Precedence and associativity
- Integration tests (abs, max, sign functions)

**Example Use Cases**:
```
# Absolute value
abs(x) = if x > 0 then x else -x

# Maximum of two values
max(x, y) = if x > y then x else y

# Sign function (nested conditionals)
sign(x) = if x > 0 then 1 else if x < 0 then -1 else 0

# Recursive sequence function
f(s) = if s = <> then 0 else head s + f(tail s)

# Pattern matching alternative
total(<>) = 0
total(<x> ^ s) = x + total(s)
# Equivalent to: total(seq) = if seq = <> then 0 else ...
```

**Deliverable**: Can express conditional logic in mathematical specifications
**Unblocks**: Solutions 40-52 (conditional expressions in recursive functions)

---

### Phase 17: Recursive Free Types with Constructor Parameters ✅ COMPLETED
**Timeline**: 4-5 hours actual
**Goal**: Support recursive free type definitions with parameterized constructors
**Priority**: CRITICAL (needed for Solutions 44-47)
**Status**: ✅ Completed (773 tests passing)

**Problem**: Basic free types (Phase 4) only supported simple constructor names without parameters. Z notation requires recursive free types with parameterized constructors like `Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩`.

**Solution**: Enhance free type syntax to support constructor parameters enclosed in angle brackets.

**Added**:
- FreeBranch AST node with name and optional parameters field
- Modified FreeType to use `list[FreeBranch]` instead of `list[str]`
- Parser support for angle bracket parameters `⟨Type⟩` or `<Type>`
- LaTeX generation with `\ldata` and `\rdata` for parameterized constructors
- Support for complex parameter types (cross products, function applications)
- Backward compatibility with simple free types (Phase 4)

**Input Format**:
```
given N

Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩

List ::= nil | cons⟨N × List⟩
```

**LaTeX Output**:
```latex
\begin{zed}[N]\end{zed}

\begin{zed}Tree ::= stalk | leaf \ldata N \rdata | branch \ldata Tree \cross Tree \rdata\end{zed}

\begin{zed}List ::= nil | cons \ldata N \cross List \rdata\end{zed}
```

**Implementation Details**:
- **FreeBranch**: New dataclass with `name: str` and `parameters: Expr | None`
- **FreeType**: Changed `branches: list[str]` to `branches: list[FreeBranch]`
- **Parser**: Added `_parse_free_type()` enhancement to parse `⟨...⟩` parameters
  - Uses `_parse_cross()` for parameter expressions (handles identifiers and cross products)
  - Special case for empty parameters `⟨⟩` creates empty SequenceLiteral
  - Supports both Unicode `⟨⟩` and ASCII `<>` angle brackets
- **LaTeX**: Updated `_generate_free_type()` to render `\ldata` and `\rdata` for parameterized branches
  - Added `"×": r"\cross"` to BINARY_OPS dictionary
  - Added `"×": 8` to PRECEDENCE dictionary
- **Token reuse**: Leveraged LANGLE/RANGLE tokens from Phase 12

**Key Design Decisions**:
1. **Parameter type**: `Expr | None` allows arbitrary type expressions (identifiers, cross products, function applications)
2. **Parser method**: Use `_parse_cross()` instead of `_parse_comparison()` to correctly handle cross products without consuming too much
3. **LaTeX wrapping**: Entire free type in `\begin{zed}...\end{zed}` environment
4. **Backward compatibility**: Simple branches (no parameters) render without `\ldata`/`\rdata`

**Test Coverage**: 18 tests in test_phase17_free_types.py covering:
- Simple branches (no parameters)
- Single parameter constructors (leaf⟨N⟩)
- Multi-parameter constructors (branch⟨Tree × Tree⟩)
- Mixed branches (combination of simple and parameterized)
- ASCII angle brackets alternative (`<>`)
- Complex parameter types (`cons⟨N × seq(N)⟩`)
- LaTeX generation for all cases
- End-to-end integration tests (Tree, List definitions)
- Error handling (empty branches, unclosed brackets)
- Backward compatibility with Phase 4 simple free types

**Verified Against**:
- Solutions 44-47 test file successfully generated PDF
- Tree definition renders correctly: `Tree ::= stalk | leaf ⟨N⟩ | branch⟨Tree × Tree⟩`

**Deliverable**: Can process recursive free type definitions with constructor parameters
**Unblocks**: Solutions 44-47 (free types and structural induction)

---

### Phase 12: Sequences
**Timeline**: 6-8 hours
**Goal**: Sequence types and sequence operators
**Priority**: MEDIUM (needed for Solutions 37-39)

**Add**:
- Sequence types: `seq X`, `seq1 X` (non-empty), `iseq X` (injective)
- Sequence literals: `<>`, `<a, b, c>`
- Concatenation: `s ^ t`
- Head/tail/last/front: `head s`, `tail s`, `last s`, `front s`
- Sequence filtering: `s |` A` (filter by set)
- Reverse: `rev s`
- Extraction: `s(i)` (element at position)
- Distributed concatenation: `cat/s`
- Squash: `squash R`

**Input Format**:
```
<a>
<a, b, c, d> ^ <a, b> = {1 |-> a, 2 |-> b, 3 |-> c, 4 |-> d, 5 |-> a, 6 |-> b}
tail <a, b, c, d> = <b, c, d>
front <a, b, c, d> = <a, b, c>
ran <a, b, a, d> = {a, b, d}

f : Place -> P Place
forall p : Place | f p = {q : Place | p |-> q in ran trains}

{p : Place | exists1 x : dom trains | (trains x).2 = p}
```

**LaTeX Output**:
```latex
$\langle a \rangle$
$\langle a, b, c, d \rangle \cat \langle a, b \rangle = \{1 \mapsto a, 2 \mapsto b, \ldots\}$
$\tail \langle a, b, c, d \rangle = \langle b, c, d \rangle$
$\front \langle a, b, c, d \rangle = \langle a, b, c \rangle$
$\ran \langle a, b, a, d \rangle = \{a, b, d\}$
```

**Test Coverage**: Solutions 37-39
**Deliverable**: Can process sequence specifications and operations

---

### Phase 13: Schemas and State Machines
**Timeline**: 10-12 hours
**Goal**: Z schemas, state, and operations
**Priority**: MEDIUM-LOW (needed for Solutions 40-43)

**Add**:
- Schema boxes with declarations and predicates
- Schema references and inclusion
- Schema decoration: `S'`, `S?`, `S!`
- Delta notation: `Delta S` (before/after state)
- Xi notation: `Xi S` (no state change)
- Schema composition: `S1 ; S2`, `S1 and S2`, `S1 or S2`
- Schema projection: `S \ (x, y)`
- Preconditions: `pre S`
- Schema quantification

**Input Format**:
```
schema State
  hd : seq(Title x Length x Viewed)
where
  cumulative_total hd <= 12000
  forall p : ran hd | p.2 <= 360
end

schema AddSong
  Delta State
  song? : SongId
where
  song? notin ran hd
  hd' = hd ^ <song?>
end
```

**LaTeX Output**:
```latex
\begin{schema}{State}
hd : \seq(Title \cross Length \cross Viewed)
\where
cumulative\_total~hd \leq 12000 \\
\forall p : \ran hd \bullet p.2 \leq 360
\end{schema}

\begin{schema}{AddSong}
\Delta State \\
song? : SongId
\where
song? \notin \ran hd \\
hd' = hd \cat \langle song? \rangle
\end{schema}
```

**Test Coverage**: Solutions 40-43
**Deliverable**: Can process state-based specifications with schemas

---

### Phase 14: Free Types and Induction
**Timeline**: 8-10 hours
**Goal**: Recursive types and inductive proofs
**Priority**: LOW (needed for Solutions 44-47)

**Add**:
- Free type definitions: `Type ::= constructor1 | constructor2 << Type >>`
- Recursive constructors with parameters
- Pattern matching in function definitions
- Inductive proof structure (base case + inductive step)
- Recursive function definitions over free types
- Proof by structural induction

**Input Format**:
```
Tree ::= stalk | leaf << N >> | branch << Tree x Tree >>

count : Tree -> N
count stalk = 0
forall n : N | count (leaf n) = 1
forall t1, t2 : Tree | count (branch (t1, t2)) = count t1 + count t2

PROOF (by induction on t : Tree):
Base case (stalk):
  # (flatten stalk)
  = # <> [flatten]
  = 0 [#]
  = count stalk [count]

Inductive step (branch):
  # (flatten branch (t1, t2))
  = # (flatten t1 ^ flatten t2) [flatten]
  = # flatten t1 + # flatten t2 [# is distributive]
  = count t1 + count t2 [induction hypothesis]
  = count branch (t1, t2) [count]
```

**LaTeX Output**:
```latex
\begin{zed}
Tree ::= stalk | leaf \ldata \nat \rdata | branch \ldata Tree \cross Tree \rdata
\end{zed}

\begin{axdef}
count : Tree \fun \nat
\also
count~stalk = 0 \\
\forall n : \nat \bullet count~(leaf~n) = 1 \\
\forall t_{1}, t_{2} : Tree \bullet count~(branch~(t_{1}, t_{2})) = count~t_{1} + count~t_{2}
\end{axdef}

[Proof rendered with proper structure...]
```

**Test Coverage**: Solutions 44-47
**Deliverable**: Can process recursive types and inductive proofs

---

## Updated Timeline Summary

### Completed (Phase 0-17) ✅
- **Total time invested**: ~70-90 hours
- **Coverage**: 69.2% of course material (36/52 solutions fully working, Solutions 44-47 verified)
- **Status**: ✅ Phase 17 complete - recursive free types with constructor parameters implemented
- **Phases complete**: 0, 1, 2, 3, 4, 5, 5b, 6, 7, 8, 9, 10a, 10b, 11a, 11b, 11c, 11d, 11.5, 11.6, 11.7, 11.8, 11.9, 14, 15, 16, 17
- **Test coverage**: 773 tests passing

### Remaining (Phases 12-13) for 100% Coverage
- **Phase 12**: Sequences (full operators) (4-6h) → 75% coverage (Solutions 37-39)
- **Phase 13**: Schemas/State Machines (10-12h) → 83% coverage (Solutions 40-43)
- **Phase 18**: Pattern matching (4-6h) → 90% coverage (Solutions 44-47 complete)
- **Supplementary**: Advanced features (4-6h) → 100% coverage (Solutions 48-52)

**Total remaining**: 22-30 hours of focused work

### Grand Total
- **Current progress**: 69.2% complete (36/52 solutions fully working)
- **Solutions 44-47**: Verified working (recursive free types)
- **Estimated total for 100%**: 92-120 hours
- **Next milestone**: Phase 12 (full sequence operators) OR Phase 18 (pattern matching)

### Advantages of Phased Approach
1. ✅ **Early utility**: Phase 1 usable for truth table problems immediately
2. ✅ **Risk reduction**: Each phase validates the architecture
3. ✅ **Isolated testing**: Clear test scope per phase
4. ✅ **Regular milestones**: Working software at each phase
5. ✅ **User feedback**: Real usage drives next phase priorities
6. ✅ **Easier debugging**: Smaller scope to diagnose issues

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

## Design Decisions

### 1. Package Choice: fuzz vs zed-* ✅ RESOLVED

**Decision**: Support both, default to **zed-***

**Rationale**:
- **zed-* advantages**:
  - No custom fonts (uses Computer Modern + AMS)
  - Works on any LaTeX installation immediately
  - Instructor uses it (submission compatibility)
  - Built-in proof tree support (`\infer`, `\assume`, `\discharge`)
  - Modular design (load only what's needed)

- **fuzz advantages**:
  - Historical standard for Z notation
  - Single package simplicity
  - Already working in txt2tex_v3.py
  - May have typechecker integration

**Implementation**: Both packages use identical macro names (`\land`, `\forall`, `\begin{schema}`, etc.), so generated LaTeX is 99% compatible. Only difference is preamble and proof tree syntax.

**Configuration**:
```python
Options(use_fuzz=False)  # Default: zed-*
Options(use_fuzz=True)   # Use fuzz package
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

**Output LaTeX** (with default zed-* packages):
```latex
\documentclass{article}
\usepackage{zed-cm}
\usepackage{zed-maths}
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

**Note**: Output with `use_fuzz=True` is identical except first three `\usepackage` lines become `\usepackage{fuzz}`.
