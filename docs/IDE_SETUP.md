# IDE Setup for txt2tex

## VSCode / Cursor LaTeX Workshop Configuration

### Overview

The project uses natbib for Harvard-style citations, which requires **two pdflatex passes**:
1. **First pass**: Generates .aux file with citation information
2. **Second pass**: Reads .aux file and inserts correct citations

### Configuration Files

#### [.vscode/settings.json](../.vscode/settings.json)

**Default Recipe**: `fuzz -> pdflatex*2`
- Runs fuzz type checker
- Runs pdflatex twice to resolve citations

**Available Recipes**:
1. `fuzz -> pdflatex*2` (default) - Type check with fuzz, compile twice
2. `pdflatex*2` - Compile twice without fuzz
3. `fuzz -> pdflatex` - Single pass (faster but citations won't resolve)
4. `pdflatex` - Single pass without fuzz

**Environment Variables**:
```json
"env": {
    "TEXINPUTS": ".:%DIR%:%DIR%/latex//:",
    "MFINPUTS": ".:%DIR%:%DIR%/latex//:"
}
```

#### [hw/.latexmkrc](../hw/.latexmkrc)

Configures latexmk for natbib:
- Sets `$max_repeat = 5` to ensure citations resolve
- Adds current directory to TEXINPUTS/MFINPUTS
- Uses `pdflatex -interaction=nonstopmode`

#### [examples/infrastructure/.latexmkrc](../examples/infrastructure/.latexmkrc)

Same configuration for examples directory.

### Why Two Passes Are Required

**With natbib**, the first pdflatex pass produces warnings like:
```
Package natbib Warning: Citation `simpson25a' on page 1 undefined.
Package natbib Warning: Citation(s) may have changed.
(natbib)                Rerun to get citations correct.
```

These are **expected** and resolved automatically on the second pass.

**First pass**:
- Reads `\citep{simpson25a}` commands
- Writes citation info to `.aux` file
- Shows warnings about undefined citations

**Second pass**:
- Reads `.aux` file with citation info
- Replaces `\citep{simpson25a}` with `(Simpson, 2025a)`
- No warnings

### Build Methods

All build methods handle double compilation correctly:

#### 1. LaTeX Workshop (IDE)
When you save a `.tex` file, LaTeX Workshop automatically:
1. Runs fuzz type checker
2. Runs pdflatex (first pass)
3. Runs pdflatex (second pass)
4. Citations resolve correctly, no warnings remain

#### 2. txt2pdf.sh Script
```bash
./txt2pdf.sh hw/solutions.txt --fuzz
```

Internally runs pdflatex twice (lines 113-124):
```bash
pdflatex -interaction=nonstopmode solutions.tex  # First pass
pdflatex -interaction=nonstopmode solutions.tex  # Second pass
```

#### 3. Makefile
```bash
make -C hw solutions.pdf
```

Calls txt2pdf.sh, which handles double compilation.

```bash
make -C examples all
```

Uses `hatch run convert`, which calls txt2pdf.sh.

#### 4. Hatch Command
```bash
hatch run convert hw/solutions.txt --fuzz
```

Calls txt2pdf.sh internally.

### Verification

To verify citations are working:

```bash
# Check PDF has correct citations (not [?] or undefined)
pdftotext hw/solutions.pdf - | grep "Simpson"

# Should show:
# (Simpson, 2025a, Slide 20)
# (Simpson, 2025c, slide 41)
# etc.
```

### Troubleshooting

#### Problem: IDE shows natbib warnings

**Symptom**:
```
Package natbib: Citation `simpson25a' on page 1 undefined.
Package natbib: Citation(s) may have changed. Rerun to get citations correct.
```

**Solution**:
1. Check `.vscode/settings.json` has `"latex-workshop.latex.recipe.default": "fuzz -> pdflatex*2"`
2. Manually trigger rebuild: `Cmd+Shift+P` → "LaTeX Workshop: Build LaTeX Project"
3. Check `.latexmkrc` exists in working directory with `$max_repeat = 5`

#### Problem: Citations show as (?)

**Cause**: Only one pdflatex pass was run

**Solution**: Use one of the double-pass methods above

#### Problem: Fuzz type checking fails

**Symptom**: IDE doesn't complete build

**Solution**:
- Use `pdflatex*2` recipe (without fuzz) for rapid iteration
- Fix fuzz errors, then switch back to `fuzz -> pdflatex*2`

### Best Practices

1. **Development**: Use `fuzz -> pdflatex*2` recipe (default)
2. **Quick iteration**: Temporarily switch to `pdflatex*2` recipe
3. **Final build**: Always use `./txt2pdf.sh file.txt --fuzz` or Makefile
4. **Verify**: Check PDF output with `pdftotext` to confirm citations rendered

### References

- **txt2pdf.sh**: [txt2pdf.sh:113-124](../txt2pdf.sh#L113-L124) - Double pdflatex pass
- **LaTeX Workshop**: [.vscode/settings.json](../.vscode/settings.json) - IDE configuration
- **Makefiles**: [hw/Makefile](../hw/Makefile), [examples/Makefile](../examples/Makefile)
- **Citation syntax**: [USER-GUIDE.md:68-82](../USER-GUIDE.md#L68-L82)
