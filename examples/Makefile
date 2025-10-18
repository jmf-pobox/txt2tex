# Makefile for txt2tex examples
#
# Usage:
#   make          # Build all PDFs
#   make all      # Build all PDFs
#   make phase8   # Build phase8.pdf
#   make clean    # Remove all generated files
#   make -j       # Build in parallel

SHELL := /bin/bash

# Find all .txt files in this directory (excluding test_ and solutions_ files)
TXT_FILES := $(filter-out test_% solutions_%, $(wildcard *.txt))

# Generate corresponding .tex and .pdf targets
TEX_FILES := $(TXT_FILES:.txt=.tex)
PDF_FILES := $(TXT_FILES:.txt=.pdf)

# Default target: build all PDFs
.PHONY: all
all: $(PDF_FILES)

# Pattern rule: .txt -> .pdf (via txt2pdf.sh script with --fuzz option)
%.pdf: %.txt ../txt2pdf.sh
	@echo "Building $@..."
	@../txt2pdf.sh $< > /dev/null 2>&1 || (echo "Error building $@"; exit 1)

# Individual phase targets for convenience
.PHONY: phase0 phase1 phase2 phase3 phase4 phase5 phase6 phase7 phase8 phase9 phase10a phase10b phase11a
phase0: phase0.pdf
phase1: phase1.pdf
phase2: phase2.pdf
phase3: phase3.pdf
phase4: phase4.pdf
phase5: phase5.pdf
phase6: phase6.pdf
phase7: phase7.pdf
phase8: phase8.pdf
phase9: phase9.pdf
phase10a: phase10a.pdf
phase10b: phase10b.pdf
phase11a: phase11a.pdf

# Clean auxiliary files (keep LaTeX source and PDF)
.PHONY: clean
clean:
	@echo "Cleaning auxiliary files..."
	@rm -f *.aux *.log *.pdflatex.log *.fuzz.log
	@rm -f *.tfm *.pk *.gf *.600pk *.600gf
	@echo "Done."

# Deep clean: remove everything except source .txt files
.PHONY: distclean
distclean: clean
	@echo "Removing all generated files..."
	@rm -f $(TEX_FILES) $(PDF_FILES)
	@rm -f *.sty *.mf
	@echo "Done."

# List all available targets
.PHONY: list
list:
	@echo "Available targets:"
	@echo "  all          - Build all PDFs (default)"
	@echo "  phase0-11a   - Build specific phase PDF"
	@echo "  clean        - Remove all generated files"
	@echo "  list         - Show this help"
	@echo ""
	@echo "Available .txt files:"
	@for f in $(TXT_FILES); do echo "  $$f"; done

# Help target
.PHONY: help
help: list
