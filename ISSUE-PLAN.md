# Issue Discovery and Tracking Plan

**Purpose**: Systematic plan to identify, document, validate, and track all known bugs and limitations in txt2tex.

**Last Updated**: 2025-11-23

**Status**: Ready for execution

---

## Executive Summary

This plan provides a systematic workflow for discovering all known bugs and limitations across the txt2tex codebase. The plan is designed to be:

1. **Resumable**: Can be executed across multiple sessions without losing progress
2. **Complete**: Covers all potential sources of bug/limitation information
3. **Validated**: Each issue is verified before documentation
4. **Non-duplicative**: Cross-references existing GitHub issues

---

## Search Strategy

### Phase 1: Documentation Sources

Search all documentation for mentions of bugs, limitations, and known issues.

**Files to search** (18 files identified):

1. `docs/development/STATUS.md` - Primary bug tracking table
2. `tests/bugs/README.md` - Bug test cases documentation
3. `docs/guides/FUZZ_FEATURE_GAPS.md` - Known fuzz limitations
4. `docs/guides/FUZZ_VS_STD_LATEX.md` - Fuzz vs LaTeX differences
5. `CLAUDE.md` - Project context and known bugs
6. `README.md` - User-facing documentation
7. `docs/DESIGN.md` - Design decisions vs limitations
8. `docs/guides/USER_GUIDE.md` - Syntax limitations
9. `docs/guides/PROOF_SYNTAX.md` - Proof-specific limitations
10. `docs/development/QA_PLAN.md` - Quality issues
11. `.github/ISSUES_TO_CREATE.md` - Planned issues
12. `.github/ISSUE_TEMPLATE/bug_report.md` - Bug template
13. `examples/README.md` - Example limitations
14. `docs/tutorials/README.md` - Tutorial-noted issues
15. `docs/tutorials/00_getting_started.md` - Getting started issues
16. `docs/development/CODE_REVIEW.md` - Code review findings
17. `.claude/agents/documentation-guardian.md` - Documentation issues
18. `.claude/agents/code-quality-enforcer.md` - Quality issues

**Search terms for documentation**:
- `bug` / `Bug` / `BUG`
- `limitation` / `Limitation` / `LIMITATION`
- `known issue` / `Known issue` / `KNOWN ISSUE`
- `workaround` / `Workaround`
- `not supported` / `Not supported` / `NOT supported`
- `not implemented` / `Not implemented` / `NOT implemented`
- `blocks` / `Blocks` / `BLOCKS`
- `fails` / `Fails` / `FAILS`
- `error` / `Error` (in context)
- `❌` (X emoji - often marks unsupported features)
- `⚠️` (warning emoji - often marks partial support)

**Command to execute**:
```bash
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem

# Search all markdown files for bug/limitation mentions
grep -rn -E "(bug|limitation|known issue|workaround|not supported|not implemented|blocks|fails|❌|⚠️)" \
  --include="*.md" \
  . > /tmp/txt2tex_doc_issues.txt
```

### Phase 2: Source Code Analysis

Search Python source code for developer comments indicating issues.

**Files to search**:
- `src/txt2tex/*.py` (7 files: __init__.py, tokens.py, parser.py, cli.py, latex_gen.py, lexer.py, ast_nodes.py)

**Search terms for source code**:
- `TODO` - Tasks to be done
- `FIXME` - Known broken code
- `HACK` - Non-ideal workarounds
- `XXX` - Important notes/warnings
- `BUG` - Known bugs
- `WORKAROUND` - Temporary solutions
- `NOTE:` - Important implementation notes

**Commands to execute**:
```bash
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem

# Search source files for issue markers
grep -rn -E "(TODO|FIXME|HACK|XXX|BUG|WORKAROUND|NOTE:)" \
  --include="*.py" \
  src/txt2tex/ > /tmp/txt2tex_source_issues.txt

# Also search for comments mentioning "limitation" or "not supported"
grep -rn -E "(limitation|not supported|known issue|fails)" \
  -i --include="*.py" \
  src/txt2tex/ >> /tmp/txt2tex_source_issues.txt
```

**Result**: Currently shows NO matches (clean codebase!)

### Phase 3: Test Suite Analysis

Search test files for skip/xfail markers and "known issue" comments.

**Test directory structure**:
- `tests/test_*.py` - Main test files organized by glossary lectures
- `tests/bugs/` - Bug test cases directory
- `tests/*/test_*.py` - Subdirectory-organized tests

**Search terms for tests**:
- `@pytest.skip` - Skipped tests
- `@pytest.xfail` - Expected failures
- `pytest.mark.skip` - Skip markers
- `pytest.mark.xfail` - Expected fail markers
- `known issue` - Comments about known problems
- `# BUG` - Inline bug comments
- `# TODO` - Test todos

**Commands to execute**:
```bash
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem

# Search for skip/xfail decorators
grep -rn -E "(@pytest\.(skip|xfail)|pytest\.mark\.(skip|xfail))" \
  --include="*.py" \
  tests/ > /tmp/txt2tex_test_skips.txt

# Search for known issue comments
grep -rn -E "(known issue|# BUG|# TODO|# FIXME)" \
  -i --include="*.py" \
  tests/ > /tmp/txt2tex_test_issues.txt
```

**Result**: Currently shows NO skip/xfail markers (excellent!)

### Phase 4: Bug Test Cases

Examine all files in `tests/bugs/` directory.

**Known bug test files**:
- `bug1_prose_period.txt` - Parser fails on prose with periods
- `bug2_multiple_pipes.txt` - TEXT blocks with multiple pipes
- `bug3_compound_id.txt` - Compound identifiers with operator suffixes
- `regression_text_comma_after_parens.txt` (formerly bug4) - Comma detection (RESOLVED)
- `regression_text_logical_operators.txt` (formerly bug5) - Logical operators (RESOLVED)

**Additional test files found** (15 regression tests + 7 feature tests):

*Regression Tests (resolved bugs)*:
- `regression_in_operator_*.txt` (8 files) - IN operator disambiguation
- `regression_bullet_separator_*.txt` (3 files) - Bullet separator parsing
- `regression_subset_operator.txt` - SUBSET operator
- `regression_notin_operator.txt` - NOTIN operator
- `regression_text_*.txt` (2 files) - TEXT block operators

*Feature Tests (never bugs)*:
- `feature_justification_*.txt` (5 files) - Justification formatting edge cases
- `feature_semicolon_separator.txt` (formerly test_issue7_semicolon.txt) - Semicolon separator
- `feature_bag_syntax_in_free_types.txt` - Bag notation in free types

**Command to execute**:
```bash
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem

# List all bug test files
ls -la tests/bugs/bug*.txt tests/bugs/test_*.txt > /tmp/txt2tex_bug_files.txt

# Test each bug file to determine status
for f in tests/bugs/bug*.txt tests/bugs/test_*.txt; do
  if [ -f "$f" ]; then
    echo "=== Testing $f ===" >> /tmp/txt2tex_bug_validation.txt
    hatch run convert "$f" 2>&1 | head -20 >> /tmp/txt2tex_bug_validation.txt
    echo "" >> /tmp/txt2tex_bug_validation.txt
  fi
done
```

### Phase 5: GitHub Issues

Fetch and cross-reference existing GitHub issues.

**Current GitHub issues** (4 open):
1. Issue #13: Bug: Field Projection on Function Application in Quantifiers (labeled: bug)
2. Issue #3: Lexer: Cannot use identifiers like R+, R* (operator suffixes)
3. Issue #2: TEXT blocks: Multiple pipes in expressions close math mode incorrectly
4. Issue #1: Parser: Prose with inline math and periods causes parse errors

**Command to execute**:
```bash
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem

# Fetch all GitHub issues (open and closed)
gh issue list --repo jmf-pobox/txt2tex --limit 100 --json number,title,state,labels,body,url \
  > /tmp/txt2tex_github_issues.json

# Also fetch closed issues
gh issue list --repo jmf-pobox/txt2tex --state closed --limit 100 --json number,title,state,labels,body,url \
  > /tmp/txt2tex_github_issues_closed.json
```

---

## Checkpoint System

To enable resumable work across sessions, maintain progress checkpoints.

### Checkpoint File: `ISSUE-PROGRESS.json`

```json
{
  "last_updated": "2025-11-23T12:00:00Z",
  "phases": {
    "documentation_search": {
      "status": "completed|in_progress|not_started",
      "files_processed": ["STATUS.md", "FUZZ_FEATURE_GAPS.md", ...],
      "issues_found": 12,
      "last_file": "DESIGN.md"
    },
    "source_code_search": {
      "status": "completed|in_progress|not_started",
      "files_processed": ["lexer.py", "parser.py", ...],
      "issues_found": 0,
      "last_file": "latex_gen.py"
    },
    "test_suite_search": {
      "status": "completed|in_progress|not_started",
      "files_processed": ["test_lexer.py", ...],
      "issues_found": 0,
      "last_file": ""
    },
    "bug_test_validation": {
      "status": "completed|in_progress|not_started",
      "files_validated": ["bug1_prose_period.txt", ...],
      "active_bugs": 3,
      "resolved_bugs": 2,
      "last_file": "bug5_or_operator.txt"
    },
    "github_sync": {
      "status": "completed|in_progress|not_started",
      "last_sync": "2025-11-23T12:00:00Z",
      "open_issues": 4,
      "closed_issues": 0
    }
  },
  "issues_discovered": 15,
  "issues_validated": 10,
  "issues_documented": 8
}
```

### Creating Checkpoints

After completing each phase, update the checkpoint file:

```bash
# After Phase 1: Documentation search
echo '{"phases": {"documentation_search": {"status": "completed", ...}}}' \
  > ISSUE-PROGRESS.json

# After Phase 2: Source code search
# Update JSON with source_code_search status

# And so on...
```

### Resuming from Checkpoint

```bash
# Check current progress
cat ISSUE-PROGRESS.json | jq '.phases'

# Resume from last incomplete phase
# If documentation_search = "in_progress", continue from last_file
```

---

## Issue Validation Workflow

For each discovered issue, follow this validation process:

### Step 1: Issue Verification

**Confirm the issue exists:**

1. **For parser/runtime bugs:**
   ```bash
   # Test with minimal example
   echo "test case content" > /tmp/test_issue.txt
   hatch run convert /tmp/test_issue.txt
   # Expected: Error or incorrect output
   ```

2. **For LaTeX generation issues:**
   ```bash
   # Generate LaTeX and inspect
   hatch run cli /tmp/test_issue.txt -o /tmp/test_issue.tex
   cat /tmp/test_issue.tex  # Inspect output
   ```

3. **For fuzz validation issues:**
   ```bash
   # Test with fuzz mode
   hatch run convert /tmp/test_issue.txt --fuzz
   # Expected: Fuzz validation error
   ```

4. **For unimplemented features:**
   - Check FUZZ_FEATURE_GAPS.md for documentation
   - Verify feature is truly missing (not just undocumented)
   - Test that workaround (if any) actually works

### Step 2: Issue Classification

**Categorize the issue:**

1. **Critical Bug**
   - Causes parser crash or incorrect compilation
   - No workaround available
   - Blocks common use cases
   - Examples: Bug #1 (prose with periods)

2. **Medium Bug**
   - Causes incorrect output but has workaround
   - Blocks specific features or edge cases
   - Examples: Bug #2 (multiple pipes in TEXT), Bug #3 (compound identifiers)

3. **Low Priority Bug**
   - Minor rendering issue
   - Easy workaround available
   - Rare occurrence
   - Examples: (none currently)

4. **Known Limitation**
   - Not a bug, but documented constraint
   - Intentional design decision
   - Examples: Semicolon not used for composition (by design)

5. **Design Decision**
   - Not a bug or limitation
   - Architectural choice with rationale
   - Examples: Parser requires TEXT blocks for prose

6. **Fuzz Limitation**
   - Works in txt2tex but fails fuzz validation
   - Fuzz type checker limitation, not txt2tex bug
   - Examples: Mu operator syntax differences

7. **Resolved Issue**
   - Previously reported bug that's now fixed
   - Keep in tracking for regression testing
   - Examples: Bug #4, Bug #5

### Step 3: Workaround Documentation

**If workaround exists, document it:**

1. **Document the workaround**:
   ```markdown
   **Workaround**: Use TEXT blocks for prose with periods:
   ```txt
   TEXT: 1 in {4, 3, 2, 1} is true.
   ```
   ```

2. **Test the workaround**:
   ```bash
   # Verify workaround actually works
   echo "TEXT: 1 in {4, 3, 2, 1} is true." > /tmp/test_workaround.txt
   hatch run convert /tmp/test_workaround.txt
   # Expected: Success
   ```

3. **Document limitations of workaround**:
   - Does it fully solve the problem?
   - Are there edge cases where it fails?
   - Does it have performance implications?

### Step 4: GitHub Cross-Reference

**Check if issue already exists on GitHub:**

1. **Search existing issues**:
   ```bash
   gh issue list --repo jmf-pobox/txt2tex --search "keywords from issue"
   ```

2. **If issue exists**:
   - Note issue number (#N)
   - Verify description matches
   - Check if status is accurate (open/closed)
   - Update local tracking with GitHub URL

3. **If issue does NOT exist**:
   - Mark as "needs GitHub issue"
   - Prepare issue content (see templates below)
   - Do NOT create duplicate issues

### Step 5: Test Case Creation

**Ensure minimal test case exists:**

1. **Check tests/bugs/ directory**:
   - Does `bugN_name.txt` exist?
   - Is it truly minimal (5-10 lines)?
   - Does it reproduce the issue?

2. **If test case missing, create it**:
   ```bash
   cat > tests/bugs/bugN_name.txt << 'EOF'
   === Bug N Test: Description ===

   [minimal failing example]
   EOF
   ```

3. **Verify test case**:
   ```bash
   hatch run convert tests/bugs/bugN_name.txt
   # Should reproduce the bug
   ```

---

## Duplicate Prevention

### Before Creating GitHub Issues

**Check these sources for duplicates:**

1. **GitHub issues** (open and closed):
   ```bash
   gh issue list --repo jmf-pobox/txt2tex --state all --search "keywords"
   ```

2. **STATUS.md Bug Tracking table**:
   - Check "Issue" column for existing issue numbers
   - Check "Test Case" column for existing bug files

3. **tests/bugs/README.md**:
   - Check "Active Bugs" section
   - Check "Resolved Issues" section

4. **FUZZ_FEATURE_GAPS.md**:
   - Check if it's a documented fuzz limitation (not a bug)
   - Check "Missing Features" sections

5. **.github/ISSUES_TO_CREATE.md**:
   - Check if issue is already planned

### Duplicate Identification Logic

**An issue is a duplicate if:**

1. Same symptom (error message or incorrect output)
2. Same root cause (same component fails)
3. Same test case (reproduces same way)

**An issue is NOT a duplicate if:**

1. Different symptom even if same component
2. Different workaround required
3. One is feature request, other is bug

---

## Issue Documentation Templates

### Template: Critical Bug

```markdown
## Issue: [Short Description]

**Priority**: CRITICAL
**Component**: [lexer|parser|latex-gen|cli]
**Status**: ACTIVE
**GitHub**: [#N](url) or "needs issue"

### Description
[1-2 sentences describing the bug]

### Test Case
**File**: `tests/bugs/bugN_name.txt`

**Input**:
```txt
[minimal failing example]
```

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens - error message or incorrect output]

### Workaround
[If any] or "None available"

### Impact
- **Blocks**: [What use cases this blocks]
- **Affects**: [Who is affected]

### Validation Status
- [ ] Issue verified (reproduced)
- [ ] Test case created
- [ ] GitHub issue exists
- [ ] Documented in STATUS.md
```

### Template: Known Limitation

```markdown
## Limitation: [Short Description]

**Priority**: [LOW|MEDIUM|HIGH]
**Component**: [component]
**Status**: DOCUMENTED
**Reason**: [Design decision|Fuzz limitation|Not implemented]

### Description
[Why this limitation exists]

### Workaround
[If any]

### Future Plans
[If any] or "No plans to implement"

### Validation Status
- [ ] Limitation documented
- [ ] Workaround tested
- [ ] FUZZ_FEATURE_GAPS.md updated
```

### Template: Design Decision

```markdown
## Design Decision: [Short Description]

**Decision**: [What was decided]
**Rationale**: [Why this decision was made]
**Alternative**: [What alternatives were considered]
**Trade-offs**: [What was sacrificed]

### Documentation
- **DESIGN.md**: Section [reference]
- **USER_GUIDE.md**: Section [reference]

### Not a Bug Because
[Explain why this is intentional, not a bug]
```

---

## Progress Tracking

### Metrics to Track

1. **Discovery Progress**:
   - Files searched: N / Total
   - Issues discovered: N
   - Issues per source: (docs: N, code: N, tests: N, bugs: N)

2. **Validation Progress**:
   - Issues verified: N / Discovered
   - Test cases created: N
   - Workarounds documented: N

3. **GitHub Sync Progress**:
   - GitHub issues: Open N, Closed N
   - Issues needing GitHub: N
   - Issues with GitHub link: N

4. **Documentation Progress**:
   - Issues in ISSUES.md: N
   - Issues in STATUS.md: N
   - Issues in FUZZ_FEATURE_GAPS.md: N

### Daily Summary Format

```markdown
## Progress Report: 2025-11-23

**Session**: 1 of N
**Duration**: 2 hours
**Phase**: Documentation Search

### Completed
- [x] Searched STATUS.md (3 bugs found)
- [x] Searched FUZZ_FEATURE_GAPS.md (4 limitations found)
- [x] Searched tests/bugs/README.md (5 bugs documented)

### In Progress
- [ ] Searching DESIGN.md (50% complete)

### Discovered
- 12 issues total
- 3 critical bugs
- 4 known limitations
- 5 resolved issues

### Next Steps
- Complete DESIGN.md search
- Begin source code search phase
- Validate newly discovered issues
```

---

## Execution Workflow

### Session 1: Documentation Discovery (2-3 hours)

**Goal**: Find all issues mentioned in documentation

1. **Setup**:
   ```bash
   cd /Users/jfreeman/Coding/fuzz/txt2tex/sem
   mkdir -p /tmp/txt2tex_issue_discovery
   ```

2. **Execute searches**:
   - Run documentation grep commands
   - Manually read STATUS.md Bug Tracking section
   - Manually read FUZZ_FEATURE_GAPS.md Missing Features
   - Manually read tests/bugs/README.md

3. **Record findings**:
   - Create ISSUE-PROGRESS.json with discoveries
   - Note which files mention each issue
   - Cross-reference mentions (same issue in multiple files)

4. **Checkpoint**:
   - Mark documentation_search as "completed"
   - Count total issues discovered
   - List files processed

### Session 2: Source Code Discovery (1-2 hours)

**Goal**: Find all TODO/FIXME/HACK comments in source

1. **Execute searches**:
   - Run source code grep commands
   - Manually inspect any matches

2. **Analyze findings**:
   - Currently shows 0 matches (excellent code quality!)
   - If any found, categorize as bug/todo/note

3. **Checkpoint**:
   - Mark source_code_search as "completed"

### Session 3: Test Suite Discovery (1-2 hours)

**Goal**: Find skip/xfail markers and known issue comments

1. **Execute searches**:
   - Run test suite grep commands
   - Currently shows 0 skip/xfail markers (excellent!)

2. **Checkpoint**:
   - Mark test_suite_search as "completed"

### Session 4: Bug Test Validation (2-3 hours)

**Goal**: Test every bug file to determine current status

1. **Test each bug file**:
   ```bash
   for f in tests/bugs/bug*.txt; do
     echo "Testing $f"
     hatch run convert "$f" 2>&1 | head -20
   done
   ```

2. **Categorize results**:
   - Still fails → Active bug
   - Now works → Resolved bug
   - Unclear → Needs investigation

3. **Document findings**:
   - Update bug status in findings
   - Note which bugs are resolved but not documented

4. **Checkpoint**:
   - Mark bug_test_validation as "completed"
   - List active vs resolved bugs

### Session 5: GitHub Synchronization (1 hour)

**Goal**: Fetch all GitHub issues and cross-reference

1. **Fetch issues**:
   - Open issues (already done: 4 issues)
   - Closed issues
   - Parse JSON output

2. **Cross-reference**:
   - Match GitHub issues to discovered issues
   - Identify issues needing GitHub creation
   - Identify GitHub issues not in local tracking

3. **Checkpoint**:
   - Mark github_sync as "completed"
   - List issues needing GitHub

### Session 6: Issue Validation (3-4 hours)

**Goal**: Verify every discovered issue

1. **For each issue**:
   - Run validation workflow (Step 1-5 above)
   - Document findings
   - Update ISSUES.md

2. **Create test cases** for any issues missing them

3. **Checkpoint**:
   - Mark issues_validated count
   - List issues needing test cases

### Session 7: Documentation Update (2 hours)

**Goal**: Update ISSUES.md with all findings

1. **Populate ISSUES.md** from template structure
2. **Verify consistency** across all documentation
3. **Final review** of all findings

---

## Tools and Commands Reference

### Useful Commands

```bash
# Search all markdown files
grep -rn "pattern" --include="*.md" .

# Search Python files only
grep -rn "pattern" --include="*.py" src/

# List bug test files
ls -1 tests/bugs/bug*.txt

# Test a bug file
hatch run convert tests/bugs/bugN_name.txt

# Fetch GitHub issues
gh issue list --repo jmf-pobox/txt2tex --json number,title,state

# Search GitHub issues
gh issue list --repo jmf-pobox/txt2tex --search "keyword"

# Count test files
find tests/ -name "test_*.py" | wc -l

# Count source lines
find src/ -name "*.py" -exec wc -l {} + | tail -1
```

### Search Pattern Combinations

```bash
# Find all issue mentions in docs
grep -rn -iE "(bug|limitation|issue|not supported|blocks|fails)" \
  --include="*.md" . | less

# Find all TODOs in source
grep -rn -E "(TODO|FIXME|HACK|XXX)" --include="*.py" src/

# Find all test skips
grep -rn -E "@pytest\.(skip|xfail)" --include="*.py" tests/

# Find all bug test files
find tests/bugs/ -name "*.txt" -type f
```

---

## Success Criteria

This plan is successfully executed when:

1. **Discovery Complete**:
   - [ ] All 18 documentation files searched
   - [ ] All 7 source files searched
   - [ ] All test files searched
   - [ ] All bug test files validated
   - [ ] All GitHub issues fetched

2. **Validation Complete**:
   - [ ] Every discovered issue verified
   - [ ] Every issue categorized (bug/limitation/design)
   - [ ] Every issue has test case (if applicable)
   - [ ] Every workaround tested

3. **Documentation Complete**:
   - [ ] ISSUES.md populated with all findings
   - [ ] STATUS.md Bug Tracking table accurate
   - [ ] FUZZ_FEATURE_GAPS.md complete
   - [ ] tests/bugs/README.md up to date

4. **GitHub Sync Complete**:
   - [ ] All active bugs have GitHub issues
   - [ ] All GitHub issues cross-referenced
   - [ ] No duplicate issues created

5. **Consistency Verified**:
   - [ ] Same issue described consistently across docs
   - [ ] Issue numbers match GitHub
   - [ ] Test case files match documentation
   - [ ] Status (active/resolved) consistent everywhere

---

## Known Edge Cases

### Edge Case 1: Resolved but Undocumented Bugs

**Scenario**: Bug test file exists, bug is resolved, but not marked as resolved in docs.

**Detection**:
- Bug test file passes `hatch run convert` without error
- tests/bugs/README.md still lists as "ACTIVE"

**Resolution**:
- Update tests/bugs/README.md status to RESOLVED
- Add to "Resolved Issues" section
- Note which commit/phase resolved it

### Edge Case 2: Fuzz Limitations vs Bugs

**Scenario**: Feature works in txt2tex but fails fuzz validation.

**Detection**:
- `hatch run convert file.txt` succeeds
- `hatch run convert file.txt --fuzz` fails with fuzz error

**Classification**:
- If fuzz limitation documented in FUZZ_VS_STD_LATEX.md → "Fuzz Limitation"
- If txt2tex generates invalid LaTeX → "Bug"

**Resolution**:
- Document in FUZZ_FEATURE_GAPS.md if not already there
- NOT a bug unless txt2tex generates wrong LaTeX

### Edge Case 3: Design Decisions Perceived as Bugs

**Scenario**: User expects feature X, but it's intentionally not supported.

**Detection**:
- Feature documented as "by design" in DESIGN.md
- No plans to implement in STATUS.md roadmap

**Classification**:
- "Design Decision" not "Bug" or "Limitation"

**Resolution**:
- Document rationale in ISSUES.md
- Explain alternative approach
- Not tracked as bug

### Edge Case 4: Multiple Test Files for Same Bug

**Scenario**: Multiple bug test files reproduce the same underlying issue.

**Detection**:
- Same error message
- Same root cause (same failing component)

**Resolution**:
- Primary bug file: Most minimal example
- Secondary bug files: Note "related to Bug #N"
- All linked to same GitHub issue

---

## Appendix A: File Locations

### Key Documentation Files

```
/Users/jfreeman/Coding/fuzz/txt2tex/sem/
├── CLAUDE.md                              # Project context
├── README.md                              # User-facing docs
├── docs/
│   ├── DESIGN.md                          # Architecture
│   ├── guides/
│   │   ├── USER_GUIDE.md                  # Syntax reference
│   │   ├── PROOF_SYNTAX.md                # Proof syntax
│   │   ├── FUZZ_VS_STD_LATEX.md           # Fuzz differences
│   │   └── FUZZ_FEATURE_GAPS.md           # Missing features
│   ├── development/
│   │   ├── STATUS.md                      # Implementation status
│   │   ├── QA_PLAN.md                     # Quality assurance
│   │   └── CODE_REVIEW.md                 # Review guidelines
│   └── tutorials/
│       └── README.md                      # Tutorial index
├── tests/
│   ├── README.md                          # Test organization
│   └── bugs/
│       └── README.md                      # Bug test cases
├── .github/
│   ├── ISSUES_TO_CREATE.md                # Planned issues
│   └── ISSUE_TEMPLATE/
│       └── bug_report.md                  # Bug template
└── examples/
    └── README.md                          # Example documentation
```

### Source Code Files

```
/Users/jfreeman/Coding/fuzz/txt2tex/sem/src/txt2tex/
├── __init__.py                            # Package init
├── tokens.py                              # Token definitions
├── lexer.py                               # Lexical analysis
├── parser.py                              # Parsing logic
├── ast_nodes.py                           # AST node definitions
├── latex_gen.py                           # LaTeX generation
└── cli.py                                 # Command-line interface
```

### Test Files

```
/Users/jfreeman/Coding/fuzz/txt2tex/sem/tests/
├── test_*.py                              # Unit tests (65 files)
└── bugs/
    ├── bug1_prose_period.txt              # Bug #1
    ├── bug2_multiple_pipes.txt            # Bug #2
    ├── bug3_compound_id.txt               # Bug #3
    ├── bug4_comma_after_parens.txt        # Bug #4 (resolved)
    ├── bug5_or_operator.txt               # Bug #5 (resolved)
    └── [other bug test files]             # Additional bugs
```

---

## Appendix B: Issue Categories

### Category Definitions

1. **Critical Bug**
   - Crashes parser or runtime
   - Produces incorrect output with no workaround
   - Blocks common/essential functionality
   - Affects multiple users
   - Priority: Fix immediately

2. **Medium Bug**
   - Incorrect output but workaround exists
   - Blocks specific features or edge cases
   - Affects some users
   - Priority: Fix in next release

3. **Low Priority Bug**
   - Minor rendering inconsistency
   - Rare occurrence
   - Easy workaround
   - Affects few users
   - Priority: Fix when convenient

4. **Known Limitation**
   - Intentional constraint
   - Documented in user-facing docs
   - Alternative approach available
   - No plans to change

5. **Design Decision**
   - Architectural choice
   - Rationale documented
   - Benefits outweigh costs
   - Not a defect

6. **Fuzz Limitation**
   - Works in txt2tex
   - Fails fuzz validation
   - Fuzz package limitation
   - Not txt2tex bug

7. **Feature Request**
   - New functionality
   - Not currently supported
   - May implement in future
   - Tracked separately from bugs

---

## Appendix C: GitHub Issue Labels

### Recommended Labels

**Priority**:
- `critical` - Crashes, data loss, no workaround
- `high` - Blocks important features
- `medium` - Has workaround, affects some users
- `low` - Minor issue, rare occurrence

**Component**:
- `lexer` - Tokenization issues
- `parser` - Parsing logic issues
- `latex-gen` - LaTeX generation issues
- `cli` - Command-line interface issues

**Type**:
- `bug` - Defect in existing functionality
- `limitation` - Known constraint
- `enhancement` - New feature request
- `documentation` - Docs need update

**Status**:
- `needs-reproduction` - Can't reproduce yet
- `needs-test-case` - Need minimal example
- `has-workaround` - Temporary solution exists
- `blocked` - Waiting on external dependency

**Impact**:
- `blocks-homework` - Affects student assignments
- `blocks-examples` - Affects example files
- `blocks-solutions` - Affects reference solutions

---

## Next Steps

After completing this plan:

1. **Create ISSUES.md** with all findings (use template below)
2. **Update STATUS.md** with current bug status
3. **Update FUZZ_FEATURE_GAPS.md** with any new limitations
4. **Update tests/bugs/README.md** with accurate status
5. **Create missing GitHub issues** (if any)
6. **Create missing test cases** (if any)
7. **Document workarounds** for all active bugs
8. **Validate consistency** across all documentation

---

**End of Issue Discovery and Tracking Plan**
