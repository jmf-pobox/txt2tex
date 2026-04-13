.PHONY: lint format format-check type type-pyright test test-cov check check-cov build clean \
	ethos-doctor ethos-agents ethos-team dev-doctor dev-setup

lint:
	uv run ruff check .

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

check: lint format-check type type-pyright test

check-cov: lint format-check type type-pyright test-cov

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
