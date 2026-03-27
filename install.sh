#!/bin/sh
# Install txt2tex — whiteboard notation to LaTeX/PDF converter.
# Usage: curl -fsSL https://raw.githubusercontent.com/jmf-pobox/txt2tex/main/install.sh | sh
#
# Installs txt2tex via uv (or pip), checks for LaTeX dependencies,
# and provides guidance for optional tools (fuzz, latexmk, tex-fmt).
set -eu

# --- Colors (disabled when not a terminal) ---
if [ -t 1 ]; then
  BOLD='\033[1m' GREEN='\033[32m' YELLOW='\033[33m' RED='\033[31m' NC='\033[0m'
else
  BOLD='' GREEN='' YELLOW='' RED='' NC=''
fi

info() { printf '%b▶%b %s\n' "$BOLD" "$NC" "$1"; }
ok()   { printf '  %b✓%b %s\n' "$GREEN" "$NC" "$1"; }
warn() { printf '  %b!%b %s\n' "$YELLOW" "$NC" "$1"; }
fail() { printf '  %b✗%b %s\n' "$RED" "$NC" "$1"; exit 1; }

# --- Step 1: Python ---

info "Checking Python..."

PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PY_VERSION=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$("$cmd" -c 'import sys; print(sys.version_info.major)')
    PY_MINOR=$("$cmd" -c 'import sys; print(sys.version_info.minor)')
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 12 ]; then
      PYTHON="$cmd"
      ok "Python $PY_VERSION found ($cmd)"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  fail "Python 3.12+ not found. Install from https://www.python.org/downloads/"
fi

# --- Step 2: Install txt2tex ---

info "Installing txt2tex..."

if command -v uv >/dev/null 2>&1; then
  ok "uv found"
  uv tool install txt2tex 2>/dev/null && ok "txt2tex installed via uv" || {
    uv tool install --upgrade txt2tex 2>/dev/null && ok "txt2tex upgraded via uv"
  }
elif command -v pipx >/dev/null 2>&1; then
  ok "pipx found"
  pipx install txt2tex 2>/dev/null && ok "txt2tex installed via pipx" || {
    pipx upgrade txt2tex 2>/dev/null && ok "txt2tex upgraded via pipx"
  }
else
  warn "Neither uv nor pipx found — using pip"
  "$PYTHON" -m pip install --user txt2tex && ok "txt2tex installed via pip"
fi

if command -v txt2tex >/dev/null 2>&1; then
  ok "txt2tex command available: $(txt2tex --help 2>&1 | head -1)"
else
  warn "txt2tex installed but not on PATH"
  printf '  You may need to add ~/.local/bin to your PATH:\n'
  printf '    export PATH="$HOME/.local/bin:$PATH"\n'
fi

# --- Step 3: LaTeX distribution ---

info "Checking LaTeX distribution..."

TEX_OK=1

if command -v pdflatex >/dev/null 2>&1; then
  ok "pdflatex found"
else
  warn "pdflatex not found — PDF compilation will not work"
  TEX_OK=0
fi

if command -v latexmk >/dev/null 2>&1; then
  ok "latexmk found (recommended for bibliography handling)"
else
  warn "latexmk not found — bibliography/citation processing may be incomplete"
fi

# Check required LaTeX packages (only if pdflatex available)
if [ "$TEX_OK" -eq 1 ]; then
  MISSING_PKGS=""
  for pkg in adjustbox natbib geometry amsfonts hyperref; do
    TEST_DOC="\\documentclass{article}\\usepackage{$pkg}\\begin{document}test\\end{document}"
    TMPDIR=$(mktemp -d)
    printf '%s' "$TEST_DOC" > "$TMPDIR/test.tex"
    if pdflatex -interaction=batchmode -halt-on-error -output-directory="$TMPDIR" "$TMPDIR/test.tex" >/dev/null 2>&1; then
      ok "LaTeX package: $pkg"
    else
      warn "LaTeX package missing: $pkg"
      MISSING_PKGS="$MISSING_PKGS $pkg"
    fi
    rm -rf "$TMPDIR"
  done

  if [ -n "$MISSING_PKGS" ]; then
    printf '\n'
    warn "Missing LaTeX packages:$MISSING_PKGS"
    printf '  Install texlive-latex-extra to get these packages:\n'
    printf '    macOS:  brew install --cask mactex (includes everything)\n'
    printf '    Ubuntu: sudo apt-get install texlive-latex-extra\n'
    printf '    Fedora: sudo dnf install texlive-collection-latexextra\n'
  fi
fi

if [ "$TEX_OK" -eq 0 ]; then
  printf '\n'
  info "Install a LaTeX distribution for PDF output:"
  printf '  macOS:  brew install --cask mactex\n'
  printf '  Ubuntu: sudo apt-get install texlive-latex-extra latexmk\n'
  printf '  Fedora: sudo dnf install texlive-scheme-medium texlive-collection-latexextra\n'
  printf '  Other:  https://tug.org/texlive/\n'
  printf '\n'
  info "Or use --tex-only to generate LaTeX without PDF compilation."
fi

# --- Step 4: Optional tools ---

info "Checking optional tools..."

if command -v fuzz >/dev/null 2>&1; then
  ok "fuzz typechecker found (Z notation type checking available)"
else
  warn "fuzz not found — Z notation type checking disabled"
  printf '  Install from: https://github.com/Spivoxity/fuzz\n'
  printf '    git clone https://github.com/Spivoxity/fuzz.git\n'
  printf '    cd fuzz && ./configure && make && sudo make install\n'
fi

if command -v tex-fmt >/dev/null 2>&1; then
  ok "tex-fmt found (--format flag available)"
else
  warn "tex-fmt not found — --format flag will be unavailable"
  printf '  Install: cargo install tex-fmt\n'
fi

# --- Done ---

printf '\n%b%btxt2tex is ready!%b\n\n' "$GREEN" "$BOLD" "$NC"

if [ "$TEX_OK" -eq 1 ]; then
  printf 'Quick start:\n'
  printf '  echo "p land q" > test.txt\n'
  printf '  txt2tex test.txt              # generates test.tex and test.pdf\n'
  printf '  txt2tex test.txt --tex-only   # generates test.tex only\n'
else
  printf 'Quick start (LaTeX-only mode):\n'
  printf '  echo "p land q" > test.txt\n'
  printf '  txt2tex test.txt --tex-only   # generates test.tex\n'
fi
printf '\n'
printf 'Verify installation:  txt2tex --check-env\n'
printf 'Full documentation:   https://github.com/jmf-pobox/txt2tex\n\n'
