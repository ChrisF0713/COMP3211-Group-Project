import unittest

from pim_manager import PIMManager
from model.note import Note
from model.task import Task
from model.event import Event
from model.contact import Contact


class TestPIMManager(unittest.TestCase):

    def setUp(self):
        self.manager = PIMManager()

        self.note = Note("Complete assignment")
        self.task = Task("Submit project", "2026-11-20 18:00")
        self.event = Event(
            "Group meeting",
            "2026-11-20 14:00",
            "2026-11-20 13:30"
        )
        self.contact = Contact(
            "Alice",
            "Paris",
            "0123456789"
        )

        self.manager.add_record(self.note)
        self.manager.add_record(self.task)
        self.manager.add_record(self.event)
        self.manager.add_record(self.contact)

    def test_add_record(self):
        self.assertEqual(len(self.manager.records), 4)

    def test_find_record(self):
        result = self.manager.find_record(self.note.pir_id)
        self.assertEqual(result, self.note)

    def test_delete_record(self):
        result = self.manager.delete_record(self.note.pir_id)

        self.assertTrue(result)
        self.assertEqual(len(self.manager.records), 3)

    def test_modify_record(self):
        result = self.manager.modify_record(
            self.note.pir_id,
            "content",
            "Finish assignment"
        )

        self.assertTrue(result)
        self.assertEqual(self.note.content, "Finish assignment")

    def test_search_by_type(self):
        results = self.manager.search_by_type("Note")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.note)

    def test_search_by_field(self):
        results = self.manager.search_by_field(
            "name",
            "Alice"
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.contact)

    def test_search_by_time(self):
        results = self.manager.search_by_time(
            "deadline",
            "before",
            "2026-11-21 00:00"
        )

        self.assertIn(self.task, results)

    def test_combine_search_results(self):
        notes = self.manager.search_by_type("Note")
        contacts = self.manager.search_by_type("Contact")

        results = self.manager.combine_search_results(
            "OR", notes, contacts
        )

        self.assertEqual(len(results), 2)


if __name__ == "__main__":
    unittest.main()