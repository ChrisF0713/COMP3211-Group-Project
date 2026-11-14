
import json

from model.note import Note
from model.task import Task
from model.event import Event
from model.contact import Contact


class FileManager:

    @staticmethod
    def save_records(records, filename):
        data = []

        for record in records:
            record_data = {
                "type": type(record).__name__,
                "pir_id": record.pir_id
            }

            if isinstance(record, Note):
                record_data["content"] = record.content

            elif isinstance(record, Task):
                record_data["description"] = record.description
                record_data["deadline"] = record.deadline

            elif isinstance(record, Event):
                record_data["description"] = record.description
                record_data["starting_time"] = record.starting_time
                record_data["alarm"] = record.alarm

            elif isinstance(record, Contact):
                record_data["name"] = record.name
                record_data["address"] = record.address
                record_data["mobile_number"] = record.mobile_number

            data.append(record_data)

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print("Records saved successfully.")

    @staticmethod
    def load_records(filename):
        records = []

        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        for item in data:
            record_type = item["type"]

            if record_type == "Note":
                record = Note(item["content"])

            elif record_type == "Task":
                record = Task(
                    item["description"],
                    item["deadline"]
                )

            elif record_type == "Event":
                record = Event(
                    item["description"],
                    item["starting_time"],
                    item["alarm"]
                )

            elif record_type == "Contact":
                record = Contact(
                    item["name"],
                    item["address"],
                    item["mobile_number"]
                )

            else:
                continue

            # Restore the original ID
            record.pir_id = item["pir_id"]

            records.append(record)

        return records
