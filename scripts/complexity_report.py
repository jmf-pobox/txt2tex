"""Generate a complexity / quality snapshot for src/txt2tex.

Composes four off-the-shelf tools into a single markdown report:

  - radon mi    : Maintainability Index per file (A/B/C grade + numeric).
  - radon cc -n D : Cyclomatic complexity, only D-grade and worse.
  - lizard      : Long / branchy functions (CCN >= 20 or NLOC >= 100).
  - pydeps      : Module fan-in / fan-out (raw counts; no graphviz needed).
  - wily report : Trend across the most recent N revisions, if a wily DB
                  exists.  Skipped silently otherwise.

The output is written to docs/complexity-report.md.  The same data is also
written to docs/complexity-report.json so a subsequent run can diff against
the prior snapshot and report deltas.

Usage:
    uv run python scripts/complexity_report.py [--src PATH] [--wily-revs N]

The script does not modify source; it is read-only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = REPO_ROOT / "src" / "txt2tex"
REPORT_MD = REPO_ROOT / "docs" / "complexity-report.md"
REPORT_JSON = REPO_ROOT / "docs" / "complexity-report.json"


def _run(cmd: list[str], *, cwd: Path = REPO_ROOT, check: bool = True) -> str:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
    return proc.stdout


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------

_MI_LINE = re.compile(r"^(.+?\.py)\s+-\s+([A-F])\s+\(([\d.]+)\)\s*$")


def collect_mi(src: Path) -> list[dict[str, Any]]:
    out = _run(["uv", "run", "radon", "mi", str(src), "-s"])
    rows: list[dict[str, Any]] = []
    for line in out.splitlines():
        m = _MI_LINE.match(line.strip())
        if m:
            rows.append(
                {
                    "file": str(Path(m.group(1)).relative_to(REPO_ROOT)),
                    "grade": m.group(2),
                    "mi": float(m.group(3)),
                }
            )
    rows.sort(key=lambda r: r["mi"])
    return rows


_CC_BLOCK_HEADER = re.compile(r"^(.+\.py)$")
_CC_ITEM = re.compile(
    r"^\s+([CFM])\s+(\d+):\d+\s+(\S+(?:\.\S+)?)\s+-\s+([A-F])\s+\((\d+)\)\s*$"
)


def collect_cc(src: Path, min_grade: str = "D") -> list[dict[str, Any]]:
    out = _run(["uv", "run", "radon", "cc", str(src), "-s", "-n", min_grade])
    rows: list[dict[str, Any]] = []
    current_file: str | None = None
    for line in out.splitlines():
        m = _CC_BLOCK_HEADER.match(line)
        if m:
            current_file = str(Path(m.group(1)).relative_to(REPO_ROOT))
            continue
        m = _CC_ITEM.match(line)
        if m and current_file is not None:
            rows.append(
                {
                    "file": current_file,
                    "line": int(m.group(2)),
                    "kind": {"C": "class", "F": "function", "M": "method"}[m.group(1)],
                    "name": m.group(3),
                    "grade": m.group(4),
                    "complexity": int(m.group(5)),
                }
            )
    rows.sort(key=lambda r: r["complexity"], reverse=True)
    return rows


def collect_lizard(
    src: Path,
    ccn_threshold: int = 20,
    length_threshold: int = 100,
) -> list[dict[str, Any]]:
    out = _run(
        [
            "uv",
            "run",
            "lizard",
            str(src),
            "--CCN",
            str(ccn_threshold),
            "--length",
            str(length_threshold),
        ],
        check=False,
    )
    rows: list[dict[str, Any]] = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 6:
            continue
        try:
            nloc = int(parts[0])
            ccn = int(parts[1])
            tokens = int(parts[2])
            params = int(parts[3])
            length = int(parts[4])
        except ValueError:
            continue
        last = parts[-1]
        if "@" not in last or ".py" not in last:
            continue
        name, _, location = last.partition("@")
        file_part = location.split("@", 1)[-1]
        try:
            relfile = str(Path(file_part).resolve().relative_to(REPO_ROOT))
        except ValueError:
            relfile = file_part
        rows.append(
            {
                "file": relfile,
                "function": name,
                "nloc": nloc,
                "ccn": ccn,
                "tokens": tokens,
                "params": params,
                "length": length,
            }
        )
    # lizard emits every function in its detail table; --CCN / --length
    # only affect the summary line.  Filter to the actual warnings ourselves.
    rows = [
        r for r in rows if r["ccn"] >= ccn_threshold or r["nloc"] >= length_threshold
    ]
    # lizard also emits each warning twice (per-file section + summary block).
    seen: set[tuple[str, str, int, int]] = set()
    deduped: list[dict[str, Any]] = []
    for r in rows:
        key = (r["file"], r["function"], r["ccn"], r["nloc"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    deduped.sort(key=lambda r: (r["ccn"], r["nloc"]), reverse=True)
    return deduped


def collect_pydeps(src: Path) -> list[dict[str, Any]]:
    raw = _run(
        ["uv", "run", "pydeps", str(src), "--show-deps", "--no-show"],
        check=False,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    inbound: dict[str, int] = {}
    outbound: dict[str, int] = {}
    for mod, info in data.items():
        deps = info.get("imports") or []
        outbound[mod] = len(deps)
        for dep in deps:
            inbound[dep] = inbound.get(dep, 0) + 1
    rows: list[dict[str, Any]] = []
    for mod in sorted(set(list(inbound) + list(outbound))):
        if "txt2tex" not in mod:
            continue
        rows.append(
            {
                "module": mod,
                "fan_in": inbound.get(mod, 0),
                "fan_out": outbound.get(mod, 0),
            }
        )
    return rows


_WILY_ROW = re.compile(
    r"^│\s+([a-f0-9]{7})\s+│\s*\S+\s*│\s+(\d{4}-\d{2}-\d{2})\s+│\s+(\d+)"
)


def collect_wily_trend(src: Path, *, n: int = 20) -> dict[str, list[dict[str, Any]]]:
    if not shutil.which("uv"):
        return {}
    wily_db = Path.home() / ".wily"
    if not wily_db.exists():
        return {}
    trends: dict[str, list[dict[str, Any]]] = {}
    for f in sorted(src.glob("*.py")):
        if f.stat().st_size < 1000:
            continue
        rel = str(f.relative_to(REPO_ROOT))
        try:
            wily_cmd = [
                "uv",
                "run",
                "wily",
                "report",
                rel,
                "raw.loc",
                "cyclomatic.complexity",
                "-n",
                str(n),
            ]
            out = _run(wily_cmd, check=False)
        except RuntimeError:
            continue
        series: list[dict[str, Any]] = []
        for line in out.splitlines():
            m = _WILY_ROW.match(line)
            if m:
                # Parse the LoC + CC numbers from the cells after the date.
                cells = [c.strip() for c in line.split("│")[1:-1]]
                if len(cells) >= 5:
                    cc_cell = cells[3]
                    loc_cell = cells[4]
                    cc_val = re.match(r"(\d+)", cc_cell)
                    loc_val = re.match(r"(\d+)", loc_cell)
                    series.append(
                        {
                            "commit": m.group(1),
                            "date": m.group(2),
                            "loc": int(loc_val.group(1)) if loc_val else None,
                            "cc": int(cc_val.group(1)) if cc_val else None,
                        }
                    )
        if series:
            trends[rel] = series
    return trends


# ---------------------------------------------------------------------------
# Snapshot diff (vs prior JSON)
# ---------------------------------------------------------------------------


def load_prior_snapshot() -> dict[str, Any] | None:
    if not REPORT_JSON.exists():
        return None
    try:
        return json.loads(REPORT_JSON.read_text())
    except json.JSONDecodeError:
        return None


def diff_mi(prior: list[dict[str, Any]], curr: list[dict[str, Any]]) -> list[str]:
    prior_map = {r["file"]: r["mi"] for r in prior}
    notes: list[str] = []
    for r in curr:
        if r["file"] in prior_map and abs(r["mi"] - prior_map[r["file"]]) >= 0.5:
            delta = r["mi"] - prior_map[r["file"]]
            arrow = "↑" if delta > 0 else "↓"
            notes.append(
                f"  {r['file']}: MI {prior_map[r['file']]:.2f} -> "
                f"{r['mi']:.2f} ({arrow}{abs(delta):.2f})"
            )
    return notes


def diff_cc_count(prior: list[dict[str, Any]], curr: list[dict[str, Any]]) -> str:
    return f"  D-or-worse functions: {len(prior)} → {len(curr)}"


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_markdown(snapshot: dict[str, Any], prior: dict[str, Any] | None) -> str:
    parts: list[str] = []
    ts = snapshot["generated"]
    commit = snapshot.get("commit", "unknown")
    parts.append("# Complexity Report\n")
    parts.append(f"_Generated {ts} at commit `{commit}`._\n")
    parts.append(
        "This snapshot is produced by `make complexity-report` (see "
        "`scripts/complexity_report.py`).  It composes radon, lizard, pydeps, "
        "and wily into a point-in-time view of the codebase plus a trend "
        "window if a wily history exists.\n"
    )

    # Maintainability Index
    parts.append("## Maintainability Index (radon mi)\n")
    parts.append("Lower = harder to maintain.  Grades: A >= 20, B 10-19, C < 10.\n")
    parts.append("| File | MI | Grade |")
    parts.append("|------|---:|:-----:|")
    parts.extend(
        f"| `{r['file']}` | {r['mi']:.2f} | {r['grade']} |" for r in snapshot["mi"]
    )
    parts.append("")

    # Cyclomatic Complexity (D+)
    parts.append("## Cyclomatic Complexity ≥ D (radon cc)\n")
    parts.append("Functions / methods with cyclomatic complexity grade D or worse.\n")
    cc_rows = snapshot["cc"]
    if not cc_rows:
        parts.append("_None._\n")
    else:
        parts.append("| File | Line | Name | CC | Grade |")
        parts.append("|------|-----:|------|---:|:-----:|")
        parts.extend(
            f"| `{r['file']}` | {r['line']} | `{r['name']}` | "
            f"{r['complexity']} | {r['grade']} |"
            for r in cc_rows[:25]
        )
        if len(cc_rows) > 25:
            parts.append(f"\n_…{len(cc_rows) - 25} more not shown._\n")
        else:
            parts.append("")

    # Lizard warnings
    parts.append("## Lizard Warnings (CCN ≥ 20 or NLOC ≥ 100)\n")
    liz = snapshot["lizard"]
    if not liz:
        parts.append("_No functions exceed thresholds._\n")
    else:
        parts.append(f"_{len(liz)} function(s) exceed thresholds._\n")
        parts.append("| File | Function | CCN | NLOC | Tokens | Params |")
        parts.append("|------|----------|----:|-----:|-------:|-------:|")
        parts.extend(
            f"| `{r['file']}` | `{r['function']}` | "
            f"{r['ccn']} | {r['nloc']} | {r['tokens']} | {r['params']} |"
            for r in liz[:20]
        )
        if len(liz) > 20:
            parts.append(f"\n_…{len(liz) - 20} more not shown._\n")
        else:
            parts.append("")

    # Module structure
    parts.append("## Module Structure (pydeps)\n")
    deps = snapshot["pydeps"]
    if not deps:
        parts.append("_pydeps output unavailable._\n")
    else:
        parts.append("| Module | Fan-in | Fan-out |")
        parts.append("|--------|-------:|--------:|")
        parts.extend(
            f"| `{r['module']}` | {r['fan_in']} | {r['fan_out']} |" for r in deps
        )
        parts.append("")

    # Recent trend section, populated only when wily history is available.
    trends = snapshot.get("trend", {})
    parts.append("## Recent Trend (wily)\n")
    if not trends:
        parts.append(
            "_No wily history available.  Run `uv run wily build src/txt2tex "
            "--max-revisions 50` to seed the cache, then re-run this report._\n"
        )
    else:
        parts.append(
            "LoC and cyclomatic complexity at the **oldest** and **newest** "
            "revisions in the wily window.  Files with zero net change in both "
            "metrics are omitted.\n"
        )
        parts.append(
            "| File | Oldest commit | Oldest LoC | Oldest CC | Newest commit "
            "| Newest LoC | Newest CC | LoC d | CC d |"
        )
        parts.append(
            "|------|--------------|-----------:|----------:|---------------"
            "|-----------:|----------:|------:|-----:|"
        )
        sig_rows: list[tuple[str, dict[str, Any], dict[str, Any], int, int]] = []
        for path, series in trends.items():
            if not series:
                continue
            oldest = series[-1]
            newest = series[0]
            loc_d = (newest["loc"] or 0) - (oldest["loc"] or 0)
            cc_d = (newest["cc"] or 0) - (oldest["cc"] or 0)
            if loc_d == 0 and cc_d == 0:
                continue
            sig_rows.append((path, oldest, newest, loc_d, cc_d))
        # Sort by absolute LoC change (largest moves first).
        sig_rows.sort(key=lambda t: abs(t[3]), reverse=True)
        for path, oldest, newest, loc_d, cc_d in sig_rows:
            parts.append(
                f"| `{path}` | `{oldest['commit']}` ({oldest['date']}) | "
                f"{oldest['loc']} | {oldest['cc']} | "
                f"`{newest['commit']}` ({newest['date']}) | "
                f"{newest['loc']} | {newest['cc']} | "
                f"{loc_d:+d} | {cc_d:+d} |"
            )
        if not sig_rows:
            parts.append("| _no changes in window_ |  |  |  |  |  |  |  |  |")
        parts.append("")

    # Diff vs prior snapshot
    if prior:
        parts.append("## Delta vs Prior Snapshot\n")
        prior_ts = prior.get("generated", "?")
        prior_commit = prior.get("commit", "?")
        parts.append(f"Prior snapshot: {prior_ts} @ `{prior_commit}`\n")
        mi_notes = diff_mi(prior.get("mi", []), snapshot["mi"])
        if mi_notes:
            parts.append("**MI shifts (Δ ≥ 0.5):**")
            parts.extend(mi_notes)
            parts.append("")
        else:
            parts.append("_No MI shifts ≥ 0.5._\n")
        parts.append(diff_cc_count(prior.get("cc", []), snapshot["cc"]))
        parts.append(
            f"  Lizard warnings: {len(prior.get('lizard', []))} → "
            f"{len(snapshot['lizard'])}"
        )
        parts.append("")

    parts.append("---\n")
    parts.append(
        "_Generated by `scripts/complexity_report.py`.  Both "
        "`docs/complexity-report.md` and `docs/complexity-report.json` are "
        "committed so future runs can show deltas._\n"
    )
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--wily-revs", type=int, default=20)
    args = parser.parse_args()

    src: Path = args.src
    if not src.exists():
        print(f"src not found: {src}", file=sys.stderr)
        return 1

    try:
        commit = _run(["git", "rev-parse", "--short", "HEAD"]).strip()
    except RuntimeError:
        commit = "unknown"

    snapshot: dict[str, Any] = {
        "generated": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "commit": commit,
        "src": str(src.relative_to(REPO_ROOT)),
        "mi": collect_mi(src),
        "cc": collect_cc(src),
        "lizard": collect_lizard(src),
        "pydeps": collect_pydeps(src),
        "trend": collect_wily_trend(src, n=args.wily_revs),
    }

    prior = load_prior_snapshot()
    md = render_markdown(snapshot, prior)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(md)
    REPORT_JSON.write_text(json.dumps(snapshot, indent=2) + "\n")

    print(f"Wrote {REPORT_MD.relative_to(REPO_ROOT)}")
    print(f"Wrote {REPORT_JSON.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
