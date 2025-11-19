# Text Processing and Bibliography

This directory contains examples of text block types and bibliography management in txt2tex.

## Topics Covered

- `TEXT:` blocks - Smart text with automatic formula detection
- `PURETEXT:` blocks - Raw text with LaTeX escaping
- `LATEX:` blocks - Raw LaTeX passthrough
- `PAGEBREAK:` - Page break insertion
- Bibliography management with citations
- Harvard-style citations with natbib

## Text Block Types

### TEXT: - Smart Detection
```
TEXT: The set { x : N | x > 0 } contains positive integers.
TEXT: We know that forall x : N | x >= 0 is true.
```
**Features**:
- Operators converted: `=>` → $\Rightarrow$, `<=>` → $\Leftrightarrow$
- Formulas auto-detected: `{ x : N | x > 0 }` → math mode
- Sequence literals: `<a, b, c>` → $\langle a, b, c \rangle$
- Citations: `[cite key]` → (Author, Year)

### PURETEXT: - Escaping Only
```
PURETEXT: Author's name, "quoted text", & symbols.
```
**Features**:
- Escapes LaTeX special characters: `&`, `%`, `$`, `#`, etc.
- NO formula detection
- NO operator conversion
- Perfect for bibliography entries

### LATEX: - Raw Passthrough
```
LATEX: \begin{center}\textit{Custom formatting}\end{center}
LATEX: \vspace{1cm}
```
**Features**:
- NO escaping - raw LaTeX
- Perfect for custom commands, tikz, environments

### PAGEBREAK:
```
PAGEBREAK:
```
Generates `\newpage` for page breaks.

## Bibliography Management

### Using .bib File (Recommended)
```
BIBLIOGRAPHY: references.bib
BIBLIOGRAPHY_STYLE: plainnat
```

### Citations in TEXT Blocks
```
TEXT: The proof technique follows [cite simpson25a].
TEXT: See [cite spivey92 p. 42] for details.
```
Renders as: (Simpson, 2025a), (Spivey, 1992, p. 42)

### Manual Bibliography (Alternative)
Use LATEX blocks with `\begin{thebibliography}` for custom formatting.

## Examples in This Directory

Browse the `.txt` files to see:
- Smart formula detection in TEXT blocks
- PURETEXT for special characters
- LATEX passthrough usage
- Complete bibliography workflow

## See Also

- **docs/USER_GUIDE.md** - Section "Text Blocks"
- **Previous**: 10_schemas/
- **Next**: 12_advanced/
