## Plan 03: Specific Exception Handling and Better Messages (Behavior-Preserving)

### Objective
Replace broad `except Exception` with precise exceptions and improve error messages with context and guidance, without changing control flow or exit codes.

### Scope
- CLI I/O paths (`src/txt2tex/cli.py`)
- Generator parsing fallback (`src/txt2tex/latex_gen.py`)
- Audit raise sites for clarity and suggestions (parser/generator)

### Guardrails
- Preserve return codes and stderr/stdout behavior
- Do not catch `KeyboardInterrupt` or `SystemExit`
- Keep messages stable except for added context (no semantic behavior change)

### Phased Steps

1) Define Domain Exceptions (No Behavior Change Yet)
- Add `src/txt2tex/errors.py` with typed exceptions (as thin aliases if needed):
  - `InputReadError` (optional wrapper)
  - Reuse `LexerError`, `ParserError` (already present)
  - `GenerationFallback` (marker for expected fallback paths)
- No usages yet; commit to establish taxonomy

2) Tighten CLI Exception Handling
- In `cli.py`, replace
  - `except Exception as e` on read with `except (FileNotFoundError, PermissionError, IsADirectoryError) as e`
  - processing block’s broad catch with `except (LexerError, ParserError, ValueError) as e`
- Messages: include file path and a brief hint (e.g., "check path and permissions")
- Keep exit code `1` and message format (stderr) unchanged apart from added detail

3) Tighten Generator Fallback Catch
- In `latex_gen.py` fallback region, replace `except Exception` with `except (LexerError, ParserError, ValueError)`
- Add a brief inline comment explaining that only expected parse failures should be handled here; everything else must surface

4) Improve Raise Messages (Low Risk)
- Augment existing raise sites with context variables
  - Example: `Expected variable name after ';' in quantifier; found {token.value!r}`
- Do not change exception types; only message strings

5) Tests
- Add CLI tests that simulate missing file, permission error, directory path
- Add generator fallback tests where inner parse fails but outer conversion succeeds
- Ensure unexpected exceptions are not swallowed (simulate via injected error)

### Completion Criteria
- No `except Exception` in the codebase within the targeted modules
- CLI and generator produce clearer, contextual messages
- All tests remain green; exit codes unchanged


