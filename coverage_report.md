# Line Coverage Report for the System Model

COMP3211 Software Engineering — Group Project

## 1. How this report was produced

The project may only use standard libraries, so coverage is measured with the standard-library `trace` module rather than a third-party tool.

```text
python -m unittest discover -s tests -t .
python -m trace --count --missing --summary --coverdir cover/ \
    --module unittest discover -s tests -t .
python coverage_report.py
```

`trace` writes one `.cover` file per executed module, marking lines that never ran with a leading `>>>>>>`. `coverage_report.py` reads those markers for the project's own packages and prints the tables below. Both scripts ship in the source root so the result is reproducible.

Test suite: **188 tests, all passing.**

## 2. Line coverage — the model package

| Module | Executed | Total | Coverage |
|---|---|---|---|
| `model.contact` | 31 | 31 | 100.0% |
| `model.criteria` | 112 | 112 | 100.0% |
| `model.errors` | 9 | 9 | 100.0% |
| `model.event` | 40 | 40 | 100.0% |
| `model.expression` | 209 | 209 | 100.0% |
| `model.note` | 13 | 13 | 100.0% |
| `model.pir` | 84 | 84 | 100.0% |
| `model.repository` | 57 | 57 | 100.0% |
| `model.storage` | 71 | 71 | 100.0% |
| `model.task` | 20 | 20 | 100.0% |
| **Total** | **646** | **646** | **100.0%** |

## 3. The uncovered lines

Every line of the model package is executed by the suite, so there is nothing uncovered to explain: 376 of 376 statements, 100.0%.

Two branches were the last to be covered, and both are now pinned by a test that names them:

`model/criteria.py` — `TimeCompare.matches` catches the `ValidationError` that `parse_timestamp` raises for a stored value that is not in our format, and returns `False` rather than crashing the search. A record with such a value can only arrive from a hand-edited `.pim` file. Pinned by `test_time_compare_skips_unparseable_stored_value`, which sets the bad value on a record that really carries the field.

`model/storage.py` — the loader reports an OS-level read failure other than `FileNotFoundError` as a `PIMError` (`could not read …`), so the controller can print it instead of a traceback. Pinned by `test_unreadable_path_is_reported_as_pim_error`.

The `Criterion` base class raises `NotImplementedError` in both methods; those two statements count as executed because `test_base_criterion_methods_are_abstract` calls them and asserts the exception.

## 4. The other layers, for context

Reported separately because the brief requires coverage of the **model**. They are covered by the controller tests, which drive the real application through scripted stdin.

| Module | Executed | Total | Coverage |
|---|---|---|---|
| `controller.app_controller` | 231 | 244 | 94.7% |
| `view.console_view` | 39 | 57 | 68.4% |
| **Total** | **270** | **301** | **89.7%** |

The uncovered remainder is menu text for paths the tests do not trigger, such as printing the current-record header before a field edit that is then abandoned. These are presentation branches with no logic of their own.

## 5. Why main.py is not measured

`main.py` is a thin bootstrap: it constructs `PIMRepository`, `ConsoleView` and `AppController`, then calls `run()`. There is no logic in it to test. The wiring it performs is exercised indirectly by `tests/test_controller.py`, which builds the same three objects.
