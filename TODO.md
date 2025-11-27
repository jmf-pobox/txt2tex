# TODO: Linting Standards Tightening

**Status: PLANNING**

## Overview

Phased rollout of additional linting rules to tighten coding standards. Each group is assessed independently, with user approval required before keeping new rules.

---

## Group 1: Critical Safety & Bug Prevention (Highest Value)

**Priority: CRITICAL** - These catch real bugs, security issues, and leftover debug code.

### Rules to Enable

| Rule | Name | Description |
|------|------|-------------|
| **S** | flake8-bandit | Security vulnerability detection |
| **BLE** | flake8-blind-except | Prevents bare `except:` clauses |
| **T10** | flake8-debugger | Catches leftover `breakpoint()`, `pdb` |
| **T20** | flake8-print | Catches leftover `print()` statements |
| **A** | flake8-builtins | Prevents shadowing builtins (`list = []`) |

### Workflow

- [x] **Step 1.1**: Enable rules in `pyproject.toml`
- [x] **Step 1.2**: Run `hatch run lint` and count violations per rule
- [x] **Step 1.3**: Present violation counts to user
- [x] **Step 1.4**: User decides: keep all / keep some / disable
- [x] **Step 1.5**: Fix violations for kept rules OR add to ignore list
- [x] **Step 1.6**: Commit changes

### Status: COMPLETE ✅

### Results

| Rule | Violations | Resolution |
|------|------------|------------|
| S | 4024 (all S101 in tests) | Keep, ignore S101 in tests |
| BLE | 2 | Keep, fixed with pytest.raises |
| T10 | 0 | Keep (free win) |
| T20 | 27 | Keep, per-file ignores for cli.py/tests, removed lexer debug prints |
| A | 0 | Keep (free win) |

---

## Group 2: Dead Code & Code Quality

**Priority: HIGH** - Improves maintainability by catching unused/dead code.

### Rules to Enable

| Rule | Name | Description |
|------|------|-------------|
| **ARG** | flake8-unused-arguments | Catches unused function parameters |
| **ERA** | flake8-eradicate | Detects commented-out code |
| **PIE** | flake8-pie | Unnecessary `pass`, duplicate dict keys, etc. |
| **RET** | flake8-return | Return statement best practices |
| **RSE** | flake8-raise | Raise statement best practices |

### Workflow

- [ ] **Step 2.1**: Enable rules in `pyproject.toml`
- [ ] **Step 2.2**: Run `hatch run lint` and count violations per rule
- [ ] **Step 2.3**: Present violation counts to user
- [ ] **Step 2.4**: User decides: keep all / keep some / disable
- [ ] **Step 2.5**: Fix violations for kept rules OR add to ignore list
- [ ] **Step 2.6**: Commit changes

### Status: NOT STARTED

---

## Group 3: Type Safety Enhancements

**Priority: MEDIUM-HIGH** - Tightens type checking across all tools.

### mypy Additions

| Option | Effect |
|--------|--------|
| `strict_equality = true` | Warns comparing incompatible types |
| `disallow_any_generics = true` | Forbids unparameterized generics |
| `enable_error_code = ["ignore-without-code"]` | Requires error codes on `# type: ignore` |

### Pyright Tightening

| Setting | From | To |
|---------|------|-----|
| `reportUnknownMemberType` | `information` | `warning` |
| `reportUnknownVariableType` | `information` | `warning` |
| `reportUnknownArgumentType` | (default) | `warning` |

### Workflow

- [ ] **Step 3.1**: Enable mypy additions
- [ ] **Step 3.2**: Run `hatch run type` and count new errors
- [ ] **Step 3.3**: Enable pyright tightening
- [ ] **Step 3.4**: Run `hatch run type-pyright` and count new warnings
- [ ] **Step 3.5**: Present all counts to user
- [ ] **Step 3.6**: User decides: keep all / keep some / disable
- [ ] **Step 3.7**: Fix violations for kept options OR revert
- [ ] **Step 3.8**: Commit changes

### Status: NOT STARTED

---

## Group 4: Performance & Modern Python

**Priority: MEDIUM** - Performance improvements and modernization.

### Rules to Enable

| Rule | Name | Description |
|------|------|-------------|
| **PERF** | perflint | Performance anti-patterns |
| **PTH** | flake8-use-pathlib | Prefer `pathlib` over `os.path` |
| **ISC** | flake8-implicit-str-concat | Implicit string concatenation bugs |
| **FBT** | flake8-boolean-trap | Boolean argument anti-patterns |
| **C90** | mccabe | Cyclomatic complexity (max 10) |

### Workflow

- [ ] **Step 4.1**: Enable rules in `pyproject.toml`
- [ ] **Step 4.2**: Run `hatch run lint` and count violations per rule
- [ ] **Step 4.3**: Present violation counts to user
- [ ] **Step 4.4**: User decides: keep all / keep some / disable
- [ ] **Step 4.5**: Fix violations for kept rules OR add to ignore list
- [ ] **Step 4.6**: Commit changes

### Status: NOT STARTED

---

## Group 5: Testing & Advanced Linting (Lowest Priority)

**Priority: LOW** - Nice-to-have improvements for testing and exception handling.

### Rules to Enable

| Rule | Name | Description |
|------|------|-------------|
| **PT** | flake8-pytest-style | Pytest best practices |
| **SLF** | flake8-self | Private member access violations |
| **TRY** | tryceratops | Exception handling best practices |
| **PL** | pylint | Additional pylint rules (subset) |

### Workflow

- [ ] **Step 5.1**: Enable rules in `pyproject.toml`
- [ ] **Step 5.2**: Run `hatch run lint` and count violations per rule
- [ ] **Step 5.3**: Present violation counts to user
- [ ] **Step 5.4**: User decides: keep all / keep some / disable
- [ ] **Step 5.5**: Fix violations for kept rules OR add to ignore list
- [ ] **Step 5.6**: Commit changes

### Status: NOT STARTED

---

## Execution Notes

### Assessment Command Template

```bash
# For ruff rules, count violations per rule:
hatch run ruff check . --select=RULE 2>/dev/null | grep -c "^"

# For mypy, count total errors:
hatch run mypy src/txt2tex tests 2>/dev/null | grep -c "error:"

# For pyright, count warnings:
hatch run pyright 2>/dev/null | grep -c "warning"
```

### Decision Criteria (Suggested)

| Violations | Recommendation |
|------------|----------------|
| 0 | Keep (free improvement) |
| 1-10 | Keep and fix |
| 11-50 | User decides: fix vs disable |
| 50+ | Likely disable or defer |

### Rollback Strategy

If a rule causes too many issues:
1. Add to `ignore = [...]` in `pyproject.toml`
2. Document why in a comment
3. Optionally revisit later

---

## Progress Summary

| Group | Status | Rules Kept | Rules Disabled |
|-------|--------|------------|----------------|
| 1 - Safety | ✅ Complete | S, BLE, T10, T20, A | None |
| 2 - Dead Code | Not Started | - | - |
| 3 - Type Safety | Not Started | - | - |
| 4 - Performance | Not Started | - | - |
| 5 - Testing | Not Started | - | - |

---

## Previous Completed Work

### Fuzz-Mode Refactoring (COMPLETE) ✅

Reduced `self.use_fuzz` usages from 31 to 20 by centralizing common patterns into 7 helper methods.

**Completed Phases:**
- Phase 1: Separator helpers (`_get_bullet_separator`, `_get_colon_separator`, `_get_mid_separator`)
- Phase 2: Type name helper (`_get_type_latex`)
- Phase 3: Closure operator helper (`_get_closure_operator_latex`)
- Phase 4: Identifier formatting helper (`_format_multiword_identifier`)
- Phase 5: Binary operator helper (`_map_binary_operator`)
- Phase 6: Documentation updated
