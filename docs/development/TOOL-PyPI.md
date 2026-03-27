# PyPI Publishing Checklist for txt2tex

---

## 1. Bump the Version
- Update the version in `src/txt2tex/__version__.py`.

---

## 2. Build the Distribution
```sh
make build
```
- This runs `uv build` and `twine check dist/*`.

---

## 3. Test Install Locally
```sh
uv pip install -e .
```
- Installs your package in editable mode for local development.

---

## 4. Test the Build in a Clean Environment
```sh
uv run --isolated --with dist/txt2tex-*.whl -- txt2tex --help
```
- Ensures the built wheel works as expected after install.

---

## 5. Upload to PyPI

```sh
uvx twine upload dist/*
```
Tag the release in git:
```sh
git tag vX.Y.Z
git push origin main vX.Y.Z
```

---

## 6. Verify on PyPI
- Check your package at: https://pypi.org/project/txt2tex/
- Try installing in a fresh environment:
  ```sh
  uv tool install txt2tex
  txt2tex --help
  ```

---

## 7. Troubleshooting
- If you get a version error, bump the version and rebuild.
- If dependencies are missing, add them to `[project] dependencies` in `pyproject.toml`.
- If the CLI doesn't work, verify the entry point in `[project.scripts]`.
