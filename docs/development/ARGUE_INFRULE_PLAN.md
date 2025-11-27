# Implementation Plan: argue, infrule, \derive, \shows Support

## Executive Summary

**DECISION MADE**: After evaluating comparison PDFs with real LaTeX examples, the approach is:

1. **EQUIV → argue migration + ARGUE: alias**:
   - Modify EQUIV: to generate argue environment (simpler, better page breaking)
   - Add ARGUE: as an alias (both syntaxes work identically)
   - Backwards compatible, helps new users learn zed2e conventions
2. **PROOF: Keep as-is**: Current \infer macro implementation works well for nested proofs
3. **Add INFRULE: syntax**: New complementary block type for horizontal-line inference rules (different paradigm from PROOF:)
4. **Add shows operator**: Standalone operator for sequent judgments (⊢)

This achieves zed2e alignment while preserving what works, adding complementary features, and supporting both familiar (EQUIV:) and standard (ARGUE:) syntax.

## Background

### Current State

**EQUIV: Blocks** (Equational Reasoning)
- Input syntax: `EQUIV:` followed by expressions and justifications
- LaTeX output: `\begin{array}{lcl}...\end{array}`
- Features: Two-column layout, supports justification annotations
- Quality: User is "happy with the style of output"

**PROOF: Trees** (Natural Deduction)
- Input syntax: `PROOF:` followed by indented tree structure
- LaTeX output: `\infer` macro from zed-proof.sty
- Features: Nested tree structure, premise/conclusion relationships
- Quality: User is "happy with the style of output"

### Target Constructs

**argue Environment** (fuzz.sty lines 222-227)
```latex
\begin{argue}
  expression_1 & justification_1 \\
  expression_2 & justification_2 \\
  ...
\end{argue}
```
- Purpose: Multi-line equational reasoning
- Features: Two-column layout, `\t1`/`\t2` indentation, better page breaking
- Similar to: EQUIV: blocks (but different LaTeX environment)

**infrule Environment** (fuzz.sty line 240)
```latex
\begin{infrule}
  premise_1 & label_1 \\
  premise_2 & label_2 \\
  \derive \\
  conclusion & label
\end{infrule}
```
- Purpose: Inference rules with horizontal line separator
- Features: Horizontal line format (premises above, conclusion below)
- Different from: PROOF: trees (horizontal line vs nested structure)

**\derive Command** (fuzz.sty lines 244-248)
```latex
\derive     % Creates horizontal rule in infrule
\derive[n]  % Horizontal rule with label number
```
- Purpose: Creates horizontal rule separating premises from conclusion
- Context: Used within infrule environment

**\shows Command** (fuzz.sty line 301)
```latex
\shows   % Renders as ⊢ (turnstile symbol)
```
- Purpose: Sequent judgment operator (⊢)
- Context: Can be used in infrule or standalone in expressions

## Comparison Results

### argue vs EQUIV (Test: /tmp/argue_comparison.pdf)

**Key findings:**
- argue cannot be wrapped in adjustbox (not allowed in LR mode)
- argue uses `\halign to\linewidth` for **automatic line-width handling** - no overflow!
- This is actually better than adjustbox: native width control, no wrapper needed
- Both produce clean two-column layout with justifications
- argue has better page breaking (`\interdisplaylinepenalty`)
- argue supports indentation (`\t1`, `\t2`) for nested reasoning

**Decision: Migrate EQUIV → argue**
- Simpler LaTeX generation (no adjustbox wrapper needed)
- Better page breaking out of the box
- Native fuzz construct (zed2e alignment)
- Auto margin handling is superior to manual adjustbox

### PROOF vs infrule (Test: /tmp/infrule_comparison.pdf)

**Key findings:**
- Different paradigms: tree structure (PROOF) vs horizontal line (infrule)
- PROOF (\infer): Excels at complex nested proofs, recursive structure
- infrule: Excels at simple formal rules, textbook presentation format
- Both have clear use cases, not redundant

**Decision: Keep PROOF, Add INFRULE**
- PROOF works well for complex proofs (no changes needed)
- Add INFRULE as complementary syntax for simple inference rules
- Users can choose appropriate tool for each use case

## Implementation Approach

### Phase 1: EQUIV → argue Migration + Add ARGUE: Alias (~4-6 hours)

**Approach**: Modify EQUIV: to generate argue environment, and add ARGUE: as an alias.

**Dual syntax support**: Both EQUIV: and ARGUE: will work identically, generating argue environment.

**Current behavior**:
```txt
EQUIV:
  p land q
  <=> q land p [commutative]
```
Generates:
```latex
\begin{center}
\adjustbox{max width=\textwidth}{%
$\displaystyle
\begin{array}{l@{\hspace{2em}}r}
p \land q \\
\Leftrightarrow q \land p & [\mbox{commutative}]
\end{array}$%
}
\end{center}
```

**New behavior** (both syntaxes work):
```txt
EQUIV:                          ARGUE:
  p land q                         p land q
  <=> q land p [commutative]       <=> q land p [commutative]
```
Both generate:
```latex
\begin{argue}
  p \land q & \\
  \Leftrightarrow q \land p & \mbox{commutative}
\end{argue}
```

**Benefits of dual syntax**:
- ✅ Existing users: Keep using EQUIV: (familiar, backwards compatible)
- ✅ New users: Can learn ARGUE: from the start (matches zed2e docs)
- ✅ Migration: Users can gradually switch EQUIV: → ARGUE: in their documents
- ✅ Documentation: Can show both forms, explain they're equivalent

**Implementation Steps**:

1. **Rename internal structures** (refactor EQUIV → ARGUE throughout codebase)
   - Rename `EquivBlock` → `ArgueBlock` in ast_nodes.py
   - Rename `EQUIV_BLOCK` → `ARGUE_BLOCK` token in lexer.py
   - Rename `parse_equiv_block()` → `parse_argue_block()` in parser.py
   - Rename `_generate_equiv_block()` → `_generate_argue_block()` in latex_gen.py
   - Update all references throughout codebase

2. **Lexer changes** (src/txt2tex/lexer.py:~250-260)
   - Recognize both "EQUIV:" and "ARGUE:" keywords
   - Both map to ARGUE_BLOCK token (EQUIV is the alias)
   - Update token type name from EQUIV_BLOCK to ARGUE_BLOCK

3. **Parser changes** (src/txt2tex/parser.py:~1450-1470)
   - Rename method to `parse_argue_block()`
   - Both EQUIV: and ARGUE: syntaxes parsed identically
   - Produce ArgueBlock AST node (renamed from EquivBlock)

4. **AST changes** (src/txt2tex/ast_nodes.py)
   - Rename class: `EquivBlock` → `ArgueBlock`
   - Keep same structure: `lines: list[tuple[Expr, str | None]]`
   - Update all type hints and references

5. **LaTeX generation** (src/txt2tex/latex_gen.py:~1530-1570)
   - Rename method: `_generate_equiv_block()` → `_generate_argue_block()`
   - Replace array generation with argue environment
   - Remove adjustbox wrapper (not needed with argue)
   - Keep same two-column format: expression & justification

6. **Testing**:
   - Update ALL existing tests to use ArgueBlock instead of EquivBlock
   - Update test expectations to expect argue LaTeX output (not array)
   - Test both EQUIV: and ARGUE: syntaxes produce identical output
   - Regenerate all .tex expected outputs in test files
   - Verify all examples compile successfully
   - Run full test suite (expect ~50-70 test updates)

7. **Documentation**:
   - Update USER_GUIDE.md: Rename section to "ARGUE: / EQUIV:", explain both work
   - Update ZED2E_ALIGNMENT_PLAN.md to mark argue as completed
   - Note: "EQUIV: is a backwards-compatible alias for ARGUE:"
   - Code comments: Explain EQUIV maps to ARGUE_BLOCK internally
   - Tutorials can use either syntax (explain they're identical)

**Migration impact**:
- ✅ Backwards compatible: EQUIV: continues to work (alias for ARGUE:)
- ✅ Clean codebase: Internal names match actual implementation (argue)
- ✅ Reduced technical debt: Code says what it does (ArgueBlock, not EquivBlock)
- ✅ Better LaTeX output: Uses argue environment (better page breaking)
- ✅ Simpler generation code: No adjustbox wrapper needed
- ✅ Educational: New users can learn ARGUE: from start, matches fuzz documentation
- ⚠️  Refactoring: Rename EquivBlock → ArgueBlock throughout codebase
- ⚠️  All test expectations need updating (mechanical change)
- ⚠️  Lexer/parser changes to recognize both keywords

**Estimated Effort**: ~5-7 hours (refactoring + test updates + dual keyword support)

---

### Phase 2: Add INFRULE: Syntax + shows Operator (~6-8 hours)

**Approach**: Add new INFRULE: block type and shows operator (PROOF: unchanged).

**New syntax**:

```txt
INFRULE:
  P [premise]
  P => Q [premise]
  ---
  Q [modus ponens]
```
Generates:
```latex
\begin{infrule}
  P & \mbox{premise} \\
  P \implies Q & \mbox{premise} \\
  \derive \\
  Q & \mbox{modus ponens}
\end{infrule}
```

**shows operator** (usable in expressions):
```txt
Gamma shows P
```
Generates: `Γ \shows P`

**Implementation Steps**:

1. **Lexer changes** (src/txt2tex/lexer.py)
   - Add INFRULE_BLOCK token (similar to PROOF_BLOCK)
   - Add SHOWS keyword token (binary operator)
   - Recognize `---` as DERIVE_LINE separator token

2. **Parser changes** (src/txt2tex/parser.py)
   - Add `parse_infrule_block()` method (similar to `parse_proof_block()`)
   - Add InfruleBlock AST node
   - Parse SHOWS as infix operator (low precedence, similar to `in`)

3. **AST nodes** (src/txt2tex/ast_nodes.py)
   ```python
   @dataclass
   class InfruleBlock:
       premises: list[tuple[Expr, str | None]]  # (premise, label)
       conclusion: tuple[Expr, str | None]       # (conclusion, label)
   ```

4. **LaTeX generation** (src/txt2tex/latex_gen.py)
   - Add `_generate_infrule_block()` method
   - Generate `\begin{infrule}...\derive...\end{infrule}`
   - Handle SHOWS operator → `\shows`

5. **Testing**:
   - Create test_infrule.py with 10-15 unit tests
   - Create test_shows_operator.py for shows in various contexts
   - Create examples/infrule_demo.txt showing PROOF vs INFRULE
   - Verify all examples compile successfully

**Migration impact**:
- ✅ New optional syntax (users can learn when needed)
- ✅ PROOF: remains unchanged (no migration needed)
- ✅ Complementary tools (different use cases)
- ⚠️  ~15-20 new tests to add

**Estimated Effort**: ~6-8 hours (new features + tests)

---

### Phase 3: Documentation + Integration (~2-3 hours)

**Documentation updates**:

1. **USER_GUIDE.md**:
   - Update EQUIV section: "EQUIV: now uses fuzz's argue environment for better page breaking"
   - Add INFRULE section: Syntax, usage, comparison with PROOF
   - Add shows operator: Usage in expressions, sequent judgments

2. **ZED2E_ALIGNMENT_PLAN.md**:
   - Mark argue environment as ✅ COMPLETED
   - Mark infrule environment as ✅ COMPLETED
   - Mark \shows command as ✅ COMPLETED

3. **Examples**:
   - Update examples/user_guide/08_equivalence_chains.txt with note about argue
   - Create examples/user_guide/infrule_simple.txt showing INFRULE usage
   - Create examples/user_guide/shows_operator.txt showing sequent judgments

**Estimated Effort**: ~2-3 hours

---

## Total Implementation Plan

### Summary

| Phase | Task | Effort | Deliverable |
|-------|------|--------|-------------|
| 1 | EQUIV → ARGUE refactor + alias | 5-7 hours | ArgueBlock internally, both EQUIV: and ARGUE: work |
| 2 | Add INFRULE + shows | 6-8 hours | New INFRULE: syntax, shows operator |
| 3 | Documentation | 2-3 hours | Complete docs and examples |
| **Total** | | **13-18 hours** | Full zed2e alignment |

### Risks and Mitigation

**Risk 1**: Test updates take longer than expected
- **Mitigation**: Use automated test regeneration where possible
- **Fallback**: Update tests incrementally, mark failing tests as TODO

**Risk 2**: argue environment has unexpected rendering issues
- **Mitigation**: Comparison PDFs already validated argue works well
- **Fallback**: Keep array generation code, add flag to switch back

**Risk 3**: INFRULE syntax conflicts with existing parser
- **Mitigation**: `---` separator is simple and unlikely to conflict
- **Fallback**: Use different separator (e.g., `====`) if needed

---

## Testing Strategy (Updated)

### Phase 1 Testing (argue migration)

**Test approach**:
1. Modify `_generate_equiv_block()` to use argue
2. Run full test suite: `hatch run test`
3. Update ALL failing EQUIV test expectations (mechanical)
4. Verify examples compile: `make` in examples/
5. Visual spot-check: Compare old vs new PDFs

**Success criteria**:
- All 1199+ tests pass
- All examples compile without errors
- Visual inspection shows no degradation

### Phase 2 Testing (INFRULE + shows)

**Test approach**:
1. Create test_infrule.py with comprehensive unit tests
2. Create test_shows_operator.py for shows in various contexts
3. Test INFRULE examples compile successfully
4. Verify shows operator works in axdef, TEXT, expressions

**Success criteria**:
- 15-20 new tests all pass
- INFRULE examples compile and render correctly
- shows operator generates correct `\shows` LaTeX

### Phase 3 Testing (Integration)

**Test approach**:
1. Run `./qa_check.sh` on all examples
2. Check for garbled characters or rendering issues
3. Verify documentation examples compile
4. Cross-reference with ZED2E_ALIGNMENT_PLAN.md

**Success criteria**:
- QA checks pass
- No new garbled characters introduced
- Documentation examples work correctly

---

## Next Steps (Updated based on decisions)

1. ✅ **Comparison PDFs created and evaluated**
2. ✅ **Decisions made**: argue migration + INFRULE addition
3. **Ready to implement Phase 1**: EQUIV → argue migration
4. **User approval**: Proceed with implementation?

**Estimated timeline**: 2-3 coding sessions (~4-6 hours each)

---

## Appendix: Comparison Files

**Created for evaluation**:
- `/tmp/argue_comparison.pdf` - Shows EQUIV (array) vs argue side-by-side
- `/tmp/infrule_comparison.pdf` - Shows PROOF (\infer) vs infrule side-by-side

**Key takeaways**:
- argue's `\halign to\linewidth` provides automatic margin handling
- argue cannot be wrapped in adjustbox (not needed!)
- PROOF and INFRULE serve different purposes (both valuable)
