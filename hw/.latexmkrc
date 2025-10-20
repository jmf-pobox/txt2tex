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
$pdflatex = 'pdflatex -interaction=nonstopmode %O %S';

# Run pdflatex twice minimum (for natbib citations)
# This eliminates "Citation may have changed" warnings
$max_repeat = 5;
