# Developer Workflow

## Branch Protection

`main` is protected. All changes require:
- Feature branch → PR → CI pass → Merge

## Quick Start

```bash
# New feature
git checkout -b feat/description
# ... make changes ...
git commit -m "feat: description"
git push -u origin HEAD
# → Create PR on GitHub → Merge after CI passes

# Sync after merge
git checkout main && git pull
git branch -d feat/description
```

## Quality Gates

**CI runs these commands on all PRs:**

```bash
make lint           # Ruff linting
make format-check   # Code formatting
make type           # MyPy type checking (strict)
make type-pyright   # Pyright type checking (strict)
make test-cov       # Tests with coverage
```

**Local development:** Run `make check` before pushing (runs all of the above).

## Toolchain

| Tool | Purpose | Command |
|------|---------|---------|
| **uv** | Package manager, virtualenv, task runner | `uv sync`, `uv run` |
| **ruff** | Linting and formatting | `make lint`, `make format` |
| **mypy** | Type checking (strict) | `make type` |
| **pyright** | Type checking (strict, second opinion) | `make type-pyright` |
| **pytest** | Testing | `make test` |

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:` code change (no new feature/fix)
- `test:` adding tests
- `ci:` CI/CD changes
