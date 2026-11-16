"""Tests for the controller, driven with scripted input.

Run from the project root:

    python -m unittest discover -s tests -t .
"""

import io
import os
import sys
import unittest
from contextlib import redirect_stdout

from controller import AppController
from model import (
    Contact,
    InvalidFieldError,
    Note,
    PIMRepository,
    Storage,
    Task,
)
from view import ConsoleView


class ControllerTestCase(unittest.TestCase):
    """Base class that points stdin at a script and captures stdout."""

    def setUp(self):
        self.repository = PIMRepository()
        self.view = ConsoleView()
        self.controller = AppController(
            repository=self.repository, view=self.view
        )
        self._real_stdin = sys.stdin

    def tearDown(self):
        sys.stdin = self._real_stdin

    def run_script(self, script):
        """Run the app against `script`, returning what it printed."""
        sys.stdin = io.StringIO(script)
        out = io.StringIO()
        with redirect_stdout(out):
            self.controller.run()
        return out.getvalue()


class TestMenuHandling(ControllerTestCase):

    def test_exit_by_menu_number(self):
        # Menu 12 exits cleanly.
        out = self.run_script("12\n")
        self.assertIn("Goodbye", out)

    def test_exit_by_zero(self):
        # 0 at the main menu also exits, as the prompts promise.
        out = self.run_script("0\n")
        self.assertIn("Goodbye", out)

    def test_non_numeric_choice_is_reported(self):
        # Garbage input produces an error message and the loop continues.
        out = self.run_script("abc\n12\n")
        self.assertIn("Error", out)

    def test_out_of_range_choice_is_reported(self):
        out = self.run_script("99\n12\n")
        self.assertIn("Error", out)


class TestCreateRecords(ControllerTestCase):

    def test_create_note(self):
        # Menu 1 -> type 1 (Note) -> content.
        out = self.run_script("1\n1\nBuy milk\n12\n")
        self.assertIn("Record created", out)
        self.assertEqual(len(self.repository), 1)
        self.assertIsInstance(self.repository.all()[0], Note)

    def test_create_task(self):
        # Menu 1 -> type 2 (Task) -> description -> deadline.
        self.run_script("1\n2\nFinish report\n2026-11-20 18:00\n12\n")
        self.assertEqual(len(self.repository), 1)
        self.assertIsInstance(self.repository.all()[0], Task)

    def test_create_event(self):
        # Menu 1 -> type 3 (Event) -> description, start, alarm.
        self.run_script(
            "1\n3\nTeam meeting\n2026-11-20 14:00\n2026-11-20 13:30\n12\n"
        )
        record = self.repository.all()[0]
        self.assertEqual(record.starting_time, "2026-11-20 14:00")

    def test_create_contact(self):
        # Menu 1 -> type 4 (Contact) -> name, address, mobile.
        self.run_script("1\n4\nAlice\nParis\n0123456789\n12\n")
        record = self.repository.all()[0]
        self.assertIsInstance(record, Contact)
        self.assertEqual(record.mobile_number, "0123456789")

    def test_create_with_invalid_timestamp_is_rejected(self):
        # The model validates, so the record never enters the collection.
        out = self.run_script("1\n2\nBad task\nnot-a-date\n12\n")
        self.assertIn("Error", out)
        self.assertEqual(len(self.repository), 0)

    def test_backing_out_of_create_stores_nothing(self):
        # Choosing a type then entering 0 leaves the collection empty.
        self.run_script("1\n1\n0\n12\n")
        self.assertEqual(len(self.repository), 0)

    def test_backing_out_of_type_menu_stores_nothing(self):
        # 0 at the record-type menu returns to the main menu.
        self.run_script("1\n0\n12\n")
        self.assertEqual(len(self.repository), 0)


class TestReadUpdateDelete(ControllerTestCase):

    def test_display_all_when_empty(self):
        out = self.run_script("2\n12\n")
        self.assertIn("No records", out)

    def test_display_all_shows_stored_record(self):
        self.repository.add(Note("visible"))
        out = self.run_script("2\n12\n")
        self.assertIn("visible", out)

    def test_display_one_by_id(self):
        note = self.repository.add(Note("findable"))
        out = self.run_script(f"3\n{note.pir_id}\n12\n")
        self.assertIn("findable", out)

    def test_display_one_unknown_id(self):
        out = self.run_script("3\nnosuchid\n12\n")
        self.assertIn("Error", out)

    def test_modify_updates_a_field(self):
        note = self.repository.add(Note("before"))
        # Menu 5 -> id -> field 1 -> new value.
        self.run_script(f"5\n{note.pir_id}\n1\nafter\n12\n")
        self.assertEqual(self.repository.all()[0].content, "after")

    def test_modify_unknown_id(self):
        out = self.run_script("5\nnosuchid\n12\n")
        self.assertIn("Error", out)

    def test_modify_reports_a_field_the_record_does_not_have(self):
        # The field menu only offers record.FIELDS, so this cannot be provoked
        # through the prompts; drive the same handler with a repository whose
        # update() refuses the field, which is what PIR.set_field raises for a
        # field the record does not carry. InvalidFieldError is a sibling of
        # ValidationError under PIMError, so a handler that catches only
        # ValidationError lets it escape as a traceback.
        note = Note("before")

        class FieldRejectingRepository(PIMRepository):
            def update(self, pir_id, field, value):
                raise InvalidFieldError(
                    f"{self.get(pir_id).TYPE_NAME} has no field {field!r}"
                )

        rejecting = FieldRejectingRepository()
        rejecting.add(note)
        self.controller = AppController(repository=rejecting, view=self.view)

        out = self.run_script(f"5\n{note.pir_id}\n1\nafter\n12\n")
        self.assertIn("Error", out)
        self.assertIn("has no field", out)
        self.assertEqual(rejecting.all()[0].content, "before")

    def test_delete_removes_record(self):
        note = self.repository.add(Note("doomed"))
        self.run_script(f"4\n{note.pir_id}\n12\n")
        self.assertEqual(len(self.repository), 0)

    def test_delete_unknown_id(self):
        out = self.run_script("4\nnosuchid\n12\n")
        self.assertIn("Error", out)


class TestSearch(ControllerTestCase):

    def setUp(self):
        super().setUp()
        self.note = self.repository.add(Note("buy milk"))
        self.task = self.repository.add(Task("finish report", "2026-11-20 18:00"))
        self.contact = self.repository.add(Contact("Alice", "Paris", "0123456789"))

    def test_search_by_type(self):
        # Menu 6 -> type 2 (Task).
        out = self.run_script("6\n2\n12\n")
        self.assertIn("finish report", out)
        self.assertNotIn("buy milk", out)

    def test_search_by_text(self):
        # Menu 7 -> field 1 (content) -> keyword.
        out = self.run_script("7\n1\nmilk\n12\n")
        self.assertIn("buy milk", out)

    def test_search_by_text_miss(self):
        out = self.run_script("7\n1\nnothing\n12\n")
        self.assertIn("No matching records", out)

    def test_search_by_time(self):
        # Menu 8 -> field 1 (deadline) -> comparison 1 (before) -> timestamp.
        out = self.run_script("8\n1\n1\n2026-12-01 00:00\n12\n")
        self.assertIn("finish report", out)

    def test_search_by_time_rejects_bad_timestamp(self):
        out = self.run_script("8\n1\n1\nnot-a-date\n12\n")
        self.assertIn("Error", out)

    def test_logical_search_and(self):
        # Menu 9 -> 2 (AND) -> first: Single test, Record type, Task
        #                     -> second: Single test, Text field, description, "report"
        out = self.run_script("9\n2\n1\n1\n2\n1\n2\n2\nreport\n12\n")
        self.assertIn("finish report", out)
        self.assertNotIn("buy milk", out)

    def test_logical_search_not(self):
        # Menu 9 -> 4 (NOT) -> Single test -> Record type -> Note.
        # The result is every record that is not a note.
        out = self.run_script("9\n4\n1\n1\n1\n12\n")
        self.assertIn("Criterion", out)
        self.assertIn("finish report", out)
        self.assertNotIn("buy milk", out)

    def test_logical_search_backs_out(self):
        # Backing out of the criterion builder returns without searching.
        self.run_script("9\n0\n12\n")
        self.assertEqual(len(self.repository), 3)

    def test_logical_search_reports_an_empty_keyword(self):
        # Menu 9 used to abandon silently; an empty keyword is invalid input and
        # must be reported, the way menu 7 already does.
        # 9 -> Single test -> Text field -> content -> empty -> back out
        out = self.run_script("9\n1\n2\n1\n\n0\n0\n12\n")
        self.assertIn("Error:", out)
        self.assertIn("must not be empty", out)


class TestPersistence(ControllerTestCase):

    def setUp(self):
        super().setUp()
        self.path = "test_controller_records.pim"

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_save_reports_path(self):
        self.repository.add(Note("saved"))
        out = self.run_script(f"10\n{self.path}\n12\n")
        self.assertIn("saved to", out.lower())
        self.assertTrue(os.path.exists(self.path))

    def test_load_restores_records(self):
        # Save a file with the storage layer, then load it through the menu.
        self.repository.add(Note("travelling"))
        Storage().save(self.repository.all(), self.path)

        fresh = PIMRepository()
        controller = AppController(repository=fresh, view=ConsoleView())
        sys.stdin = io.StringIO(f"11\n{self.path}\n12\n")
        with redirect_stdout(io.StringIO()):
            controller.run()
        self.assertEqual(len(fresh), 1)
        self.assertEqual(fresh.all()[0].content, "travelling")

    def test_load_with_records_asks_before_replacing(self):
        # Unsaved records are announced before a load replaces them.
        self.repository.add(Note("unsaved precious"))
        Storage().save([Note("from disk")], self.path)
        out = self.run_script(f"11\n{self.path}\ny\n12\n")
        self.assertIn("replace", out.lower())
        self.assertEqual(len(self.repository), 1)
        self.assertEqual(self.repository.all()[0].content, "from disk")

    def test_load_declined_keeps_current_records(self):
        # Saying no to the confirm leaves memory exactly as it was.
        self.repository.add(Note("unsaved precious"))
        Storage().save([Note("from disk")], self.path)
        out = self.run_script(f"11\n{self.path}\nn\n12\n")
        self.assertIn("cancelled", out.lower())
        self.assertEqual(self.repository.all()[0].content, "unsaved precious")

    def test_load_with_empty_memory_does_not_confirm(self):
        # Nothing to lose, so no prompt is shown.
        Storage().save([Note("from disk")], self.path)
        out = self.run_script(f"11\n{self.path}\n12\n")
        self.assertNotIn("Continue", out)
        self.assertEqual(len(self.repository), 1)

    def test_load_empty_filename_is_reported(self):
        out = self.run_script("11\n\n12\n")
        self.assertIn("Error", out)

    def test_save_empty_filename_is_reported(self):
        out = self.run_script("10\n\n12\n")
        self.assertIn("Error", out)
        self.assertFalse(os.path.exists(self.path))

    def test_load_missing_file(self):
        out = self.run_script("11\nabsent_file\n12\n")
        self.assertIn("Error", out)


class TestDebugMode(ControllerTestCase):
    """The --debug trace: stderr only, stdout untouched."""

    def test_debug_logs_actions_to_stderr(self):
        # With debug on, every dispatched action is traced to stderr.
        from contextlib import redirect_stderr

        self.controller.debug = True
        sys.stdin = io.StringIO("2\n12\n")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            self.controller.run()
        self.assertIn("[debug] action=display_all", err.getvalue())

    def test_no_debug_by_default(self):
        # Default controllers do not trace anything.
        sys.stdin = io.StringIO("2\n12\n")
        err = io.StringIO()
        from contextlib import redirect_stderr
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            self.controller.run()
        self.assertEqual(err.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
