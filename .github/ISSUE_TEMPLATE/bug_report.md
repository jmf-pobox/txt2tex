---
name: Bug Report
about: Report a bug in txt2tex with test case
title: "[BUG] "
labels: bug
assignees: ''
---

## Description
Brief description of the bug.

## Test Case

**Location**: `tests/bugs/bugX_name.txt` (if creating new file)

**Input**:
```txt
[Paste the minimal txt2tex input that triggers the bug]
```

## Reproduction Steps

```bash
hatch run convert tests/bugs/bugX_name.txt
```

## Expected Behavior
What should happen?

## Actual Behavior
What actually happens? (error message, incorrect output, etc.)

## Workaround
Is there a workaround? If so, describe it.

## Impact
- **Severity**: HIGH / MEDIUM / LOW
- **Blocks**: Which solutions/homework?
- **Component**: parser / lexer / latex-gen

## Environment
- txt2tex commit: [output of `git rev-parse HEAD`]
- Python version: 3.13
- OS: macOS / Linux / Windows
