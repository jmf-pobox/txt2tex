# LaTeX Workshop / latexmk configuration
# Ensures local .sty and .mf files are found

# Add current directory to search paths
$ENV{'TEXINPUTS'} = '.:' . ($ENV{'TEXINPUTS'} || '');
$ENV{'MFINPUTS'} = '.:' . ($ENV{'MFINPUTS'} || '');

# Use pdflatex
$pdf_mode = 1;
$postscript_mode = $dvi_mode = 0;

# Don't stop on errors (match our build script behavior)
$pdflatex = 'pdflatex -interaction=nonstopmode %O %S';
