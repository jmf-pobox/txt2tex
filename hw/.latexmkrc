# LaTeX Workshop / latexmk configuration for hw/
# Ensures local .sty and .mf files are found
# Configured for natbib citations (requires multiple passes)

# Add current directory to search paths
$ENV{'TEXINPUTS'} = '.:' . ($ENV{'TEXINPUTS'} || '');
$ENV{'MFINPUTS'} = '.:' . ($ENV{'MFINPUTS'} || '');

# Use pdflatex
$pdf_mode = 1;
$postscript_mode = $dvi_mode = 0;

# Don't stop on errors (match our build script behavior)
$pdflatex = 'pdflatex -interaction=nonstopmode -file-line-error %O %S';

# Run pdflatex multiple times for natbib citations
# With manual \begin{thebibliography}, citations need 3+ passes to resolve
$max_repeat = 5;
