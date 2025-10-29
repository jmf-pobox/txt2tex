# Documentation Organization and Validation Plan

## Goal

Reorganize and validate all markdown documentation to ensure:
1. Proper organization (docs/ vs root)
2. Accuracy of all claims
3. No broken cross-references
4. Consistency across documents
5. Minimal duplication (DRY principle)

---

## Current State Analysis

### Root-Level Markdown Files

| File | Current Purpose | Should Move? | Reason |
|------|----------------|--------------|--------|
| `CLAUDE.md` | Dev context, workflows | ❌ Stay | Development reference, accessed frequently |
| `README.md` | Project overview, quick start | ❌ Stay | Entry point, GitHub displays this first |
| `DESIGN.md` | Architecture, design decisions | ✅ Move | Technical reference, belongs in docs/ |
| `STATUS.md` | Implementation status, phases | ✅ Move | Status tracking, belongs in docs/ |
| `USER-GUIDE.md` | Syntax reference | ✅ Move | User documentation, belongs in docs/ |
| `PROOF_SYNTAX.md` | Proof tree syntax | ✅ Move | Specialized reference, belongs in docs/ |
| `QA_PLAN.md` | QA checklist, procedures | ✅ Move | Process documentation, belongs in docs/ |
| `QA_CHECKS.md` | QA script documentation | ✅ Move | Process documentation, belongs in docs/ |

### Docs Directory Structure

**Current:**
```
docs/
├── archive/          # Old plans (keep)
├── fuzz/            # Fuzz manual (keep)
├── FUZZ_FEATURE_GAPS.md
├── FUZZ_VS_STD_LATEX.md
├── IDE_SETUP.md
└── QUANTIFIER_PARENTHESIZATION_PLAN.md  # Should archive or delete
```

**Target:**
```
docs/
├── archive/          # Historical docs
│   ├── QUANTIFIER_PARENTHESIZATION_PLAN.md (move here)
│   └── [existing archive files]
├── fuzz/            # Fuzz manual reference
├── DESIGN.md        # Architecture (moved from root)
├── STATUS.md        # Implementation status (moved from root)
├── USER-GUIDE.md    # Syntax reference (moved from root)
├── PROOF_SYNTAX.md  # Proof syntax (moved from root)
├── QA_PLAN.md       # QA process (moved from root)
├── QA_CHECKS.md     # QA checks (moved from root)
├── FUZZ_FEATURE_GAPS.md
├── FUZZ_VS_STD_LATEX.md
└── IDE_SETUP.md
```

---

## Validation Tasks

### Task 1: Content Accuracy Validation

#### 1.1 STATUS.md Validation

**Checks:**
- [ ] Phase numbers match actual implementation phases
- [ ] Solution coverage statistics accurate (51/52 = 98.1%)
- [ ] Feature lists match actual code capabilities
- [ ] Bug tracking table accurate (Bug #3 status)
- [ ] Test counts match actual test suite (run `hatch run test` to verify)
- [ ] Phase descriptions match DESIGN.md phase documentation
- [ ] Last updated date reflects recent changes

**Methods:**
- **Primary**: Run test suite and verify all documented features have passing tests
  ```bash
  hatch run test -v  # Verify all tests pass
  hatch run test --collect-only  # Count total tests
  ```
- **Secondary**: Check test directory structure matches claimed organization
- **Tertiary**: Compare with `src/txt2tex/parser.py`, `ast_nodes.py` for feature claims
- Verify solution counts from `hw/solutions.txt` or `examples/solutions.txt`

#### 1.2 DESIGN.md Validation

**Checks:**
- [ ] Phase descriptions match STATUS.md
- [ ] AST node descriptions match actual `ast_nodes.py` definitions
- [ ] Precedence table matches parser implementation
- [ ] Operator bindings match parser `_parse_*` methods
- [ ] Component descriptions match actual code structure
- [ ] Implementation plan phases match completed work
- [ ] Examples match USER-GUIDE.md syntax

**Methods:**
- **Primary**: Verify phase test files exist and pass for each documented phase
  ```bash
  # Check phase-specific tests
  pytest tests/ -k "phase" -v
  # Verify parser precedence via test examples
  pytest tests/test_01_propositional_logic/test_operators.py -v
  ```
- **Secondary**: Cross-reference with `src/txt2tex/parser.py` for precedence
- Verify AST nodes against `src/txt2tex/ast_nodes.py`
- Compare phase descriptions with STATUS.md

#### 1.3 USER-GUIDE.md Validation

**Checks:**
- [ ] All syntax examples generate correct LaTeX (verify with actual conversion)
- [ ] Syntax descriptions match parser behavior
- [ ] Examples compile successfully
- [ ] Operator precedence examples accurate
- [ ] Feature coverage matches STATUS.md feature list
- [ ] Cross-references to other docs are correct
- [ ] No deprecated syntax examples

**Methods:**
- **Primary**: Extract examples from USER-GUIDE.md and verify tests exist/pass
  ```bash
  # For each documented syntax example:
  # 1. Find corresponding test
  # 2. Verify test passes
  # 3. Compare example syntax with test input
  pytest tests/ -k "example_feature" -v
  ```
- **Secondary**: Generate LaTeX for major examples and verify output
  ```bash
  # Create test files from USER-GUIDE.md examples
  hatch run convert examples/test_from_user_guide.txt
  ```
- Compare feature list with STATUS.md implementation status
- Verify examples match actual test cases

#### 1.4 PROOF_SYNTAX.md Validation

**Checks:**
- [ ] Syntax examples match actual parser implementation
- [ ] Proof tree examples render correctly
- [ ] Assumption/label handling matches code
- [ ] Indentation rules match parser expectations
- [ ] Cross-references to USER-GUIDE.md accurate

**Methods:**
- **Primary**: Verify proof tree tests exist and pass
  ```bash
  pytest tests/test_04_proof_trees/ -v
  # Verify each PROOF_SYNTAX.md example has corresponding test
  ```
- **Secondary**: Test proof syntax examples with actual parser
- Verify LaTeX output renders correctly in PDF (via test-generated PDFs)

#### 1.5 QA_PLAN.md and QA_CHECKS.md Validation

**Checks:**
- [ ] QA checklist matches current solution count (52)
- [ ] Bug reporting workflow references correct locations
- [ ] QA script (`qa_check.sh`) still exists and works
- [ ] Check descriptions match actual script behavior
- [ ] Solution assessment table complete and accurate

**Methods:**
- **Primary**: Verify solution tests exist and match QA checklist
  ```bash
  # Check if solutions are tested
  pytest tests/ -k "solution" --collect-only
  # Compare with QA_PLAN.md checklist
  ```
- **Secondary**: Verify `qa_check.sh` exists and runs
- Test script with sample files
- Compare checklist with actual solution status from tests

#### 1.6 CLAUDE.md Validation

**Checks:**
- [ ] File location references accurate (sem/ directory structure)
- [ ] Workflow commands still valid (`hatch run convert`, etc.)
- [ ] Documentation file references updated after reorganization
- [ ] Quality gate commands accurate
- [ ] Bug reporting workflow references correct paths

**Methods:**
- Verify all file paths exist
- Test workflow commands
- Check documentation links after reorganization

---

### Task 2: Cross-Reference Validation

#### 2.1 Link Inventory

**Create link map:**
- Find all `[text](file.md)` and `[text](docs/file.md)` references
- Catalog which files reference which other files
- Identify broken links (missing files, wrong paths)

**Files to check for links:**
- `README.md` (references multiple docs)
- `CLAUDE.md` (references STATUS.md, DESIGN.md, USER-GUIDE.md, etc.)
- `docs/DESIGN.md` (after move)
- `docs/STATUS.md` (after move)
- `docs/USER-GUIDE.md` (after move)
- `docs/PROOF_SYNTAX.md` (after move)
- `docs/QA_PLAN.md` (after move)
- `docs/FUZZ_FEATURE_GAPS.md`
- `docs/FUZZ_VS_STD_LATEX.md`
- `docs/IDE_SETUP.md`
- `tests/README.md`
- `examples/README.md`

#### 2.2 Update All Cross-References

After moving files, update:
- [ ] All `README.md` links to moved files
- [ ] All `CLAUDE.md` links to moved files
- [ ] All inter-document links (STATUS→DESIGN, etc.)
- [ ] All test README links
- [ ] All example README links

---

### Task 3: Consistency Checks

#### 3.1 Feature Lists Consistency

**Verify alignment:**
- [ ] STATUS.md feature list matches DESIGN.md coverage
- [ ] USER-GUIDE.md features match STATUS.md implementation status
- [ ] FUZZ_FEATURE_GAPS.md missing features don't overlap with implemented features
- [ ] Test coverage claims match actual test directory structure

#### 3.2 Statistics Consistency

**Verify alignment:**
- [ ] Test counts (STATUS.md, README.md, tests/README.md)
- [ ] Solution counts (STATUS.md, QA_PLAN.md)
- [ ] Phase numbers (STATUS.md, DESIGN.md)
- [ ] Feature counts (STATUS.md, DESIGN.md)

#### 3.3 Date Consistency

**Verify:**
- [ ] Last updated dates reflect recent changes
- [ ] Dates are consistent across related sections
- [ ] Recent phase dates match implementation timeline

---

### Task 4: Duplication Removal (DRY)

#### 4.1 Identify Duplication

**Check for duplicate content:**
- [ ] Feature lists duplicated across STATUS.md, DESIGN.md, USER-GUIDE.md
- [ ] Syntax examples duplicated
- [ ] Implementation status duplicated
- [ ] Test coverage information duplicated

#### 4.2 Consolidate

**Strategy:**
- Each fact should live in ONE primary location
- Other documents should reference, not duplicate
- Use cross-references for detailed information

**Examples:**
- `STATUS.md` = authoritative source for implementation status
- `DESIGN.md` = authoritative source for architecture
- `USER-GUIDE.md` = authoritative source for syntax examples
- Other docs reference these, don't duplicate

---

### Task 5: File Organization

#### 5.1 Move Files

**Action plan:**
1. Move `DESIGN.md` → `docs/DESIGN.md`
2. Move `STATUS.md` → `docs/STATUS.md`
3. Move `USER-GUIDE.md` → `docs/USER-GUIDE.md`
4. Move `PROOF_SYNTAX.md` → `docs/PROOF_SYNTAX.md`
5. Move `QA_PLAN.md` → `docs/QA_PLAN.md`
6. Move `QA_CHECKS.md` → `docs/QA_CHECKS.md`
7. Move `docs/QUANTIFIER_PARENTHESIZATION_PLAN.md` → `docs/archive/`

#### 5.2 Update All References

**After each move:**
- Update README.md "Project Documentation" section
- Update CLAUDE.md "Key Documentation Files" section
- Update all cross-references in moved files
- Update all cross-references in other files
- Update tests/README.md references
- Update examples/README.md references

---

## Implementation Plan

### Phase 1: Validation (Before Moving)

1. **Test-Based Content Validation** (Primary Method)
   - **Run full test suite**: `hatch run test -v`
   - **Map tests to documented features**: For each feature in STATUS.md, verify test exists and passes
   - **Verify test counts**: Compare documented test counts with actual counts
   - **Validate syntax examples**: Extract USER-GUIDE.md examples, find/test corresponding tests
   - **Check solution coverage**: Verify solution tests align with STATUS.md coverage claims
   - **Validate phase implementations**: Check phase test files match DESIGN.md phase descriptions

2. **Link Audit**
   - Catalog all markdown links
   - Identify broken links
   - Create link map

3. **Consistency Check**
   - Compare feature lists (use test coverage as source of truth)
   - Compare statistics (use actual test counts)
   - Compare dates

4. **Duplication Analysis**
   - Identify duplicate content
   - Plan consolidation

### Phase 2: File Movement

1. **Move files one at a time**
   - Design.md → docs/DESIGN.md
   - STATUS.md → docs/STATUS.md
   - USER-GUIDE.md → docs/USER-GUIDE.md
   - PROOF_SYNTAX.md → docs/PROOF_SYNTAX.md
   - QA_PLAN.md → docs/QA_PLAN.md
   - QA_CHECKS.md → docs/QA_CHECKS.md
   - QUANTIFIER_PARENTHESIZATION_PLAN.md → docs/archive/

2. **After each move:**
   - Update all references immediately
   - Verify links work
   - Test documentation still accessible

### Phase 3: Reference Updates

1. **Update README.md**
   - Fix "Project Documentation" section paths
   - Update any other references

2. **Update CLAUDE.md**
   - Fix "Key Documentation Files" section
   - Update workflow references
   - Update file location examples

3. **Update Internal Links**
   - Fix links in all moved files
   - Fix links in other documentation
   - Fix links in test/examples READMEs

4. **Verify GitHub Links**
   - Ensure GitHub will render links correctly
   - Test relative paths work from root and docs/

### Phase 4: Accuracy Verification

1. **Re-run Test-Based Validation**
   - Run full test suite: `hatch run test -v`
   - Verify all documented features still have passing tests
   - Check test counts match documentation
   - Verify no tests broke due to link/documentation changes

2. **Test Documentation Examples**
   - Run documented commands
   - Test example files compile
   - Extract examples from docs, verify tests exist
   - Verify workflow still works

3. **Final Review**
   - Read through all documentation
   - Check for broken formatting
   - Verify consistency with test suite results
   - **Key check**: All documented ✅ features have passing tests

---

## Validation Methods

### Primary: Test-Based Validation (Most Important)

**Principle**: Tests are executable specifications. If a feature is documented as implemented, tests should pass. If tests don't exist or fail, documentation is incorrect.

#### 1. Test Suite as Truth Source

**Run full test suite and analyze results:**
```bash
# Run all tests with coverage
hatch run test-cov

# Collect test names organized by feature
hatch run test --collect-only

# Verify specific feature tests exist
pytest tests/ -k "feature_name" -v
```

**For each documented feature:**
- [ ] Verify test exists if documented as ✅ implemented
- [ ] Verify test does NOT exist if documented as ❌ not implemented
- [ ] Verify test passes (feature actually works)
- [ ] Compare test examples with documentation examples

#### 2. Feature Implementation Validation via Tests

**Strategy**: Map documented features to test files and verify alignment.

```bash
# Example: Validate quantifier implementation
pytest tests/test_02_predicate_logic/test_quantifiers.py -v

# Example: Validate schema syntax
pytest tests/test_06_definitions/ -v

# Example: Validate proof trees
pytest tests/test_04_proof_trees/ -v
```

**For STATUS.md feature list:**
- [ ] Each claimed feature has corresponding test
- [ ] Tests are organized as documented (lecture-based structure)
- [ ] Test counts match documented test counts
- [ ] Test coverage aligns with solution coverage claims

#### 3. Syntax Documentation Validation via Tests

**Strategy**: Extract test examples and verify they match USER-GUIDE.md documentation.

```bash
# Extract actual working examples from tests
grep -r "def test" tests/ -A 10 | grep -E "(Input|Example|txt)" 

# Test USER-GUIDE.md examples compile
# Create test file from documentation example
hatch run convert examples/test_user_guide_example.txt
```

**Validation checklist:**
- [ ] Each USER-GUIDE.md syntax example has corresponding test
- [ ] Test input matches documented syntax
- [ ] Generated LaTeX matches documented output
- [ ] No deprecated syntax in examples without warnings

#### 4. Implementation Status Verification

**Compare STATUS.md claims with test results:**

```bash
# Verify solution coverage
pytest tests/ -k "solution" --collect-only | wc -l

# Verify phase implementation by checking phase-specific tests
pytest tests/ -k "phase" -v

# Check for tests marking incomplete features
grep -r "not yet\|TODO\|FIXME\|not implemented" tests/
```

**Validation:**
- [ ] All documented implemented features have passing tests
- [ ] Features marked as "not implemented" have no tests (or skip/xfail tests)
- [ ] Partial implementations documented correctly (tests with limitations)
- [ ] Bug tracking matches failing/blocked tests

#### 5. Cross-Reference Validation

**Use tests to verify cross-document consistency:**

```bash
# Compare STATUS.md feature list with actual test coverage
# Extract features from STATUS.md
# Map to test files
# Verify alignment
```

**Validation:**
- [ ] STATUS.md features → test files exist
- [ ] DESIGN.md phase descriptions → phase test files exist
- [ ] USER-GUIDE.md examples → test examples exist
- [ ] FUZZ_FEATURE_GAPS.md gaps → tests appropriately missing

### Secondary: Automated Checks

1. **Link Validation Script**
   ```bash
   # Find all markdown links
   grep -r "\[.*\]\(.*\.md\)" . --include="*.md"
   
   # Check for broken links (after verifying file structure)
   # This could be a simple script that checks if target files exist
   ```

2. **Statistics Verification via Tests**
   ```bash
   # Count tests from actual run
   hatch run test --collect-only | grep -c "test"
   
   # Verify solution count from actual file
   grep -c "^\*\* Solution" hw/solutions.txt
   
   # Compare with STATUS.md claims
   ```

3. **Syntax Example Testing**
   ```bash
   # Extract examples from USER-GUIDE.md
   # Create test files for each
   # Run through converter
   # Verify they compile and pass tests
   ```

### Tertiary: Manual Checks

1. **Read-through** - Read each document for accuracy
2. **Cross-reference** - Verify all links work
3. **Code inspection** - Verify implementation matches tests
4. **Statistics verification** - Count actual tests/features

---

## Success Criteria

✅ **All files organized:**
- Root: Only README.md and CLAUDE.md
- Docs: All other documentation

✅ **All links work:**
- No broken markdown links
- All cross-references valid
- GitHub renders correctly

✅ **Content accurate:**
- All documented ✅ features have passing tests
- Statistics match actual test counts
- Feature lists match test coverage
- Examples in docs match test examples
- Examples compile/run correctly
- Dates reflect reality

✅ **No duplication:**
- Each fact in one primary location
- References used instead of duplication
- DRY principle maintained

✅ **Consistency:**
- Feature lists aligned
- Statistics aligned
- Dates aligned
- Terminology consistent

---

## Deliverables

1. **Reorganized Documentation Structure**
   - Files moved to appropriate locations
   - Clear organization

2. **Updated Documentation**
   - All references fixed
   - All links working
   - Content validated

3. **Validation Report**
   - List of changes made
   - Issues found and fixed
   - Verification of accuracy

4. **Documentation Index**
   - Updated README.md with correct paths
   - Clear navigation structure

---

## Timeline Estimate

- **Phase 1 (Validation)**: 2-3 hours
- **Phase 2 (File Movement)**: 1 hour
- **Phase 3 (Reference Updates)**: 2-3 hours
- **Phase 4 (Verification)**: 1-2 hours

**Total**: 6-9 hours

---

## Notes

- **Tests as source of truth**: Use passing tests to validate all documentation claims
- **Test coverage first**: If a feature has tests that pass, document as implemented. If not, document as not implemented or verify tests are missing intentionally.
- Keep README.md and CLAUDE.md in root for easy access
- Test all changes incrementally
- Verify GitHub rendering after each move
- Maintain git history (git handles renames well)
- Consider adding a docs/README.md for navigation
- **Key principle**: Documentation should reflect what tests verify works, not what code might do

