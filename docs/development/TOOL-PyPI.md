# PyPI Publishing Checklist for txt2tex

This checklist covers all steps for building, testing, and publishing the txt2tex package to PyPI, including local development installs and TestPyPI dry runs.

---

## 1. Bump the Version
- Update the version in `src/txt2tex/__version__.py`.

---

## 2. Build the Distribution
```sh
hatch build
```
- This creates `.whl` and `.tar.gz` files in the `dist/` directory.

---

## 3. Check the Distribution (Recommended)
```sh
hatch run publish:check
```
- Runs `twine check dist/*` to ensure your distributions are valid.

---

## 4. Test Install Locally (Editable/Dev Mode)
```sh
pip install -e .
```
- Installs your package in editable mode for local development.
- Uninstall with: `pip uninstall txt2tex`

---

## 5. Test the Build in a Clean Environment
```sh
python -m venv /tmp/txt2tex-test
source /tmp/txt2tex-test/bin/activate
pip install dist/txt2tex-*.whl
txt2tex --help
```
- Ensures the built wheel works as expected after install.

---

## 6. Test Upload to TestPyPI (Dry Run)
```sh
hatch run publish:test-publish
```
- This will upload to [TestPyPI](https://test.pypi.org/).
- You can install from TestPyPI with:
  ```sh
  pip install --index-url https://test.pypi.org/simple/ txt2tex
  ```

---

## 7. Upload to PyPI
```sh
hatch run publish:upload
```
- This runs `twine upload dist/*` and will prompt for your PyPI credentials or API token.

---

## 8. Verify on PyPI
- Check your package at: https://pypi.org/project/txt2tex/
- Try installing in a fresh environment:
  ```sh
  pip install txt2tex
  txt2tex --help
  ```

---

## 9. Troubleshooting
- If you get a version error, bump the version and rebuild.
- If dependencies are missing, add them to `[project] dependencies` in `pyproject.toml`.
- If the CLI doesn't work, verify the entry point in `[project.scripts]`.

---

## 10. Tag and Release
```sh
git tag vX.Y.Z
git push origin vX.Y.Z
```
- Tag your release in git for traceability.

---

## Environment Setup for Publishing

The publish environment is defined in `pyproject.toml`:

```toml
[tool.hatch.envs.publish]
dependencies = [
    "build",
    "twine",
]

[tool.hatch.envs.publish.scripts]
build = "python -m build"
upload = "twine upload dist/*"
check = "twine check dist/*"
test-publish = [
    "python -m build",
    "twine check dist/*",
    "twine upload --repository testpypi dist/*"
]
```

### Configuring PyPI Credentials

For `twine upload` to work without prompting, configure your `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN
```

Alternatively, use environment variables:
```sh
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-API-TOKEN
```

---

**Happy publishing!**

