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
# Strip leading "./" prefix for proper pattern matching
TXT_FILES := $(shell find . -type f -name "*.txt" ! -path "./reference/*" ! -path "./infrastructure/*" ! -path "*/future/*" | sed 's|^\./||')

# Generate corresponding .tex and .pdf targets
TEX_FILES := $(TXT_FILES:.txt=.tex)
PDF_FILES := $(TXT_FILES:.txt=.pdf)

# Subdirectory targets
SUBDIRS := 00_getting_started 01_propositional_logic 02_predicate_logic 03_equality \
           04_proof_trees 05_sets 06_definitions 07_relations 08_functions \
           09_sequences 10_schemas 11_text_blocks 12_advanced 13_equality_chains \
           14_relational_databases 15_schema_calculus 16_multi_decl_calculus \
           17_state_machines fuzz_tests user_guide

# Set default goal to build all PDFs
.DEFAULT_GOAL := all

# Default target: build all PDFs
.PHONY: all
all: $(PDF_FILES)

# Pattern rule: .txt -> .pdf (using txt2tex CLI via uv)
%.pdf: %.txt
	@echo "Building $@..."
	@cd .. && uv run txt2tex examples/$< || (echo "Error building $@"; exit 1)

# Subdirectory targets for convenience
.PHONY: $(SUBDIRS)
$(SUBDIRS):
	@echo "Building examples in $@..."
	@for f in $@/*.txt; do \
		if [ -f "$$f" ]; then \
			(cd .. && uv run txt2tex "examples/$$f") || { echo "failed: $$f" >&2; exit 1; }; \
		fi; \
	done

# Convenient short aliases
.PHONY: 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 fuzz
00: 00_getting_started
01: 01_propositional_logic
02: 02_predicate_logic
03: 03_equality
04: 04_proof_trees
05: 05_sets
06: 06_definitions
07: 07_relations
08: 08_functions
09: 09_sequences
10: 10_schemas
11: 11_text_blocks
12: 12_advanced
13: 13_equality_chains
14: 14_relational_databases
15: 15_schema_calculus
16: 16_multi_decl_calculus
17: 17_state_machines
fuzz: fuzz_tests

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
	@echo "  00-17                  - Build all examples in specific topic directory"
	@echo "  01_propositional_logic - Build examples in 01_propositional_logic/"
	@echo "  02_predicate_logic     - Build examples in 02_predicate_logic/"
	@echo "  03_equality            - Build examples in 03_equality/"
	@echo "  04_proof_trees         - Build examples in 04_proof_trees/"
	@echo "  05_sets                - Build examples in 05_sets/"
	@echo "  06_definitions         - Build examples in 06_definitions/"
	@echo "  07_relations           - Build examples in 07_relations/"
	@echo "  08_functions           - Build examples in 08_functions/"
	@echo "  09_sequences           - Build examples in 09_sequences/"
	@echo "  10_schemas             - Build examples in 10_schemas/"
	@echo "  11_text_blocks         - Build examples in 11_text_blocks/"
	@echo "  12_advanced            - Build examples in 12_advanced/"
	@echo "  13_equality_chains     - Build examples in 13_equality_chains/"
	@echo "  14_relational_databases - Build examples in 14_relational_databases/"
	@echo "  15_schema_calculus     - Build examples in 15_schema_calculus/"
	@echo "  16_multi_decl_calculus - Build examples in 16_multi_decl_calculus/"
	@echo "  17_state_machines      - Build examples in 17_state_machines/"
	@echo "  user_guide             - Build examples in user_guide/"
	@echo "  fuzz_tests / fuzz      - Build examples in fuzz_tests/"
	@echo "  clean                  - Remove auxiliary files"
	@echo "  distclean              - Remove all generated files"
	@echo "  list                   - Show this help"
	@echo ""
	@echo "Available .txt files:"
	@for f in $(TXT_FILES); do echo "  $$f"; done

# Help target
.PHONY: help
help: list
