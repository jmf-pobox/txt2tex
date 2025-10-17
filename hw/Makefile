# Makefile for txt2tex homework solutions
#
# Usage:
#   make             # Build solutions.pdf
#   make all         # Build all PDFs
#   make clean       # Remove all generated files
#   make -j          # Build in parallel

SHELL := /bin/bash

# Find all .txt files in this directory
TXT_FILES := $(wildcard *.txt)

# Generate corresponding .tex and .pdf targets
TEX_FILES := $(TXT_FILES:.txt=.tex)
PDF_FILES := $(TXT_FILES:.txt=.pdf)

# Default target: build solutions.pdf (the main file)
.DEFAULT_GOAL := solutions.pdf

# Build all PDFs
.PHONY: all
all: $(PDF_FILES)

# Pattern rule: .txt -> .pdf (via txt2pdf.sh script with --fuzz option)
%.pdf: %.txt ../txt2pdf.sh
	@echo "Building $@..."
	@../txt2pdf.sh $< --fuzz > /dev/null 2>&1 || (echo "Error building $@"; exit 1)

# Main solutions file
.PHONY: solutions
solutions: solutions.pdf

# Clean generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	@rm -f $(TEX_FILES) $(PDF_FILES)
	@rm -f *.aux *.log *.pdflatex.log *.fuzz.log
	@rm -f *.tfm *.pk *.gf *.600pk *.600gf
	@echo "Done."

# List all available targets
.PHONY: list
list:
	@echo "Available targets:"
	@echo "  (default)    - Build solutions.pdf"
	@echo "  all          - Build all PDFs"
	@echo "  solutions    - Build solutions.pdf"
	@echo "  clean        - Remove all generated files"
	@echo "  list         - Show this help"
	@echo ""
	@echo "Available .txt files:"
	@for f in $(TXT_FILES); do echo "  $$f"; done

# Help target
.PHONY: help
help: list
