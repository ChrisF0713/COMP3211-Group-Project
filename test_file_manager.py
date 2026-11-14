
import unittest
import os

from file_manager import FileManager
from model.note import Note
from model.task import Task
from model.event import Event
from model.contact import Contact


class TestFileManager(unittest.TestCase):

    def setUp(self):
        self.filename = "test_records.pim"

        self.records = [
            Note("Complete assignment"),
            Task("Submit project", "2026-11-20 18:00"),
            Event(
                "Group meeting",
                "2026-11-20 14:00",
                "2026-11-20 13:30"
            ),
            Contact("Alice", "Paris", "0123456789")
        ]

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_save_records(self):
        FileManager.save_records(self.records, self.filename)

        self.assertTrue(os.path.exists(self.filename))

    def test_load_records(self):
        FileManager.save_records(self.records, self.filename)

        loaded_records = FileManager.load_records(self.filename)

        self.assertEqual(len(loaded_records), 4)

    def test_loaded_record_types(self):
        FileManager.save_records(self.records, self.filename)

        loaded_records = FileManager.load_records(self.filename)

        self.assertIsInstance(loaded_records[0], Note)
        self.assertIsInstance(loaded_records[1], Task)
        self.assertIsInstance(loaded_records[2], Event)
        self.assertIsInstance(loaded_records[3], Contact)

    def test_record_ids_are_preserved(self):
        FileManager.save_records(self.records, self.filename)

        loaded_records = FileManager.load_records(self.filename)

        for original, loaded in zip(self.records, loaded_records):
            self.assertEqual(original.pir_id, loaded.pir_id)

    def test_record_data_is_preserved(self):
        FileManager.save_records(self.records, self.filename)

        loaded_records = FileManager.load_records(self.filename)

        self.assertEqual(
            loaded_records[0].content,
            self.records[0].content
        )
        self.assertEqual(
            loaded_records[1].deadline,
            self.records[1].deadline
        )
        self.assertEqual(
            loaded_records[2].starting_time,
            self.records[2].starting_time
        )
        self.assertEqual(
            loaded_records[3].mobile_number,
            self.records[3].mobile_number
        )


if __name__ == "__main__":
    unittest.main()
