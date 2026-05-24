.PHONY: help lint lint-md format format-check type type-pyright test test-cov check check-cov build clean \
	ethos-doctor ethos-agents ethos-team dev-doctor dev-setup test-e2e regen-e2e \
	complexity-report complexity-history qa qa-one reference

# `make` with no arguments prints the help.
.DEFAULT_GOAL := help

##@ Help

help:  ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n\nTargets:\n"} \
		/^##@/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 5)} \
		/^[a-zA-Z0-9_-]+:.*##/ {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' \
		$(MAKEFILE_LIST)

##@ Quality gates (use these before commit / push)

lint:  ## Run ruff lint over all Python sources
	uv run ruff check .

lint-md:  ## Lint Markdown files with markdownlint-cli2 (requires npx)
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes markdownlint-cli2 "**/*.md"; \
	else \
		echo "lint-md: npx not found — skipping. Install Node to enable: https://nodejs.org/en/download" >&2; \
	fi

format:  ## Auto-format Python sources with ruff
	uv run ruff format .

format-check:  ## Fail if formatting would change anything
	uv run ruff format --check .

type:  ## Run mypy in strict mode
	uv run mypy src/txt2tex tests

type-pyright:  ## Run pyright in strict mode
	uv run pyright

test:  ## Run the pytest suite (use ARGS=... to pass extra args)
	uv run pytest $(ARGS)

test-cov:  ## Run pytest with coverage (term + html report)
	uv run pytest --cov=src/txt2tex --cov-report=term-missing --cov-report=html $(ARGS)

check:  ## Composite gate: lint + lint-md + format-check + type + type-pyright + test
check: lint lint-md format-check type type-pyright test

check-cov:  ## check (without lint-md) but with coverage instead of plain test
check-cov: lint format-check type type-pyright test-cov

##@ End-to-end regression (not in `make check` — too slow for pre-commit)

test-e2e:  ## Run the .txt -> .tex fixture-comparison suite in parallel
	uv run pytest tests/test_e2e_regression.py -m e2e -n auto $(ARGS)

regen-e2e:  ## Regenerate every .tex fixture under examples/ (review diff before commit)
	@echo "Regenerating .tex fixtures for all examples..."
	@find examples -name "*.txt" -not -path "*/infrastructure/*" | sort | while read f; do \
		uv run txt2tex "$$f" --tex-only; \
	done
	@echo ""
	@echo "Done. Review 'git diff examples/' before committing."
	@echo "Commit only fixtures whose changes are intentional."

##@ PDF / LaTeX surface QA (examples corpus)

qa:  ## Run scripts/qa_check_all.sh over every examples/ PDF (150 files)
	scripts/qa_check_all.sh

qa-one:  ## Run scripts/qa_check.sh on a single PDF (PDF=path/to.pdf)
	@if [ -z "$(PDF)" ]; then \
		echo "Usage: make qa-one PDF=examples/01_propositional_logic/basic_operators.pdf" >&2; \
		exit 1; \
	fi
	scripts/qa_check.sh "$(PDF)"

##@ Complexity / code-quality assessment (local only; install with: uv sync --group complexity)

complexity-history:  ## Seed/extend wily history (run after fresh clone; WILY_REVS=N to widen)
	@command -v uv >/dev/null 2>&1 || { echo "uv not found; install: https://docs.astral.sh/uv/"; exit 1; }
	uv run --group complexity wily build src/txt2tex --max-revisions $(WILY_REVS)

WILY_REVS ?= 50

complexity-report:  ## Generate docs/complexity-report.{md,json} (radon+lizard+pydeps+wily)
	uv run --group complexity python scripts/complexity_report.py

##@ Reference card

reference:  ## Rebuild docs/reference.pdf and regenerate per-page PNGs in docs/_pages/
	cd docs && rm -f reference.pdf reference.aux reference.log reference.out reference.fls reference.fdb_latexmk
	cd docs && rm -f _pages/reference-*.png
	cd docs && mkdir -p _pages
	cd docs && pdflatex -interaction=nonstopmode reference.tex >/dev/null
	cd docs && pdflatex -interaction=nonstopmode reference.tex >/dev/null
	cd docs && pdftoppm -r 150 -png reference.pdf _pages/reference
	@echo "reference.pdf rebuilt; page PNGs in docs/_pages/"

##@ Build / clean

build:  ## Build the wheel + sdist and verify with twine
	uv build
	uvx twine check dist/*

clean:  ## Remove build artefacts and tool caches
	rm -rf dist/ build/ *.egg-info htmlcov/ .coverage || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

##@ Developer toolchain (ethos — agent team)

ethos-doctor:  ## Verify ethos is installed and the team is loaded
	@command -v ethos >/dev/null 2>&1 || { \
		echo "ethos not found. Install: curl -fsSL https://raw.githubusercontent.com/punt-labs/ethos/main/install.sh | sh"; \
		exit 1; \
	}
	ethos doctor
	ethos team show txt2tex

ethos-agents:  ## Regenerate .claude/agents/ from the ethos team definition
	@command -v ethos >/dev/null 2>&1 || { echo "ethos not installed; skipping"; exit 0; }
	@mkdir -p .tmp
	@python3 -c "import json,sys; print(json.dumps({'session_id':'manual','cwd':sys.argv[1]}))" "$(CURDIR)" \
		| ethos hook session-start >.tmp/ethos-agents-errors.log 2>&1 \
		&& echo "Regenerated .claude/agents/ from ethos team data" \
		|| { echo "ethos hook session-start failed; see .tmp/ethos-agents-errors.log"; cat .tmp/ethos-agents-errors.log; exit 1; }

ethos-team:  ## Print the txt2tex team roster
	@command -v ethos >/dev/null 2>&1 || { echo "ethos not installed"; exit 1; }
	ethos team show txt2tex

dev-doctor:  ## Verify the local dev environment (ethos + fuzz + latexmk + tex-fmt)
dev-doctor: ethos-doctor
	@command -v fuzz >/dev/null 2>&1 && echo "fuzz: present" || echo "fuzz: missing (Z type checking disabled)"
	@command -v latexmk >/dev/null 2>&1 && echo "latexmk: present" || echo "latexmk: missing (bibliography handling disabled)"
	@command -v tex-fmt >/dev/null 2>&1 && echo "tex-fmt: present" || echo "tex-fmt: missing (--format flag disabled)"

# Pinned to v3.3.0 (latest as of 2026-04-13).  Never pin to 'main' — that
# would allow arbitrary upstream code execution.
ETHOS_INSTALL_TAG ?= v3.3.0
dev-setup:  ## One-shot dev-machine setup (installs ethos at the pinned tag)
	@command -v ethos >/dev/null 2>&1 || \
		curl -fsSL "https://raw.githubusercontent.com/punt-labs/ethos/$(ETHOS_INSTALL_TAG)/install.sh" | sh
	@$(MAKE) ethos-agents
	@echo "Dev setup complete. Run 'make dev-doctor' to verify."
