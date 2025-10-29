# txt2tex Quality Assurance Checklist

## Bug Reporting

Found a new bug during QA? Follow the bug reporting workflow:

1. **Create minimal test case** in `tests/bugs/bugN_name.txt`
2. **Verify bug** with `hatch run convert tests/bugs/bugN_name.txt`
3. **Create GitHub issue** at [Issues](https://github.com/USER/REPO/issues/new?template=bug_report.md)
4. **Include test case** in issue description
5. **Update STATUS.md** with issue reference

See [tests/bugs/README.md](tests/bugs/README.md) for bug test case format.

**Known Bugs**: See [STATUS.md Bug Tracking section](STATUS.md#bug-tracking) for active bugs.

---

## Success Criteria
100% correctness across all 52 solutions. All three checks must pass for each solution.

## Three Binary Checks

For each solution, verify:

1. **Input Correct (.txt)** - Is solutions.txt notation correct vs reference? TEXT: blocks only for prose?
2. **Notation Correct (PDF)** - All mathematical symbols rendered correctly?
   - **Automated check**: Run `./qa_check.sh examples/solutions.pdf` first to detect rendering issues
   - Verify no garbled characters (¿, ¡, —), no text "forall"/"emptyset", no runon text
   - See [docs/QA_CHECKS.md](QA_CHECKS.md) for details on automated checks
3. **Formatting Correct (PDF)** - Line breaks, spacing, alignment match reference?

## Solution Assessment

### Solution 1 (Propositional Logic)
- [x] Input Correct
- [x] Notation Correct
- [ ] Formatting Correct - Missing spaces around parentheses, part labels on separate lines
- **User Decision**: **PASS** (approved by user)

### Solution 2 (Truth Tables)
- [x] Input Correct
- [x] Notation Correct
- [x] Formatting Correct
- **User Decision**: **PASS**

### Solution 3 (Equivalence Proofs)
- [x] Input Correct
- [x] Notation Correct
- [x] Formatting Correct
- **User Decision**: **PASS**

### Solution 4 (Non-tautologies)
- [x] Input Correct
- [x] Notation Correct
- [x] Formatting Correct
- **User Decision**: **PASS**

### Solution 5
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 6
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 7
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 8
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 9
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 10
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 11
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 12
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 13
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 14
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 15
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 16
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 17
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 18
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 19
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 20
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 21
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 22
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 23
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 24
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 25
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 26
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 27
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 28
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 29
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 30
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 31
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 32
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 33
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 34
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 35
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 36
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 37
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 38
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 39
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 40
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 41
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 42
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 43
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 44
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 45
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 46
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 47
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 48
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 49
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 50
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 51
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

### Solution 52
- [ ] Input Correct
- [ ] Notation Correct
- [ ] Formatting Correct
- **User Decision**: Pending

## Automated QA Checks

Before manual review, run automated checks:

```bash
# Generate PDF if not already done
hatch run convert examples/solutions.txt

# Run automated quality checks
./qa_check.sh examples/solutions.pdf
```

This will check for:
- Garbled characters (rendering issues)
- Text "forall" instead of ∀ symbol
- Text "emptyset" instead of ∅ symbol
- Runon text (missing spaces)
- LaTeX source issues

Fix any issues found before proceeding with manual solution-by-solution review.

**See [docs/QA_CHECKS.md](QA_CHECKS.md) for detailed documentation of the QA script.**

## README.md Verification
- [ ] All Phase 0-24 examples correct
- [ ] All implemented features documented
- [ ] Installation instructions correct
- [ ] Workflow commands accurate
- **User Decision**: Pending

## Notes

- Generated PDF: 204.5KB, 33 pages vs Reference PDF: 230.4KB, 29 pages
- Page count difference indicates potential systematic formatting issues
