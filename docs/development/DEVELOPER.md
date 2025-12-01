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
hatch run lint           # Ruff linting
hatch run type           # MyPy type checking (strict)
hatch run format --check # Code formatting
hatch run test-cov       # Tests with coverage
```

**Local development:** Run `hatch run check` before pushing (runs lint + type + test).

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:` code change (no new feature/fix)
- `test:` adding tests
- `ci:` CI/CD changes
