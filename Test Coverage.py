"""Compute line coverage for the model package from trace output.

This produces the Deliverable 4.b report. It reads the .cover files written by
`python -m trace --count --missing --summary --coverdir cover/`, which marks
unexecuted lines with a leading '>>>>>>'.

Usage:
    python -m trace --count --missing --summary --coverdir cover/ \
        --module unittest discover -s tests -t .
    python coverage_report.py
"""

import glob
import os
import re

#: The model package is what Deliverable 4 asks for.
MODEL_PREFIX = "model."

#: The other layers, reported separately for context.
CONTROLLER_PREFIX = "controller."
VIEW_PREFIX = "view."

COVERDIR = "cover"

#: Line holds no executable statement, only its unreached-body marker.
_MARKER = ">>>>>>"


def measure(path):
    """Return (executed, total) executable lines in one .cover file."""
    executed = total = 0
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith(_MARKER):
                total += 1
            elif re.match(r"\s*\d+:", line):
                total += 1
                executed += 1
    return executed, total


def collect():
    """Gather (module, executed, total) for the project's own packages."""
    rows = []
    for path in glob.glob(os.path.join(COVERDIR, "*.cover")):
        name = os.path.basename(path)[: -len(".cover")]
        if not (
            name.startswith(MODEL_PREFIX)
            or name.startswith(CONTROLLER_PREFIX)
            or name.startswith(VIEW_PREFIX)
        ):
            continue
        # __init__ modules are import wiring, not behaviour.
        if name.endswith(".__init__"):
            continue
        executed, total = measure(path)
        if total:
            rows.append((name, executed, total))
    rows.sort()
    return rows


def print_table(title, rows):
    """Print one coverage table with a total row."""
    if not rows:
        return
    print()
    print(title)
    print(f"{'Module':<26}{'Executed':>10}{'Total':>8}{'Coverage':>11}")
    print("-" * 55)
    for name, executed, total in rows:
        print(f"{name:<26}{executed:>10}{total:>8}{100 * executed / total:>10.1f}%")
    executed = sum(row[1] for row in rows)
    total = sum(row[2] for row in rows)
    print("-" * 55)
    print(f"{'TOTAL':<26}{executed:>10}{total:>8}{100 * executed / total:>10.1f}%")


def main():
    rows = collect()
    if not rows:
        print(f"No .cover files found in {COVERDIR}/.")
        print(
            "Run: python -m trace --count --missing --summary "
            "--coverdir cover/ --module unittest discover -s tests -t ."
        )
        return

    model = [r for r in rows if r[0].startswith(MODEL_PREFIX)]
    others = [r for r in rows if not r[0].startswith(MODEL_PREFIX)]

    print_table(
        "MODEL PACKAGE (the deliverable)",
        model,
    )
    print_table(
        "CONTROLLER AND VIEW (context only)",
        others,
    )


if __name__ == "__main__":
    main()
