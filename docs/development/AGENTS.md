# Agent Team

The txt2tex repo uses [ethos](https://github.com/punt-labs/ethos) to
manage its development team. This document describes who is on the team,
what each agent owns, and how to delegate work to them from a Claude
Code session.

## Team composition

The team is named `txt2tex` and is defined in
`.punt-labs/ethos/teams/txt2tex.yaml`. Identities and roles are
repo-local (under `.punt-labs/ethos/`) so that anyone cloning the repo
gets the same team without further setup.

| Handle | Role | Persona | What they own |
|--------|------|---------|---------------|
| `jfreeman` | `student` | principal-engineer | Sets goals, picks priorities, accepts deliverables |
| `jra` | `principal` | abrial — Jean-Raymond Abrial | Primary Claude agent. Leads, designs, instructs in state-based modeling |
| `jms` | `consultant` (read-only) | spivey — J. M. Spivey | Z notation, fuzz semantics, schema calculus, operator precedence |
| `rmh` | `python-specialist` | hettinger | Python implementation under `src/txt2tex` |
| `adb` | `infra-engineer` | lovelace — Ada Lovelace | Makefile, uv, install.sh, CI, LaTeX/fuzz toolchain |
| `ghr` | `docs-engineer` | hopper — Grace Hopper | README, docs, CHANGELOG, examples narrative |
| `mdm` | `cli-specialist` | mcilroy — Doug McIlroy | CLI surface, flags, error messages |
| `djb` | `security-reviewer` (read-only) | bernstein — D. J. Bernstein | Subprocess/path-traversal/input-validation review |

## Reporting structure

Every specialist `reports_to` `principal`. The principal `reports_to`
the `student`. The `consultant` (jms) `collaborates_with` the
`principal` — peer relationship, not a chain of command. This is what
the ethos team graph encodes:

```text
student (jfreeman)
   ▲
   │  reports_to
   │
principal (jra) ──collaborates_with── consultant (jms)
   ▲
   │  reports_to
   │
   ├── python-specialist (rmh)
   ├── infra-engineer (adb)
   ├── docs-engineer (ghr)
   ├── cli-specialist (mdm)
   └── security-reviewer (djb)
```

Each specialist's generated agent file (in `.claude/agents/<handle>.md`)
includes a `## What You Don't Do` section listing the principal's
responsibilities — derived mechanically from the team graph. This
prevents specialists from drifting into design or coordination work.

## Delegating work

When the principal (jra) needs specialist work done, the right pattern
is the **mission contract**:

1. Write a typed contract in `.tmp/missions/<short-name>.yaml` naming
   the worker, the evaluator, the write-set, the success criteria, and
   the budget.
2. Register it: `ethos mission create --file .tmp/missions/<name>.yaml`.
3. Spawn the worker: `Agent(subagent_type=<handle>, prompt="Mission
   m-... is yours. Read it via 'ethos mission show m-...'.",
   run_in_background=true)`.
4. Track via `ethos mission log m-...`.
5. Read the result via `ethos mission results m-...`, then close
   with `ethos mission close m-...`.

Mission contracts enforce:

- **Write-set admission** — the worker can only edit files in the
  contract's `write_set`.
- **Frozen evaluator** — the reviewer is content-hash-pinned at create
  time; if their personality, writing style, or talents change, the
  verifier refuses spawn.
- **Bounded rounds** — `budget.rounds` caps iteration; mandatory
  reflection between rounds.
- **Append-only event log** — every mission action is recorded.

For exploratory work where the contract is premature, spawn directly
via `Agent(subagent_type=<handle>, ...)` without a contract — but tell
the worker explicitly which files they may touch.

## When to consult jms

Always — before the principal takes any action that depends on Z
notation or fuzz semantics. The consultant's job is to be cheap to ask
and authoritative when consulted. Examples of questions to route to
jms first:

- "Does fuzz accept this LaTeX?"
- "What is the operator precedence here per the Z RM?"
- "Is this schema calculus expression well-typed?"
- "Why does fuzz reject this when it looks like standard Z?"

## Regenerating agents

If you change `.punt-labs/ethos/identities/`, `roles/`, or
`teams/txt2tex.yaml`, the `.claude/agents/*.md` files are stale until
you regenerate them:

```bash
make ethos-agents
```

The generation is idempotent — re-running with unchanged input
produces identical output. Restart Claude Code afterward so the new
agent definitions are picked up.

## Adding a new specialist

1. Pick a real-person archetype that fits the discipline (e.g., for
   data engineering: Codd, Stonebraker).
2. If the personality and writing-style do not exist in
   `.punt-labs/ethos/personalities/` or `writing-styles/`, copy them
   from `../punt-labs/quarry/.punt-labs/ethos/` if available, or
   author them locally.
3. Create the talent if needed in `.punt-labs/ethos/talents/`.
4. Create the identity in `.punt-labs/ethos/identities/<handle>.yaml`.
5. Create the role in `.punt-labs/ethos/roles/<role>.yaml`.
6. Add the member and `reports_to` edge to
   `.punt-labs/ethos/teams/txt2tex.yaml`.
7. `make ethos-doctor` to validate.
8. `make ethos-agents` to regenerate `.claude/agents/`.

## Reference

- ethos AGENTS guide: `../punt-labs/ethos/AGENTS.md`
- Mission skill design: `../punt-labs/ethos/docs/mission-skill-design.md`
- Team setup: `../punt-labs/ethos/docs/team-setup.md`
- Agent definitions: `../punt-labs/ethos/docs/agent-definitions.md`
