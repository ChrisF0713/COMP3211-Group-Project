# COMP3211 Group Project — Personal Information Management (PIM)

Command-line PIM system in Python 3. Object-oriented, **MVC-separated**, standard library only.

**Deadline:** Fri 2026-11-20, 20:00 — one ZIP archive.

## Hard constraints (from the brief)

| Rule | Status |
|---|---|
| Command-line only — no GUI, no web | Enforced |
| Python **or** Java | Python 3 |
| Implementation imports **standard library only** | Satisfied |
| All model code in a package named `model` | `model/` |
| Unit tests target the **model** | `tests/test_model.py` |
| Docs in DOC/DOCX/PDF, video in MP4 | Not yet produced |
| Honour Declaration in the **ZIP root** | Not yet produced |

Extra features earn no credit. Do not add them.

## Run

```bash
python main.py [--debug]
```

Menu-driven, 12 options. `0` returns to the previous menu at any prompt.
`--debug` traces every dispatched action to stderr (`[debug] action=… records=…`);
stdout stays untouched, so a debug session is diffable against a normal one.
Timestamps use `YYYY-MM-DD HH:MM` (e.g. `2026-11-20 18:00`); that single format is
enforced by the model, so a badly shaped value is rejected at entry, not discovered later.

## Test

```bash
python -m unittest discover -s tests -t .
```

**123 tests, all passing.**

- `tests/test_model.py` — the deliverable suite. Record types, the US7 expression tree,
  the repository and the `.pim` format, all without touching the CLI.
- `tests/test_controller.py` — drives `AppController` with scripted stdin through a real
  `ConsoleView`, so the three layers are proven to be wired correctly.

`-s tests` selects the test package and `-t .` puts the project root on the import path.
`tests/` has an `__init__.py`, which both makes discovery work and matches the project's
package-per-layer convention.

## Coverage

Report in [`coverage_report.txt`](coverage_report.txt) — Deliverable 4.b, reproducible.

```bash
python -m trace --count --missing --summary --coverdir cover/ \
    --module unittest discover -s tests -t .
python coverage_report.py
```

`--module unittest discover` is the working form; `-m unittest discover` fails. `coverage`
(PyPI) is a dev-time tool that never ships inside the system, so it would not break the
stdlib-only rule — but the tracer avoids the question entirely.

| Scope | Coverage |
|---|---|
| **Model package** (the deliverable) | **99.2%** (361/364) |
| Controller and view, for context | 81.4% |

Per module the model is at or near 100%; the three uncovered lines are the two abstract
`NotImplementedError` stubs in the criteria Component and one unreachable guard in the
storage loader. `coverage_report.txt` explains each one, so the exclusion reads as a
decision rather than an oversight.

## Structure

Three packages, one per MVC role, plus a `tests` package. Nothing is left in the root
except the entry point and the report artefacts.

```text
COMP3211-Group-Project/
├── main.py                  # bootstrap only: wires the three layers, calls run()
│
├── model/                   # MODEL — data, rules, persistence. No print, no input.
│   ├── __init__.py          #   the package's public surface
│   ├── errors.py            #   PIMError and its four subclasses
│   ├── pir.py               #   abstract base: id, field access, (de)serialisation
│   ├── note.py              #   content
│   ├── task.py              #   description, deadline
│   ├── event.py             #   description, starting_time, alarm
│   ├── contact.py           #   name, address, mobile_number
│   ├── criteria.py          #   US7 search expression tree (Composite pattern)
│   ├── repository.py        #   the record collection and every operation on it
│   └── storage.py           #   .pim read/write
│
├── view/                    # VIEW — every byte shown to or read from the user
│   ├── __init__.py
│   └── console_view.py
│
├── controller/              # CONTROLLER — user intent to model operations
│   ├── __init__.py
│   └── app_controller.py
│
├── tests/                   # the test package
│   ├── __init__.py
│   ├── test_model.py
│   └── test_controller.py
│
├── coverage_report.py       # rebuilds the coverage tables from trace output
├── coverage_report.txt      # Deliverable 4.b
└── .gitignore
```

### Why `model/` is a package, not a folder

`__init__.py` is what makes a directory importable as a Python package
([Python docs, Packages](https://docs.python.org/3/tutorial/modules.html#packages)). It is
also the model's contract: `from model import PIMRepository, TextContains, ValidationError`
gives callers one import line and one place to see what the layer offers, instead of
reaching into individual modules. The `__all__` list in that file is the authoritative
public surface.

The layout is a **flat layout** in the sense of the
[Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/):
the import packages sit at the top level. A `src/` layout would be the choice for a
published, pip-installable library; here it would add an installation step before
`python main.py` works, which the developer manual would then have to explain. For a
course deliverable that is run from source, flat is the right trade.

## Architecture: MVC

| Pattern role | Package | Responsibility |
|---|---|---|
| **Model** | `model/` | Owns the records, enforces invariants, defines the file format |
| **View** | `view/` | Reads input, prints output. Knows nothing about records or rules |
| **Controller** | `controller/` | Maps a menu selection to exactly one model operation, then hands the result to the view |

The dependency direction is one-way: **controller → model**, **controller → view**. The
model imports neither of the other two — that is what makes it unit-testable without
capturing stdout, which is exactly what Deliverable 4 needs. `view/console_view.py` is the
only module in the project that calls `print` or `input`.

Why MVC here rather than a monolith: US7 makes the data model non-trivial (four record
types plus an expression tree), while the presentation is deliberately plain. Separating
them means the search logic can be tested at 99% coverage without a single mocked prompt,
and the view could be replaced without touching the rules.

## Search criteria (US7)

US7 is the heaviest requirement: a criterion tests text (contains), time
(`<` before, `>` after, `=` equal) or type, and any of those combine with `&&`, `||` and `!`,
including nesting. That is an expression grammar, so it is modelled as one — a Composite
tree in `model/criteria.py`:

```text
Criterion                 Component
├── TextContains          Leaf
├── TimeCompare           Leaf
├── TypeIs                Leaf
├── And, Or               Composite  (n operands)
└── Not                   Composite  (1 operand)
```

Every node answers `matches(record)`, so `PIMRepository.search()` never inspects criterion
internals — it asks each record whether it matches. Adding a criterion means adding one
leaf class; nothing else changes. `describe()` renders a tree back to US7 notation
(`&&`, `||`, `!`) for display.

This is the Composite pattern from Lecture 08, applied where it genuinely fits rather than
decoratively. The CLI builds the tree recursively, which is what makes nesting work.

Text fields: `content`, `description`, `name`, `address`, `mobile_number`.
Time fields: `deadline`, `starting_time`, `alarm`.

## `.pim` format (US10, US11)

A JSON array, one object per record, discriminated by `"type"`:

```json
[
  { "type": "Task", "pir_id": "a1b2c3d4",
    "description": "Submit project", "deadline": "2026-11-20 18:00" }
]
```

UTF-8, indented, non-ASCII preserved. IDs are restored on load, so a save/load cycle is
lossless. The format is **validated on read**: an unknown type, a missing field or a
malformed timestamp is reported as an error rather than silently accepted.

`Storage.load()` parses the whole file before the repository replaces its contents, so a
corrupt file leaves the user's current records intact instead of wiping them. That is
tested (`test_repository_load_keeps_old_records_when_file_is_bad`). The loader also
validates the record IDs it reads: a record without a non-empty string ID, or repeating
an ID used earlier in the same file, is rejected — otherwise `get`, `modify` and `delete`
would be ambiguous about which record an ID names.

Loading a file while records are still in memory asks first (`Loading will replace the N
record(s) currently in memory; unsaved changes will be lost. Continue? (y/n)`), because
a valid file would otherwise overwrite unsaved work silently. With an empty collection
no prompt is shown.

## Requirement coverage

All 11 user stories are implemented:

| | Story | Where |
|---|---|---|
| US1–US5 | Create note / task / event / contact | `AppController.create_record` |
| US6 | Modify an existing PIR | `AppController.modify_record` → `PIMRepository.update` |
| US7 | Search with contains / `<` `>` `=` / `&&` `\|\|` `!` | `model/criteria.py`, menus 6–9 |
| US8 | Print one PIR or all PIRs | `AppController.display_all`, `display_one` |
| US9 | Delete a PIR | `PIMRepository.delete` |
| US10 | Save to `.pim` | `model/storage.py`, menu 10 |
| US11 | Load from `.pim` | `model/storage.py`, menu 11 |

The formal coverage report required by Deliverable 3.e still has to be written into this
folder.

## Deliverable status

| Deliverable | Pts | State |
|---|---|---|
| SRS | 6 | Not started |
| Design document | 5 | Not started |
| Implementation (code, dev manual, user manual, ≤4 min MP4) | 6 | Code done; manuals and video outstanding |
| Unit tests for the model | 4 | **Done** — 124 tests, 99.2% model coverage, `coverage_report.txt` |
| Presentation slides (PDF) + recording (MP4, ≤5 min, each member ≥1 min) | 4 | Not started |

Also outstanding: the requirements coverage table (Deliverable 3.e) and the Honour
Declaration with per-member contribution percentages.

## Group

| Member | Contribution % |
|---|---|
| _to be agreed_ | |
