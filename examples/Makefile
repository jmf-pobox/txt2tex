# Makefile for txt2tex examples
#
# Usage:
#   make                    # Build all PDFs in all subdirectories
#   make all                # Build all PDFs
#   make 01_propositional   # Build all examples in 01_propositional_logic/
#   make clean              # Remove all generated files
#   make -j                 # Build in parallel

SHELL := /bin/bash

# Find all .txt files in subdirectories (excluding reference/, infrastructure/, and future/)
TXT_FILES := $(shell find . -type f -name "*.txt" ! -path "./reference/*" ! -path "./infrastructure/*" ! -path "*/future/*")

# Generate corresponding .tex and .pdf targets
TEX_FILES := $(TXT_FILES:.txt=.tex)
PDF_FILES := $(TXT_FILES:.txt=.pdf)

# Subdirectory targets
SUBDIRS := 01_propositional_logic 02_predicate_logic 03_equality 04_proof_trees \
           05_sets 06_definitions 07_relations 08_functions 09_sequences fuzz_tests

# Reference directory (special - builds with fuzz validation)
# Note: Fuzz validation may report known errors (tuple projections, etc.) but PDF still builds
.PHONY: reference
reference:
	@echo "Building reference/compiled_solutions.pdf with fuzz validation..."
	@cd .. && hatch run convert examples/reference/compiled_solutions.txt --fuzz || true
	@if [ -f reference/compiled_solutions.pdf ]; then \
		echo "✓ Successfully built reference/compiled_solutions.pdf"; \
	else \
		echo "✗ Failed to build reference/compiled_solutions.pdf"; \
		exit 1; \
	fi

# Default target: build all PDFs
.PHONY: all
all: $(PDF_FILES)

# Pattern rule: .txt -> .pdf (using hatch run convert with fuzz type checking)
%.pdf: %.txt
	@echo "Building $@..."
	@cd .. && hatch run convert examples/$< --fuzz || (echo "Error building $@"; exit 1)

# Subdirectory targets for convenience
.PHONY: $(SUBDIRS)
$(SUBDIRS):
	@echo "Building examples in $@..."
	@for f in $@/*.txt; do \
		if [ -f "$$f" ]; then \
			cd .. && hatch run convert "examples/$$f" --fuzz || (echo "Error building $$f"; exit 1); \
		fi; \
	done

# Convenient short aliases
.PHONY: 01 02 03 04 05 06 07 08 09
01: 01_propositional_logic
02: 02_predicate_logic
03: 03_equality
04: 04_proof_trees
05: 05_sets
06: 06_definitions
07: 07_relations
08: 08_functions
09: 09_sequences

# Clean auxiliary files in all subdirectories
.PHONY: clean
clean:
	@echo "Cleaning auxiliary files..."
	@find . -type f \( -name "*.aux" -o -name "*.log" -o -name "*.synctex.gz" \
		-o -name "*.fuzz.log" -o -name "*.pdflatex.log" \
		-o -name "*.tfm" -o -name "*.pk" -o -name "*.gf" \
		-o -name "*.600pk" -o -name "*.600gf" \) -delete
	@echo "Done."

# Deep clean: remove everything except source .txt files
.PHONY: distclean
distclean: clean
	@echo "Removing all generated files..."
	@find . -type f \( -name "*.tex" -o -name "*.pdf" \) ! -path "./reference/*" -delete
	@echo "Done."

# List all available targets
.PHONY: list
list:
	@echo "Available targets:"
	@echo "  all                    - Build all PDFs (default)"
	@echo "  01-09                  - Build all examples in specific lecture directory"
	@echo "  01_propositional_logic - Build examples in 01_propositional_logic/"
	@echo "  02_predicate_logic     - Build examples in 02_predicate_logic/"
	@echo "  03_equality            - Build examples in 03_equality/"
	@echo "  04_proof_trees         - Build examples in 04_proof_trees/"
	@echo "  05_sets                - Build examples in 05_sets/"
	@echo "  06_definitions         - Build examples in 06_definitions/"
	@echo "  07_relations           - Build examples in 07_relations/"
	@echo "  08_functions           - Build examples in 08_functions/"
	@echo "  09_sequences           - Build examples in 09_sequences/"
	@echo "  clean                  - Remove auxiliary files"
	@echo "  distclean              - Remove all generated files"
	@echo "  list                   - Show this help"
	@echo ""
	@echo "Available .txt files:"
	@for f in $(TXT_FILES); do echo "  $$f"; done

# Help target
.PHONY: help
help: list
