# Bug Fixtures

Minimal `.txt` inputs for defects that were fixed, for behaviour with a documented
workaround, and for edge cases worth keeping. There are 32 fixtures.

Open bugs are tracked in [GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues).
A fixture is added when a bug is filed or fixed.

## Index

| Category | Count | Meaning |
|----------|-------|---------|
| Limitation | 3 | Expected behavior with a documented workaround |
| Error-expected | 1 | Exits non-zero by design |
| Regression | 21 | Fixed defects; each fixture must keep generating |
| Feature | 7 | Edge cases of working features |

### Limitations

| File | Behavior | Workaround |
|------|----------|------------|
| `bug1_prose_period.txt` | Default mode parses math, not prose | Use `TEXT:` blocks for prose with inline math |
| `bug3_compound_id.txt`, `bug3_test_simple.txt` | txt2tex emits valid LaTeX (`R^+`); the fuzz type-checker rejects it | Use the `--zed` flag to skip fuzz |

### Error-expected

| File | Behavior |
|------|----------|
| `bug7e_text_dollar_backslash.txt` | `$...$` takes whiteboard notation only. Raw LaTeX such as `\Leftrightarrow` is rejected with a pointer to the `LATEX:` block. |

### Regressions

| File | Tests |
|------|-------|
| `bug2_multiple_pipes.txt` | Multiple pipes in TEXT blocks |
| `bug4_proof_label_typography.txt` | PROOF rule labels such as `[false-intro]` and `[=> elim]` render with tight hyphens. Test: `tests/test_bug4_proof_label.py` |
| `bug5_o9_emits_semi_not_comp.txt` | `o9` emits `\comp` inside Z paragraphs and `\semi` in display math and prose |
| `bug7_text_block_math_heuristic.txt` | TEXT prose: `^`, colons, operator keywords and backslashes stay literal; only `$...$` is math |
| `bug7f_text_colon_auto_math.txt` | Bare colons in TEXT prose are punctuation |
| `bug8_multiline_abbrev_fuzz.txt` | Multi-line set comprehensions in Z paragraphs use `\\` breaks, not `\begin{array}`. Test: `tests/test_10_schemas/test_zed_blocks.py` |
| `regression_in_operator_basic.txt` | Basic `y elem T` |
| `regression_in_operator_simple.txt` | Simple membership |
| `regression_in_operator_with_comparison.txt` | `elem` with bullet separator |
| `regression_in_operator_multiple_same.txt` | Multiple `elem`, same variable |
| `regression_in_operator_multiple_nested.txt` | Multiple `elem`, different variables |
| `regression_in_operator_before_bullet.txt` | `elem` before the bullet separator |
| `regression_in_notin_operators_combined.txt` | Combined `elem` and `notin` |
| `regression_in_operator_patterns.txt` | Various `elem` patterns |
| `regression_bullet_separator_basic.txt` | Basic bullet separator |
| `regression_bullet_separator_with_notin.txt` | Bullet separator with `notin` |
| `regression_bullet_separator_notin_paren.txt` | Parenthesized bullet separator with `notin` |
| `regression_text_comma_after_parens.txt` | Comma after parentheses in TEXT |
| `regression_text_logical_operators.txt` | Logical operators in TEXT |
| `regression_subset_operator.txt` | `subset` operator |
| `regression_notin_operator.txt` | `notin` operator |

The `elem`/`notin`-before-bullet fixtures are guarded by
`tests/test_bullet_vs_projection.py`.

### Features

| File | Tests |
|------|-------|
| `feature_semicolon_separator.txt` | Semicolon as declaration separator |
| `feature_justification_caret_operator.txt` | `^` in justifications |
| `feature_justification_empty_sequence.txt` | Empty sequence in justifications |
| `feature_justification_nonempty_sequence.txt` | Non-empty sequence in justifications |
| `feature_justification_space_preservation.txt` | Spacing in justifications |
| `feature_justification_word_identifiers.txt` | Word identifiers in justifications |
| `feature_bag_syntax_in_free_types.txt` | Bag syntax in free types |

## Check all fixtures

```bash
for f in tests/bugs/*.txt; do
  echo -n "$(basename $f): "
  uv run txt2tex "$f" --tex-only >/dev/null 2>&1 && echo "PASS" || echo "NON-ZERO"
done
```

The three limitation fixtures and `bug7e_text_dollar_backslash.txt` may print
`NON-ZERO`. That is expected.

## References

- [USER_GUIDE.md](../../docs/guides/USER_GUIDE.md) - documented syntax
- [GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues) - open bugs
