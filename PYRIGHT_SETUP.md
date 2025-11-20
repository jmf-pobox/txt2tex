# Pyright Configuration

This project now includes pyright type checking to match the errors shown in Cursor/VSCode.

## Commands

### Run pyright type checking
```bash
hatch run type-pyright
```

### Run pyright with statistics
```bash
hatch run type-pyright-stats
```

### Run both mypy and pyright
```bash
hatch run type-all
```

### Full check including pyright
```bash
hatch run check-all
```

## Current Status

- **MyPy**: ✅ Passing (strict mode)
- **Pyright**: ⚠️ 94 errors to fix

## Error Types

Pyright is configured to report:
- `reportUnknownMemberType` (information level)
- `reportUnknownVariableType` (information level)  
- `reportPrivateUsage` (error level)

## Configuration

Configuration is in `pyrightconfig.json`:
- Type checking mode: strict
- Python version: 3.10
- Includes: src, tests

## Next Steps

Fix the 94 pyright errors to achieve full type safety:

1. **Parser.py** - Add type annotations for instance variables (self.pos, etc.)
2. **Tests** - Fix protected method access (_generate_identifier, etc.)
3. **LaTeX Gen** - Add type hints for partially unknown types

Once fixed, update `check` command to include `type-pyright` by default.
