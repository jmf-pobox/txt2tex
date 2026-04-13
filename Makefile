.PHONY: lint lint-md format format-check type type-pyright test test-cov check check-cov build clean \
	ethos-doctor ethos-agents ethos-team dev-doctor dev-setup test-e2e regen-e2e

lint:
	uv run ruff check .

# Markdown linting. Uses npx so contributors do not need a global install.
# Config lives in .markdownlint.jsonc and .markdownlint-cli2.jsonc.
lint-md:
	npx --yes markdownlint-cli2 "**/*.md"

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

type:
	uv run mypy src/txt2tex tests

type-pyright:
	uv run pyright

test:
	uv run pytest $(ARGS)

test-cov:
	uv run pytest --cov=src/txt2tex --cov-report=term-missing --cov-report=html $(ARGS)

check: lint lint-md format-check type type-pyright test

check-cov: lint format-check type type-pyright test-cov

# --- End-to-end regression tests (Stage A: generation fixture assertions) ---
# Separate from 'make check' — subprocess per example makes this too slow for
# the pre-commit loop. Run manually before pushing or when the generator changes.

# Run the Phase 1 e2e suite in parallel via pytest-xdist.
# All 141 examples are parametrized; each runs txt2tex --tex-only and compares
# output to the committed .tex fixture. Do not add to 'make check'.
# The -m e2e flag overrides the addopts default of '-m not e2e'.
test-e2e:
	uv run pytest tests/test_e2e_regression.py -m e2e -n auto $(ARGS)

# Regenerate all committed .tex fixtures in place by running txt2tex on every
# .txt file under examples/ (excluding examples/infrastructure/).
# Developer tool only — CI never calls this target.
# After running: inspect 'git diff examples/' and commit only intended changes.
regen-e2e:
	@echo "Regenerating .tex fixtures for all examples..."
	@find examples -name "*.txt" -not -path "*/infrastructure/*" | sort | while read f; do \
		uv run txt2tex "$$f" --tex-only; \
	done
	@echo ""
	@echo "Done. Review 'git diff examples/' before committing."
	@echo "Commit only fixtures whose changes are intentional."

build:
	uv build
	uvx twine check dist/*

clean:
	rm -rf dist/ build/ *.egg-info htmlcov/ .coverage || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# --- Ethos (developer toolchain) ---
# These targets manage the txt2tex agent team via ethos. End users running
# txt2tex do not need ethos; only developers extending the tool do.

ethos-doctor:
	@command -v ethos >/dev/null 2>&1 || { \
		echo "ethos not found. Install: curl -fsSL https://raw.githubusercontent.com/punt-labs/ethos/main/install.sh | sh"; \
		exit 1; \
	}
	ethos doctor
	ethos team show txt2tex

ethos-agents:
	@command -v ethos >/dev/null 2>&1 || { echo "ethos not installed; skipping"; exit 0; }
	@printf '{"session_id":"manual","cwd":"$(CURDIR)"}\n' | ethos hook session-start \
		>/dev/null 2>&1 && echo "Regenerated .claude/agents/ from ethos team data"

ethos-team:
	@command -v ethos >/dev/null 2>&1 || { echo "ethos not installed"; exit 1; }
	ethos team show txt2tex

# Run before opening a PR or starting cross-tool work
dev-doctor: ethos-doctor
	@command -v fuzz >/dev/null 2>&1 && echo "fuzz: present" || echo "fuzz: missing (Z type checking disabled)"
	@command -v latexmk >/dev/null 2>&1 && echo "latexmk: present" || echo "latexmk: missing (bibliography handling disabled)"
	@command -v tex-fmt >/dev/null 2>&1 && echo "tex-fmt: present" || echo "tex-fmt: missing (--format flag disabled)"

# One-shot dev-machine setup. Idempotent.
dev-setup:
	@command -v ethos >/dev/null 2>&1 || curl -fsSL https://raw.githubusercontent.com/punt-labs/ethos/main/install.sh | sh
	@$(MAKE) ethos-agents
	@echo "Dev setup complete. Run 'make dev-doctor' to verify."
