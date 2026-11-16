"""Unit tests for the model layer.

Run from the project root:

    python -m unittest discover -s tests -t .
"""

import os
import unittest

from model import (
    And,
    Contact,
    Event,
    Note,
    Not,
    Or,
    PIMError,
    PIMRepository,
    RecordNotFoundError,
    Storage,
    Task,
    TEXT_FIELDS,
    TIME_FIELDS,
    TextContains,
    TimeCompare,
    TypeIs,
    ValidationError,
    FILE_EXTENSION,
    TIMESTAMP_FORMAT,
    parse_timestamp,
)


class TestTimestampParsing(unittest.TestCase):
    """One accepted time format, validated at the boundary."""

    def test_accepts_the_documented_format(self):
        # Expect a datetime for the format the user manual documents.
        moment = parse_timestamp("2026-11-20 18:00")
        self.assertEqual(moment.year, 2026)
        self.assertEqual(moment.hour, 18)

    def test_rejects_other_shapes(self):
        # Any other layout is a validation error, not a silent misparse.
        for bad in ("2026/11/20 18:00", "20-11-2026", "2026-11-20", "18:00"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    parse_timestamp(bad)

    def test_rejects_empty_and_non_string(self):
        # Blank and non-string inputs are rejected rather than coerced.
        for bad in ("", "   ", None, 20261120):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    parse_timestamp(bad)

    def test_surrounding_whitespace_is_tolerated(self):
        # Leading and trailing spaces are stripped before parsing.
        self.assertEqual(
            parse_timestamp("  2026-11-20 18:00  "),
            parse_timestamp("2026-11-20 18:00"),
        )

    def test_rejects_unpadded_fields(self):
        # strptime would accept these, but the documented format needs the
        # zero padding, and the grammar in the SRS cannot derive them.
        for bad in ("2026-1-5 9:00", "2026-11-5 18:00", "2026-1-05 18:00"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    parse_timestamp(bad)


class TestPIRBase(unittest.TestCase):

    def test_abstract_base_cannot_be_instantiated(self):
        # PIR declares get_details abstract, so it must refuse construction.
        from model import PIR

        with self.assertRaises(TypeError):
            PIR()

    def test_identity_is_generated_and_unique(self):
        # Each record gets its own 8-character identifier.
        ids = {Note("a").pir_id for _ in range(50)}
        self.assertEqual(len(ids), 50)
        self.assertTrue(all(len(i) == 8 for i in ids))

    def test_equality_is_by_type_and_id(self):
        # Two records are equal only when both type and ID agree.
        note = Note("x")
        same = Note("different text")
        same.pir_id = note.pir_id
        self.assertEqual(note, same)
        self.assertNotEqual(note, Task("x", "2026-11-20 18:00"))

    def test_records_are_hashable(self):
        # Identity-based hashing lets records go into a set.
        note = Note("x")
        self.assertEqual(len({note, note}), 1)

    def test_get_field_returns_none_for_absent_field(self):
        # A Note has no deadline, so the generic accessor reports None.
        self.assertIsNone(Note("x").get_field("deadline"))

    def test_set_field_rejects_absent_field(self):
        # Writing a field the type does not have is an error.
        from model import InvalidFieldError

        with self.assertRaises(InvalidFieldError):
            Note("x").set_field("deadline", "2026-11-20 18:00")

    def test_set_field_updates_known_field(self):
        # A known field is written through the same validated path.
        note = Note("old")
        note.set_field("content", "new")
        self.assertEqual(note.content, "new")

    def test_to_dict_and_from_dict_round_trip(self):
        # Serialising then rebuilding must preserve type, ID and every field.
        original = Task("submit", "2026-11-20 18:00")
        rebuilt = Task.from_dict(original.to_dict())
        self.assertEqual(rebuilt.pir_id, original.pir_id)
        self.assertEqual(rebuilt.description, original.description)
        self.assertEqual(rebuilt.deadline, original.deadline)

    def test_from_dict_reports_missing_field(self):
        # A record object lacking a required field is rejected clearly.
        with self.assertRaises(ValidationError):
            Task.from_dict({"type": "Task", "pir_id": "abcd1234"})

    def test_from_dict_rejects_non_dict(self):
        # Feeding a list or scalar where an object is expected is an error.
        with self.assertRaises(ValidationError):
            Note.from_dict(["not", "a", "dict"])

    def test_comparison_with_non_record_returns_not_implemented(self):
        # Comparing a record to an unrelated object is not a record equality
        # claim, so Python's default comparison wins.
        self.assertFalse(Note("x") == "not a record")
        self.assertNotEqual(Note("x"), "not a record")

    def test_repr_is_readable(self):
        # repr() names the type and the ID, for debugging.
        note = Note("x")
        rendered = repr(note)
        self.assertIn("Note", rendered)
        self.assertIn(note.pir_id, rendered)


class TestRecordTypes(unittest.TestCase):
    """Each concrete type stores, validates and describes its own fields."""

    def test_note_fields(self):
        note = Note("buy milk")
        self.assertEqual(note.content, "buy milk")
        self.assertIn("Note", note.TYPE_NAME)
        self.assertIn("buy milk", note.get_details())

    def test_note_rejects_empty_content(self):
        # Blank text is not a usable note.
        with self.assertRaises(ValidationError):
            Note("   ")

    def test_task_fields_and_details(self):
        task = Task("submit", "2026-11-20 18:00")
        self.assertEqual(task.description, "submit")
        self.assertEqual(task.deadline, "2026-11-20 18:00")
        details = task.get_details()
        for fragment in ("Task", task.pir_id, "submit", "2026-11-20 18:00"):
            self.assertIn(fragment, details)

    def test_task_rejects_bad_deadline(self):
        # The deadline is validated at construction, not at search time.
        with self.assertRaises(ValidationError):
            Task("submit", "tomorrow")

    def test_event_fields_and_details(self):
        event = Event("meeting", "2026-11-20 14:00", "2026-11-20 13:30")
        self.assertEqual(event.starting_time, "2026-11-20 14:00")
        self.assertEqual(event.alarm, "2026-11-20 13:30")
        details = event.get_details()
        for fragment in ("Event", "meeting", "2026-11-20 14:00"):
            self.assertIn(fragment, details)

    def test_event_rejects_bad_alarm(self):
        # Both time fields are validated.
        with self.assertRaises(ValidationError):
            Event("meeting", "2026-11-20 14:00", "soon")

    def test_contact_fields_and_details(self):
        contact = Contact("Alice", "Paris", "0123456789")
        self.assertEqual(contact.name, "Alice")
        self.assertEqual(contact.address, "Paris")
        self.assertEqual(contact.mobile_number, "0123456789")
        details = contact.get_details()
        for fragment in ("Contact", "Alice", "Paris", "0123456789"):
            self.assertIn(fragment, details)

    def test_contact_keeps_leading_zero(self):
        # The mobile number is a string, so the zero must survive.
        self.assertTrue(Contact("A", "B", "0123456789").mobile_number.startswith("0"))

    def test_contact_rejects_empty_name(self):
        with self.assertRaises(ValidationError):
            Contact("  ", "Paris", "0123456789")


class TestCriteria(unittest.TestCase):
    """The search criteria, tested leaf by leaf and then composed."""

    def setUp(self):
        self.note = Note("buy milk today")
        self.task = Task("finish report", "2026-11-20 18:00")
        self.early = Task("early task", "2026-11-01 09:00")
        self.late = Task("late task", "2026-12-01 09:00")
        self.event = Event("team meeting", "2026-11-20 14:00", "2026-11-20 13:30")
        self.contact = Contact("Alice", "Hong Kong", "0123456789")

    # -- leaves ----------------------------------------------------------

    def test_text_contains_is_case_insensitive(self):
        # Matching ignores case on both the stored value and the keyword.
        self.assertTrue(TextContains("content", "MILK").matches(self.note))
        self.assertFalse(TextContains("content", "coffee").matches(self.note))

    def test_text_contains_skips_records_without_the_field(self):
        # A record type with no such field simply does not match.
        self.assertFalse(TextContains("content", "milk").matches(self.task))

    def test_text_contains_rejects_unknown_field(self):
        # Only documented text fields are searchable.
        with self.assertRaises(ValidationError):
            TextContains("pir_id", "abc")

    def test_text_contains_rejects_empty_keyword(self):
        with self.assertRaises(ValidationError):
            TextContains("content", "  ")

    def test_time_compare_before(self):
        # 'before' is strict, so the boundary record is excluded.
        test = TimeCompare("deadline", "before", "2026-11-20 18:00")
        self.assertTrue(test.matches(self.early))
        self.assertFalse(test.matches(self.task))

    def test_time_compare_after(self):
        # 'after' is strict on the other side.
        test = TimeCompare("deadline", "after", "2026-11-20 18:00")
        self.assertTrue(test.matches(self.late))
        self.assertFalse(test.matches(self.task))

    def test_time_compare_equal_is_inclusive(self):
        # 'equal' matches the exact instant.
        test = TimeCompare("deadline", "equal", "2026-11-20 18:00")
        self.assertTrue(test.matches(self.task))
        self.assertFalse(test.matches(self.early))

    def test_time_compare_skips_records_without_the_field(self):
        # A Note has no deadline, so it cannot match a deadline test.
        test = TimeCompare("deadline", "before", "2030-01-01 00:00")
        self.assertFalse(test.matches(self.note))

    def test_time_compare_rejects_bad_target_at_construction(self):
        # A malformed target fails once, up front, not per record.
        with self.assertRaises(ValidationError):
            TimeCompare("deadline", "before", "not-a-date")

    def test_time_compare_rejects_unknown_operator(self):
        with self.assertRaises(ValidationError):
            TimeCompare("deadline", "near", "2026-11-20 18:00")

    def test_time_compare_rejects_unknown_field(self):
        with self.assertRaises(ValidationError):
            TimeCompare("content", "before", "2026-11-20 18:00")

    def test_type_is_matches_class(self):
        # Type matching is case-insensitive and ignores unrelated types.
        self.assertTrue(TypeIs("Task").matches(self.task))
        self.assertTrue(TypeIs("task").matches(self.task))
        self.assertFalse(TypeIs("Note").matches(self.task))

    # -- composites ------------------------------------------------------

    def test_and_requires_all_operands(self):
        # Both branches must hold.
        both = And(TypeIs("Task"), TextContains("description", "report"))
        self.assertTrue(both.matches(self.task))
        self.assertFalse(both.matches(self.early))

    def test_or_requires_one_operand(self):
        # Either branch suffices.
        either = Or(TypeIs("Note"), TypeIs("Contact"))
        self.assertTrue(either.matches(self.note))
        self.assertTrue(either.matches(self.contact))
        self.assertFalse(either.matches(self.task))

    def test_not_inverts_its_operand(self):
        # Negation flips the result.
        self.assertFalse(Not(TypeIs("Task")).matches(self.task))
        self.assertTrue(Not(TypeIs("Task")).matches(self.note))

    def test_nesting_is_supported(self):
        # Composite inside a composite, to check deeper nesting.
        criterion = And(
            TypeIs("Task"),
            Not(TextContains("description", "early")),
        )
        self.assertTrue(criterion.matches(self.task))
        self.assertFalse(criterion.matches(self.early))

    def test_three_level_nesting(self):
        # A deeper tree still evaluates correctly.
        criterion = Or(
            And(TypeIs("Task"), TextContains("description", "late")),
            And(TypeIs("Contact"), TextContains("name", "alice")),
        )
        self.assertTrue(criterion.matches(self.late))
        self.assertTrue(criterion.matches(self.contact))
        self.assertFalse(criterion.matches(self.task))

    def test_composite_rejects_no_operands(self):
        # A connective with nothing to connect is a programming error.
        with self.assertRaises(ValidationError):
            And()

    def test_composite_rejects_non_criteria(self):
        # Operands must themselves be criteria.
        with self.assertRaises(ValidationError):
            And(TypeIs("Task"), "not a criterion")

    def test_not_rejects_non_criterion(self):
        with self.assertRaises(ValidationError):
            Not("not a criterion")

    def test_describe_renders_all_operators(self):
        # describe() reconstructs &&, || and ! for display.
        criterion = And(
            TextContains("content", "milk"),
            Or(TypeIs("Task"), Not(TypeIs("Note"))),
        )
        rendered = criterion.describe()
        self.assertIn("&&", rendered)
        self.assertIn("||", rendered)
        self.assertIn("!", rendered)
        self.assertIn("contains", rendered)

    def test_describe_shows_comparison_symbol(self):
        # A time comparison renders as '<', '>' or '='.
        self.assertIn("<", TimeCompare("deadline", "before", "2026-11-20 18:00").describe())
        self.assertIn(">", TimeCompare("deadline", "after", "2026-11-20 18:00").describe())
        self.assertIn("=", TimeCompare("deadline", "equal", "2026-11-20 18:00").describe())

    def test_repr_mentions_the_class(self):
        # repr() names the criterion type.
        self.assertIn("TypeIs", repr(TypeIs("Task")))

    def test_type_is_rejects_empty_name(self):
        with self.assertRaises(ValidationError):
            TypeIs("   ")

    def test_base_criterion_methods_are_abstract(self):
        # The Component base declares both operations; a subclass must supply them.
        from model.criteria import Criterion

        with self.assertRaises(NotImplementedError):
            Criterion().matches(Note("x"))
        with self.assertRaises(NotImplementedError):
            Criterion().describe()

    def test_time_compare_skips_unparseable_stored_value(self):
        # A record whose stored time is not in our format cannot match, and
        # must not crash the search: TimeCompare.matches() reaches its
        # `except ValidationError: return False` branch instead of raising.
        broken = Task("placeholder", "2026-11-20 18:00")
        # Force a bad value past validation to model a hand-edited file; set it
        # on a record that really carries the field, or get_field() returns None
        # and the predicate never reaches the parser at all.
        broken.__dict__["deadline"] = "whenever"
        self.assertEqual(broken.get_field("deadline"), "whenever")
        test = TimeCompare("deadline", "before", "2030-01-01 00:00")
        self.assertFalse(test.matches(broken))


class TestRepository(unittest.TestCase):
    """The collection: add, get, update, delete, search, persistence."""

    def setUp(self):
        self.repository = PIMRepository()
        self.note = Note("a note")
        self.task = Task("a task", "2026-11-20 18:00")

    def test_add_stores_and_returns_record(self):
        returned = self.repository.add(self.note)
        self.assertIs(returned, self.note)
        self.assertEqual(len(self.repository), 1)

    def test_add_rejects_non_record(self):
        # Only PIR instances belong in the collection.
        with self.assertRaises(ValidationError):
            self.repository.add("not a record")

    def test_add_rejects_duplicate_id(self):
        # Two records sharing an ID would make get() ambiguous.
        self.repository.add(self.note)
        clone = Note("different")
        clone.pir_id = self.note.pir_id
        with self.assertRaises(ValidationError):
            self.repository.add(clone)

    def test_get_returns_record(self):
        self.repository.add(self.note)
        self.assertIs(self.repository.get(self.note.pir_id), self.note)

    def test_get_raises_for_unknown_id(self):
        with self.assertRaises(RecordNotFoundError):
            self.repository.get("nope")

    def test_all_preserves_insertion_order(self):
        self.repository.add(self.note)
        self.repository.add(self.task)
        self.assertEqual(self.repository.all(), [self.note, self.task])

    def test_records_property_returns_a_copy(self):
        # Callers must not be able to mutate the store through the property.
        self.repository.add(self.note)
        snapshot = self.repository.records
        snapshot.append(self.task)
        self.assertEqual(len(self.repository), 1)

    def test_update_changes_one_field(self):
        self.repository.add(self.task)
        self.repository.update(self.task.pir_id, "description", "renamed")
        self.assertEqual(self.task.description, "renamed")
        self.assertEqual(self.task.deadline, "2026-11-20 18:00")

    def test_update_rejects_unknown_field_and_leaves_record_intact(self):
        # Validation failure must not half-apply the change.
        self.repository.add(self.note)
        with self.assertRaises(Exception):
            self.repository.update(self.note.pir_id, "deadline", "2026-11-20 18:00")
        self.assertEqual(self.note.content, "a note")

    def test_update_raises_for_unknown_id(self):
        with self.assertRaises(RecordNotFoundError):
            self.repository.update("nope", "content", "x")

    def test_delete_removes_record(self):
        self.repository.add(self.note)
        removed = self.repository.delete(self.note.pir_id)
        self.assertIs(removed, self.note)
        self.assertEqual(len(self.repository), 0)

    def test_delete_raises_for_unknown_id(self):
        with self.assertRaises(RecordNotFoundError):
            self.repository.delete("nope")

    def test_clear_empties_the_collection(self):
        self.repository.add(self.note)
        self.repository.clear()
        self.assertEqual(len(self.repository), 0)

    def test_search_filters_by_criterion(self):
        self.repository.add(self.note)
        self.repository.add(self.task)
        results = self.repository.search(TypeIs("Task"))
        self.assertEqual(results, [self.task])

    def test_search_returns_empty_list_when_nothing_matches(self):
        self.repository.add(self.note)
        self.assertEqual(self.repository.search(TypeIs("Contact")), [])

    def test_search_rejects_non_criterion(self):
        with self.assertRaises(ValidationError):
            self.repository.search("not a criterion")

    def test_iterator_yields_records(self):
        self.repository.add(self.note)
        self.assertEqual(list(self.repository), [self.note])


class TestStorage(unittest.TestCase):
    """The .pim file format: round-trip, extension handling, bad input."""

    def setUp(self):
        self.storage = Storage()
        self.path = "test_storage.pim"

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_extension_is_appended(self):
        # A name without the extension gets one added.
        from model.storage import with_extension

        self.assertEqual(with_extension("records"), "records" + FILE_EXTENSION)
        self.assertEqual(with_extension("records.pim"), "records.pim")

    def test_save_returns_path_used(self):
        path = self.storage.save([Note("x")], "test_storage")
        self.assertTrue(path.endswith(FILE_EXTENSION))
        if os.path.exists(path):
            os.remove(path)

    def test_round_trip_preserves_every_type(self):
        # All four types survive a save/load cycle field for field.
        original = [
            Note("text"),
            Task("desc", "2026-11-20 18:00"),
            Event("meeting", "2026-11-20 14:00", "2026-11-20 13:30"),
            Contact("Alice", "Paris", "0123456789"),
        ]
        self.storage.save(original, self.path)
        loaded = self.storage.load(self.path)
        self.assertEqual([type(r) for r in loaded],
                         [Note, Task, Event, Contact])
        for before, after in zip(original, loaded):
            self.assertEqual(before.pir_id, after.pir_id)
            self.assertEqual(before.to_dict(), after.to_dict())

    def test_empty_collection_round_trips(self):
        self.storage.save([], self.path)
        self.assertEqual(self.storage.load(self.path), [])

    def test_non_ascii_survives(self):
        # The file is UTF-8 with ensure_ascii off.
        self.storage.save([Note("買牛奶")], self.path)
        self.assertEqual(self.storage.load(self.path)[0].content, "買牛奶")

    def test_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.storage.load("definitely_absent.pim")

    def test_corrupt_json_is_reported_as_pim_error(self):
        # A malformed file surfaces as one domain error, not a JSON traceback.
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        with self.assertRaises(PIMError):
            self.storage.load(self.path)

    def test_wrong_top_level_shape_is_rejected(self):
        # The format is a list; an object is not acceptable.
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write('{"type": "Note"}')
        with self.assertRaises(PIMError):
            self.storage.load(self.path)

    def test_non_object_entry_is_rejected(self):
        # Every element of the list must be a record object.
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write('["just a string"]')
        with self.assertRaises(PIMError):
            self.storage.load(self.path)

    def test_save_to_unwritable_path_is_reported(self):
        # An OS-level write failure surfaces as one domain error.
        with self.assertRaises(PIMError):
            self.storage.save([Note("x")], os.path.join("no_such_dir", "a.pim"))

    def test_unknown_type_is_rejected(self):
        # A record type this version does not know is an error.
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write('[{"type": "Alien", "pir_id": "aaaaaaaa"}]')
        with self.assertRaises(PIMError):
            self.storage.load(self.path)

    def test_missing_field_is_rejected(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write('[{"type": "Task", "pir_id": "aaaaaaaa"}]')
        with self.assertRaises(PIMError):
            self.storage.load(self.path)

    def test_invalid_timestamp_in_file_is_rejected(self):
        # A stored record is validated on load, not trusted.
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(
                '[{"type": "Task", "pir_id": "aaaaaaaa",'
                ' "description": "x", "deadline": "whenever"}]'
            )
        with self.assertRaises(PIMError):
            self.storage.load(self.path)

    def test_non_string_field_value_is_rejected(self):
        # Every field is text, so a JSON null or number is a malformed record.
        for payload in (
            '[{"type": "Note", "pir_id": "aaaaaaaa", "content": null}]',
            '[{"type": "Task", "pir_id": "bbbbbbbb", "description": 12345,'
            ' "deadline": "2026-11-20 18:00"}]',
        ):
            with self.subTest(payload=payload):
                with open(self.path, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                with self.assertRaises(PIMError):
                    self.storage.load(self.path)

    def test_non_utf8_file_is_reported_as_pim_error(self):
        # A file that is not UTF-8 is malformed input, not a crash: the error
        # must be a PIMError so the controller can report it.
        with open(self.path, "wb") as handle:
            handle.write(b'[{"type":"Note","pir_id":"aaaaaaaa","content":"\xff\xfe"}]')
        with self.assertRaises(PIMError):
            self.storage.load(self.path)

    def test_unreadable_path_is_reported_as_pim_error(self):
        # The loader distinguishes "no such file" (FileNotFoundError, which the
        # controller turns into `file not found`) from any other OS-level read
        # failure, which must surface as a PIMError instead of a traceback.
        # A directory named like a .pim file fails to open on every platform:
        # PermissionError on Windows, IsADirectoryError elsewhere - both OSError.
        unusual = "test_storage_is_a_directory"
        from model.storage import with_extension

        path = with_extension(unusual)
        os.makedirs(path, exist_ok=True)
        try:
            with self.assertRaises(PIMError) as caught:
                self.storage.load(path)
            self.assertNotIsInstance(caught.exception, FileNotFoundError)
            self.assertIn("could not read", str(caught.exception))
        finally:
            os.rmdir(path)

    def test_duplicate_id_in_file_is_rejected(self):
        # Two records sharing one ID would make get/modify/delete ambiguous,
        # since lookups return the first match.
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(
                '[{"type": "Note", "pir_id": "aaaaaaaa", "content": "one"},'
                ' {"type": "Note", "pir_id": "aaaaaaaa", "content": "two"}]'
            )
        with self.assertRaises(PIMError):
            self.storage.load(self.path)

    def test_unusable_id_in_file_is_rejected(self):
        # A pir_id must be a non-empty string; anything else is malformed.
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write('[{"type": "Note", "pir_id": 42, "content": "x"}]')
        with self.assertRaises(PIMError):
            self.storage.load(self.path)

    def test_repository_load_rejects_duplicate_ids(self):
        # The repository refuses the whole file, so its own records survive.
        repository = PIMRepository()
        repository.add(Note("keep me"))
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(
                '[{"type": "Note", "pir_id": "aaaaaaaa", "content": "one"},'
                ' {"type": "Note", "pir_id": "aaaaaaaa", "content": "two"}]'
            )
        with self.assertRaises(PIMError):
            repository.load(self.path)
        self.assertEqual(len(repository), 1)
        self.assertEqual(repository.all()[0].content, "keep me")

    def test_repository_load_keeps_old_records_when_file_is_bad(self):
        # A failed load must not wipe the collection.
        repository = PIMRepository()
        repository.add(Note("keep me"))
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        with self.assertRaises(PIMError):
            repository.load(self.path)
        self.assertEqual(len(repository), 1)
        self.assertEqual(repository.all()[0].content, "keep me")

    def test_repository_save_and_load_replaces_collection(self):
        repository = PIMRepository()
        repository.add(Note("first"))
        repository.save(self.path)

        other = PIMRepository()
        other.add(Note("will be replaced"))
        other.load(self.path)
        self.assertEqual(len(other), 1)
        self.assertEqual(other.all()[0].content, "first")


if __name__ == "__main__":
    unittest.main()
