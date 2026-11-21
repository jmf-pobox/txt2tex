# IDE Setup for txt2tex

## VSCode / Cursor LaTeX Workshop Configuration

### Overview

The project uses natbib for Harvard-style citations, which requires **two pdflatex passes**:

1. **First pass**: Generates .aux file with citation information
2. **Second pass**: Reads .aux file and inserts correct citations

### Configuration Files

txt2tex does not ship an editor configuration. The `.vscode/` directory is
git-ignored, so create your own `.vscode/settings.json` in the folder you edit
in. This setup runs the fuzz type checker first, then latexmk (which repeats
pdflatex until citations resolve):

```json
{
    "latex-workshop.latex.tools": [
        {
            "name": "fuzz",
            "command": "fuzz",
            "args": ["-t", "%DOCFILE_EXT%"]
        },
        {
            "name": "latexmk",
            "command": "latexmk",
            "args": [
                "-synctex=1",
                "-interaction=nonstopmode",
                "-file-line-error",
                "-pdf",
                "-outdir=%OUTDIR%",
                "%DOC%"
            ],
            "env": {
                "TEXINPUTS": ".:%DIR%:TXT2TEX_LATEX_DIR//:",
                "MFINPUTS": ".:%DIR%:TXT2TEX_LATEX_DIR//:"
            }
        }
    ],
    "latex-workshop.latex.recipes": [
        { "name": "fuzz -> latexmk", "tools": ["fuzz", "latexmk"] },
        { "name": "latexmk", "tools": ["latexmk"] }
    ],
    "latex-workshop.latex.recipe.default": "fuzz -> latexmk"
}
```

- `fuzz -> latexmk` (default) type-checks with fuzz, then builds the PDF.
- `latexmk` builds the PDF without fuzz. Use it for quick iteration.
- `%DOCFILE_EXT%` is the LaTeX Workshop placeholder for the file name with its
  extension, so fuzz gets `myfile.tex`.
- `TEXINPUTS` and `MFINPUTS` tell LaTeX where to find `fuzz.sty` and the
  `oxsz*.mf` fonts. They ship inside the installed package, in its `latex/`
  folder. `txt2tex --tex-only` does not leave copies beside your `.tex` file.
  Print the folder with:

  ```bash
  python -c "import txt2tex, pathlib; print(pathlib.Path(txt2tex.__file__).parent / 'latex')"
  ```

  Replace `TXT2TEX_LATEX_DIR` in the settings above with the path it prints.
  Use the `python` that has txt2tex installed (in a clone, `uv run python`).

#### .latexmkrc

latexmk reads a `.latexmkrc` file from the directory you build in. The one used
for the examples is
[examples/infrastructure/.latexmkrc](../../examples/infrastructure/.latexmkrc):

- Adds the current directory to `TEXINPUTS` and `MFINPUTS`
- Builds with `pdflatex -interaction=nonstopmode`

Copy it next to your own `.tex` files if you build without the txt2tex CLI.
latexmk repeats pdflatex up to 5 times by default, which is enough for
citations to resolve.

### Why Two Passes Are Required

**With natbib**, the first pdflatex pass produces warnings like:

```text
Package natbib Warning: Citation `spivey92' on page 1 undefined.
Package natbib Warning: Citation(s) may have changed.
(natbib)                Rerun to get citations correct.
```

These are **expected** and resolved automatically on the second pass.

**First pass**:

- Reads `\citep{spivey92}` commands
- Writes citation info to `.aux` file
- Shows warnings about undefined citations

**Second pass**:

- Reads `.aux` file with citation info
- Replaces `\citep{spivey92}` with `(Spivey, 1992)`
- No warnings

### Build Methods

All build methods handle double compilation correctly:

#### 1. LaTeX Workshop (IDE)

When you save a `.tex` file, LaTeX Workshop automatically:

1. Runs fuzz type checker
2. Runs latexmk, which repeats pdflatex until citations resolve
3. Citations resolve correctly, no warnings remain

#### 2. txt2tex CLI

```bash
txt2tex examples/01_propositional_logic/basic_operators.txt
```

Uses latexmk (when available) for robust compilation. latexmk automatically handles multiple passes and bibliography processing.

#### 3. Makefile

```bash
make -C examples all
```

Uses the txt2tex CLI via the examples Makefile. This needs a clone of the
repository and [uv](https://docs.astral.sh/uv/).

### Verification

To verify citations are working:

```bash
# Check PDF has correct citations (not [?] or undefined)
pdftotext output.pdf - | grep "Spivey"

# Should show:
# (Spivey, 1992)
# (Spivey, 1992, p. 42)
# etc.
```

### Troubleshooting

#### Problem: IDE shows natbib warnings

**Symptom**:

```text
Package natbib: Citation `spivey92' on page 1 undefined.
Package natbib: Citation(s) may have changed. Rerun to get citations correct.
```

**Solution**:

1. Check `.vscode/settings.json` has `"latex-workshop.latex.recipe.default": "fuzz -> latexmk"`
2. Manually trigger rebuild: `Cmd+Shift+P` → "LaTeX Workshop: Build LaTeX Project"
3. Check that the recipe runs `latexmk` and not a single `pdflatex` pass

#### Problem: Citations show as (?)

**Cause**: Only one pdflatex pass was run

**Solution**: Build with latexmk or the txt2tex CLI, as described above

#### Problem: Fuzz type checking fails

**Symptom**: IDE doesn't complete build

**Solution**:

- Use the `latexmk` recipe (without fuzz) for rapid iteration
- Fix fuzz errors, then switch back to `fuzz -> latexmk`

### Best Practices

1. **Development**: Use the `fuzz -> latexmk` recipe (default)
2. **Quick iteration**: Temporarily switch to the `latexmk` recipe
3. **Final build**: Always use `txt2tex file.txt`
4. **Verify**: Check PDF output with `pdftotext` to confirm citations rendered

### References

- **Example latexmk settings**: [examples/infrastructure/.latexmkrc](../../examples/infrastructure/.latexmkrc)
- **Examples Makefile**: [examples/Makefile](../../examples/Makefile)
- **Citation syntax**: [USER_GUIDE.md](USER_GUIDE.md)
