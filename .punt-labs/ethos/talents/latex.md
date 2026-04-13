# LaTeX

LaTeX engineering for mathematical and formal-methods documents. The
output target of txt2tex.

## Distributions and engines

- **TeX Live 2025** is the project's reference distribution.
- **pdflatex** for the txt2tex output (no Unicode glyphs in the source).
- **latexmk** for orchestrating multi-pass builds (TOC, bibliography,
  cross-references). The `-gg` flag forces full rebuild when state is
  questionable.
- **METAFONT** for the Oxford Z fonts (`oxsz*.mf`, `zarrow.mf`,
  `zletter.mf`, `zsymbol.mf`).

## Z-notation packages

- **fuzz.sty** — Spivey's package. Defines `\zed`, `\axdef`, `\schema`,
  `\gendef`, `\syntax`, `\argue`, `\where`, `\also`, `\defs`, `\power`,
  `\finset`, the `@` bullet separator, and the Oxford Z fonts. The
  primary target.
- **zed-csp / zed2e family** (bundled in this repo as `zed-cm.sty`,
  `zed-float.sty`, `zed-lbr.sty`, `zed-maths.sty`, `zed-proof.sty`) —
  Computer-Modern alternative; Davies/Davies–Spivey lineage. Selected
  via `--zed` flag.

## Common gotchas

- `#` needs escaping in math mode generally, *except* in Z cardinality
  `\# s` where fuzz handles it.
- `\implies` and `\iff` in fuzz predicate environments — *not*
  `\Rightarrow` and `\Leftrightarrow`.
- Spacing around schema operators (`\;`, `\,`, `\!`) is significant in
  rendered output.
- Tables and proof trees: standard LaTeX `\begin{tabular}` and
  `array` work; fuzz's `argue` environment uses raw `\halign` which
  is incompatible with `adjustbox`. The project chose array-based
  ARGUE/EQUIV for that reason (see `docs/DESIGN.md §6`).
- `pdftotext` is the verification tool of choice — round-trip the PDF
  to text to confirm what the reader will see.

## Tools

- **tex-fmt** — LaTeX formatter, optional via `--format` flag.
- **chktex** — linter; run on emitted LaTeX in CI.
- **biber + biblatex** — bibliography (when needed). `latexmk` invokes
  these automatically.

## Reference touchstones

- *The LaTeX Companion* (Mittelbach et al.) — for general LaTeX issues.
- fuzz manual `doc/fuzzman-pub.pdf` — for the Z-specific commands.
- `docs/guides/FUZZ_VS_STD_LATEX.md` (this repo) — the catalog of
  diverging behavior between fuzz and standard LaTeX.

## Working principles

- Read the LaTeX log on every change. Warnings are debt.
- Prefer the package's intended environment (`\begin{schema}{Name}`
  ... `\end{schema}`) over hand-rolled `\halign` boxes — they handle
  spacing, page breaks, and float placement.
- When fuzz rejects emitted LaTeX, the LaTeX generator is wrong, not
  fuzz. Fix the source.
- For conditional content scaling (truth tables, ARGUE blocks), wrap
  in `adjustbox{max width=\textwidth}`. Do not pre-compute widths.
