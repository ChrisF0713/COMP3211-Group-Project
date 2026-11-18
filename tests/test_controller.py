"""Tests for the controller, driven with scripted input.

Run from the project root:

    python -m unittest discover -s tests -t .
"""

import io
import os
import re
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

from controller import AppController
from model import (
    Contact,
    Event,
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
        # Menu 9 exits cleanly.
        out = self.run_script("9\n")
        self.assertIn("Goodbye", out)

    def test_exit_by_zero(self):
        # 0 at the main menu also exits, as the prompts promise.
        out = self.run_script("0\n")
        self.assertIn("Goodbye", out)

    def test_non_numeric_choice_is_reported(self):
        # Garbage input produces an error message and the loop continues.
        out = self.run_script("abc\n9\n")
        self.assertIn("Error", out)

    def test_out_of_range_choice_is_reported(self):
        out = self.run_script("99\n9\n")
        self.assertIn("Error", out)


class TestCreateRecords(ControllerTestCase):

    def test_create_note(self):
        # Menu 1 -> type 1 (Note) -> content.
        out = self.run_script("1\n1\nBuy milk\n9\n")
        self.assertIn("Record created", out)
        self.assertEqual(len(self.repository), 1)
        self.assertIsInstance(self.repository.all()[0], Note)

    def test_create_task(self):
        # Menu 1 -> type 2 (Task) -> description -> deadline.
        self.run_script("1\n2\nFinish report\n2026-11-20 18:00\n9\n")
        self.assertEqual(len(self.repository), 1)
        self.assertIsInstance(self.repository.all()[0], Task)

    def test_create_event(self):
        # Menu 1 -> type 3 (Event) -> description, start, alarm.
        self.run_script(
            "1\n3\nTeam meeting\n2026-11-20 14:00\n2026-11-20 13:30\n9\n"
        )
        record = self.repository.all()[0]
        self.assertEqual(record.starting_time, "2026-11-20 14:00")

    def test_create_event_reasks_an_alarm_after_the_start(self):
        # The alarm must fall before the start. A later one is reported and only
        # that field is asked again, keeping the description and start.
        out = self.run_script(
            "1\n3\nTeam meeting\n2026-11-20 14:00\n2026-11-20 15:00\n"
            "2026-11-20 13:30\n9\n"
        )
        self.assertIn("Error", out)
        self.assertIn("earlier than starting_time", out)
        self.assertIn("Record created", out)
        self.assertEqual(self.repository.all()[0].alarm, "2026-11-20 13:30")

    def test_create_contact(self):
        # Menu 1 -> type 4 (Contact) -> name, address, mobile.
        self.run_script("1\n4\nAlice\nParis\n0123456789\n9\n")
        record = self.repository.all()[0]
        self.assertIsInstance(record, Contact)
        self.assertEqual(record.mobile_number, "0123456789")

    def test_create_contact_reasks_a_bad_mobile_number(self):
        # A number with letters is rejected, then the same field is asked again.
        out = self.run_script("1\n4\nAlice\nParis\n51114kkk\n0123 4567\n9\n")
        self.assertIn("Error", out)
        self.assertIn("mobile_number", out)
        self.assertIn("Record created", out)
        self.assertEqual(self.repository.all()[0].mobile_number, "0123 4567")

    def test_create_reasks_after_a_bad_timestamp(self):
        # A rejected value is reported and the same field is asked again, so the
        # description already typed is not thrown away.
        out = self.run_script(
            "1\n2\nBad task\nnot-a-date\n2026-11-20 18:00\n9\n"
        )
        self.assertIn("Error", out)
        self.assertIn("Record created", out)
        self.assertEqual(len(self.repository), 1)
        self.assertEqual(self.repository.all()[0].deadline, "2026-11-20 18:00")

    def test_create_stores_nothing_when_the_user_backs_out(self):
        # 0 at a field prompt abandons the record.
        self.run_script("1\n2\nBad task\n0\n9\n")
        self.assertEqual(len(self.repository), 0)

    def test_backing_out_of_create_stores_nothing(self):
        # Choosing a type then entering 0 leaves the collection empty.
        self.run_script("1\n1\n0\n9\n")
        self.assertEqual(len(self.repository), 0)

    def test_backing_out_of_type_menu_stores_nothing(self):
        # 0 at the record-type menu returns to the main menu.
        self.run_script("1\n0\n9\n")
        self.assertEqual(len(self.repository), 0)


class TestReadUpdateDelete(ControllerTestCase):

    def test_display_all_when_empty(self):
        out = self.run_script("2\n9\n")
        self.assertIn("No records", out)

    def test_display_all_shows_stored_record(self):
        self.repository.add(Note("visible"))
        out = self.run_script("2\n9\n")
        self.assertIn("visible", out)

    def test_display_one_by_id(self):
        note = self.repository.add(Note("findable"))
        out = self.run_script(f"3\n{note.pir_id}\n9\n")
        self.assertIn("findable", out)

    def test_display_one_unknown_id(self):
        out = self.run_script("3\nnosuchid\n9\n")
        self.assertIn("Error", out)

    def test_modify_updates_a_field(self):
        note = self.repository.add(Note("before"))
        # Menu 4 -> id -> field 1 -> new value.
        self.run_script(f"4\n{note.pir_id}\n1\nafter\n9\n")
        self.assertEqual(self.repository.all()[0].content, "after")

    def test_modify_unknown_id(self):
        out = self.run_script("4\nnosuchid\n9\n")
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

        out = self.run_script(f"4\n{note.pir_id}\n1\nafter\n9\n")
        self.assertIn("Error", out)
        self.assertIn("has no field", out)
        self.assertEqual(rejecting.all()[0].content, "before")

    def test_modify_reasks_after_a_bad_value(self):
        # A rejected timestamp is re-asked on the same field.
        task = Task("orig", "2026-11-20 18:00")
        self.repository.add(task)
        out = self.run_script(
            f"4\n{task.pir_id}\n2\nnot-a-date\n2026-12-01 09:00\n9\n"
        )
        self.assertIn("Error", out)
        self.assertIn("Record updated", out)
        self.assertEqual(self.repository.get(task.pir_id).deadline, "2026-12-01 09:00")

    def test_modify_returns_to_the_field_list_on_back_out(self):
        # 0 at the value prompt goes back to the field list, not the main menu,
        # and 0 again leaves the record untouched.
        task = Task("orig", "2026-11-20 18:00")
        self.repository.add(task)
        self.run_script(f"4\n{task.pir_id}\n2\n0\n0\n9\n")
        self.assertEqual(self.repository.get(task.pir_id).deadline, "2026-11-20 18:00")

    def test_delete_removes_record(self):
        note = self.repository.add(Note("doomed"))
        self.run_script(f"5\n{note.pir_id}\n9\n")
        self.assertEqual(len(self.repository), 0)

    def test_delete_unknown_id(self):
        out = self.run_script("5\nnosuchid\n9\n")
        self.assertIn("Error", out)


class TestSearch(ControllerTestCase):

    def setUp(self):
        super().setUp()
        self.note = self.repository.add(Note("buy milk"))
        self.task = self.repository.add(Task("finish report", "2026-11-20 18:00"))
        self.contact = self.repository.add(Contact("Alice", "Paris", "0123456789"))

    def test_search_by_type(self):
        # Menu 6 then a type test.
        out = self.run_script("6\ntype = Task\n0\n9\n")
        self.assertIn("finish report", out)
        self.assertNotIn("buy milk", out)

    def test_search_by_text(self):
        # Menu 6 then a text test on one named field.
        out = self.run_script("6\ncontent contains milk\n0\n9\n")
        self.assertIn("buy milk", out)

    def test_search_bare_word_matches_any_text_field(self):
        # A bare word searches all five text fields at once.
        out = self.run_script("6\nmilk\n0\n9\n")
        self.assertIn("buy milk", out)

    def test_search_by_text_miss(self):
        out = self.run_script("6\ncontent contains nothing\n0\n9\n")
        self.assertIn("No matching records", out)

    def test_search_by_time(self):
        # Menu 6 then a time comparison.
        out = self.run_script("6\ndeadline < 2026-12-01 00:00\n0\n9\n")
        self.assertIn("finish report", out)

    def test_search_by_time_rejects_bad_timestamp(self):
        out = self.run_script("6\ndeadline < not-a-date\n0\n9\n")
        self.assertIn("Error", out)

    def test_help_lists_the_real_owner_of_each_field(self):
        # The screen claims which record types carry which field. That claim was
        # once wrong - starting_time and alarm were listed as Task fields too -
        # so it is checked against the classes themselves.
        out = self.run_script("6\n0\n9\n")
        owners = {
            field: [
                cls.TYPE_NAME
                for cls in (Note, Task, Event, Contact)
                if field in cls.FIELDS
            ]
            for field in ("content", "description", "deadline",
                          "starting_time", "alarm")
        }

        for field, types in owners.items():
            with self.subTest(field=field):
                # The help must not attach a field to a type that lacks it.
                for other in ("Note", "Task", "Event", "Contact"):
                    if other in types:
                        continue
                    # A wrong pairing shows up as the field and the foreign type
                    # on the same help line.
                    pattern = rf"{field}[^\n]*{other}|{other}[^\n]*{field}"
                    self.assertIsNone(
                        re.search(pattern, out),
                        f"help pairs {field} with {other}, but {other} has no {field}",
                    )

    def test_starting_time_never_matches_a_task(self):
        # An event carries starting_time and a task does not, so a test on that
        # field must never return the task. This is the mix-up users reported.
        task = self.repository.add(Task("submit report", "2026-11-20 18:00"))
        event = self.repository.add(
            Event("team meeting", "2026-11-20 14:00", "2026-11-20 13:30")
        )

        out = self.run_script("6\nstarting_time = 2026-11-20 14:00\n0\n9\n")
        self.assertIn(event.pir_id, out)
        self.assertNotIn(task.pir_id, out)

    def test_deadline_never_matches_an_event(self):
        # The mirror image: deadline belongs to a task only.
        task = self.repository.add(Task("submit report", "2026-11-20 18:00"))
        event = self.repository.add(
            Event("team meeting", "2026-11-20 14:00", "2026-11-20 13:30")
        )

        out = self.run_script("6\ndeadline = 2026-11-20 18:00\n0\n9\n")
        self.assertIn(task.pir_id, out)
        self.assertNotIn(event.pir_id, out)

    def test_logical_search_and(self):
        # Two tests joined by &&.
        out = self.run_script('6\ntype = Task && description contains report\n0\n9\n')
        self.assertIn("finish report", out)
        self.assertNotIn("buy milk", out)

    def test_logical_search_not(self):
        # Negation: everything that is not a note.
        out = self.run_script("6\n!type = Note\n0\n9\n")
        self.assertIn("Criterion", out)
        self.assertIn("finish report", out)
        self.assertNotIn("buy milk", out)

    def test_search_backs_out(self):
        # 0 at the prompt searches nothing.
        out = self.run_script("6\n0\n9\n")
        self.assertNotIn("Criterion", out)
        self.assertEqual(len(self.repository), 3)

    def test_search_keeps_the_prompt_until_zero(self):
        # Several searches run in one visit; only 0 returns to the main menu.
        out = self.run_script("6\nmilk\nreport\n0\n9\n")
        self.assertIn("buy milk", out)
        self.assertIn("finish report", out)
        self.assertEqual(out.count("Criterion:"), 2)

    def test_search_stays_after_a_typo(self):
        # A malformed expression is reported, and the prompt comes back rather
        # than dropping the user to the main menu.
        out = self.run_script("6\ntype = &&\nmilk\n0\n9\n")
        self.assertIn("Error:", out)
        self.assertIn("buy milk", out)

    def test_search_reports_an_empty_expression(self):
        # An empty expression is invalid input and must be reported.
        out = self.run_script("6\n\n0\n9\n")
        self.assertIn("Error:", out)
        self.assertIn("must not be empty", out)

    def test_search_reports_a_malformed_expression(self):
        # A dangling operator must produce an error, not a crash.
        out = self.run_script("6\ntype = Task &&\n0\n9\n")
        self.assertIn("Error:", out)
        self.assertNotIn("Traceback", out)


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
        out = self.run_script(f"7\n{self.path}\n9\n")
        self.assertIn("saved to", out.lower())
        self.assertTrue(os.path.exists(self.path))

    def test_load_restores_records(self):
        # Save a file with the storage layer, then load it through the menu.
        self.repository.add(Note("travelling"))
        Storage().save(self.repository.all(), self.path)

        fresh = PIMRepository()
        controller = AppController(repository=fresh, view=ConsoleView())
        sys.stdin = io.StringIO(f"8\n{self.path}\n9\n")
        with redirect_stdout(io.StringIO()):
            controller.run()
        self.assertEqual(len(fresh), 1)
        self.assertEqual(fresh.all()[0].content, "travelling")

    def test_load_with_records_asks_before_replacing(self):
        # Unsaved records are announced before a load replaces them.
        self.repository.add(Note("unsaved precious"))
        Storage().save([Note("from disk")], self.path)
        out = self.run_script(f"8\n{self.path}\ny\n9\n")
        self.assertIn("replace", out.lower())
        self.assertEqual(len(self.repository), 1)
        self.assertEqual(self.repository.all()[0].content, "from disk")

    def test_load_declined_keeps_current_records(self):
        # Saying no to the confirm leaves memory exactly as it was.
        self.repository.add(Note("unsaved precious"))
        Storage().save([Note("from disk")], self.path)
        out = self.run_script(f"8\n{self.path}\nn\n0\n9\n")
        self.assertIn("cancelled", out.lower())
        self.assertEqual(self.repository.all()[0].content, "unsaved precious")

    def test_load_with_empty_memory_does_not_confirm(self):
        # Nothing to lose, so no prompt is shown.
        Storage().save([Note("from disk")], self.path)
        out = self.run_script(f"8\n{self.path}\n9\n")
        self.assertNotIn("Continue", out)
        self.assertEqual(len(self.repository), 1)

    def test_load_empty_filename_is_reported(self):
        out = self.run_script("8\n\n0\n9\n")
        self.assertIn("Error", out)

    def test_save_empty_filename_is_reported(self):
        out = self.run_script("7\n\n0\n9\n")
        self.assertIn("Error", out)
        self.assertFalse(os.path.exists(self.path))

    def test_load_missing_file(self):
        out = self.run_script("8\nabsent_file\n0\n9\n")
        self.assertIn("Error", out)

    def test_save_rejects_a_non_pim_extension(self):
        # A .txt name is refused with a message naming the accepted extension,
        # rather than being quietly redirected to a .pim file.
        out = self.run_script(f"7\nrecords.txt\n{self.path}\n9\n")
        self.assertIn("Error", out)
        self.assertIn(".pim", out)
        self.assertIn("saved to", out.lower())

    def test_load_rejects_a_non_pim_extension(self):
        out = self.run_script("8\nrecords.txt\nn\n0\n9\n")
        self.assertIn("Error", out)
        self.assertIn(".pim", out)

    def test_load_stays_after_a_missing_file(self):
        # A missing file is reported and the prompt comes back, so a mistyped
        # name does not cost a trip through the main menu.
        Storage().save([Note("from disk")], self.path)
        out = self.run_script(f"8\nabsent\nn\n{self.path}\ny\n9\n")
        self.assertIn("Error", out)
        self.assertIn("loaded", out.lower())
        self.assertEqual(self.repository.all()[0].content, "from disk")

    def test_save_stays_after_a_failed_write(self):
        # A path that cannot be written is reported, then the prompt returns.
        out = self.run_script(f"7\nno_such_dir/x\n{self.path}\n9\n")
        self.assertIn("Error", out)
        self.assertIn("saved to", out.lower())
        self.assertTrue(os.path.exists(self.path))


class TestDebugMode(ControllerTestCase):
    """The --debug trace: stderr only, stdout untouched."""

    def test_debug_logs_actions_to_stderr(self):
        # With debug on, every dispatched action is traced to stderr.
        self.controller.debug = True
        sys.stdin = io.StringIO("2\n9\n")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            self.controller.run()
        self.assertIn("[debug] action=display_all", err.getvalue())

    def test_no_debug_by_default(self):
        # Default controllers do not trace anything.
        sys.stdin = io.StringIO("2\n9\n")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            self.controller.run()
        self.assertEqual(err.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
