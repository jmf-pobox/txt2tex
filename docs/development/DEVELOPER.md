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

CI runs on all PRs:

```bash
hatch run check    # lint + type + test (run locally first)
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:` code change (no new feature/fix)
- `test:` adding tests
- `ci:` CI/CD changes

