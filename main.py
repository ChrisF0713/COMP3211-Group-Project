from datetime import datetime
from model.note import Note
from model.task import Task
from model.event import Event
from model.contact import Contact
from pim_manager import PIMManager
from file_manager import FileManager


RECORD_TYPES = ["Note", "Task", "Event", "Contact"]
SEARCH_FIELDS = [
    "content", "description", "deadline", "starting_time",
    "alarm", "name", "address", "mobile_number"
]
TIME_FIELDS = ["deadline", "starting_time", "alarm"]
COMPARISONS = ["before", "after", "equal"]


def choose_from_menu(title, options, back_label="Back"):
    print(f"\n{title}")
    for number, option in enumerate(options, start=1):
        print(f"{number}. {option}")
    print(f"0. {back_label}")

    choice = input("Enter your choice: ").strip()

    if choice == "0":
        return None

    try:
        index = int(choice) - 1
        if 0 <= index < len(options):
            return options[index]
    except ValueError:
        pass

    print("Invalid choice.")
    return "INVALID"


def create_record(manager):
    while True:
        record_type = choose_from_menu(
            "Choose a record type:",
            RECORD_TYPES,
            "Back to Main Menu"
        )

        if record_type is None:
            return
        if record_type == "INVALID":
            continue

        # Entering 0 while entering details returns to the record-type menu.
        if record_type == "Note":
            content = input("Enter note content (or 0 to go back): ").strip()
            if content == "0":
                continue
            record = Note(content)

        elif record_type == "Task":
            description = input(
                "Enter task description (or 0 to go back): "
            ).strip()
            if description == "0":
                continue

            deadline = input(
                "Enter deadline (e.g. 2026-11-20 18:00), "
                "or 0 to go back: "
            ).strip()
            if deadline == "0":
                continue

            record = Task(description, deadline)

        elif record_type == "Event":
            description = input(
                "Enter event description (or 0 to go back): "
            ).strip()
            if description == "0":
                continue

            starting_time = input(
                "Enter starting time (e.g. 2026-11-20 14:00), "
                "or 0 to go back: "
            ).strip()
            if starting_time == "0":
                continue

            alarm = input(
                "Enter alarm time (e.g. 2026-11-20 13:30), "
                "or 0 to go back: "
            ).strip()
            if alarm == "0":
                continue

            record = Event(description, starting_time, alarm)

        else:  # Contact
            name = input("Enter contact name (or 0 to go back): ").strip()
            if name == "0":
                continue

            address = input("Enter address (or 0 to go back): ").strip()
            if address == "0":
                continue

            mobile_number = input(
                "Enter mobile number (or 0 to go back): "
            ).strip()
            if mobile_number == "0":
                continue

            record = Contact(name, address, mobile_number)

        manager.add_record(record)
        print(f"Record created. Its ID is {record.pir_id}")
        return


def modify_record(manager):
    fields_by_type = {
        "Note": ["content"],
        "Task": ["description", "deadline"],
        "Event": ["description", "starting_time", "alarm"],
        "Contact": ["name", "address", "mobile_number"]
    }

    while True:
        pir_id = input(
            "\nEnter the ID of the record to modify "
            "(or 0 to return to Main Menu): "
        ).strip()

        if pir_id == "0":
            return

        record = manager.find_record(pir_id)
        if record is None:
            print("Record not found. Please try again.")
            continue

        print("\nCurrent record:")
        print(record.get_details())

        available_fields = fields_by_type[type(record).__name__]

        while True:
            field = choose_from_menu(
                "Choose a field to modify:",
                available_fields,
                "Back to record ID"
            )

            if field is None:
                break
            if field == "INVALID":
                continue

            new_value = input(
                f"Enter the new {field} (or 0 to choose another field): "
            ).strip()

            if new_value == "0":
                continue

            if new_value == "":
                print("The new value cannot be empty.")
                continue

            if manager.modify_record(pir_id, field, new_value):
                print("Record updated successfully.")
            else:
                print("Unable to update the record.")
            return


def search_by_type_menu(manager):
    while True:
        record_type = choose_from_menu(
            "Search records by type:",
            RECORD_TYPES,
            "Back to Main Menu"
        )

        if record_type is None:
            return
        if record_type == "INVALID":
            continue

        results = manager.search_by_type(record_type)
        display_search_results(results)
        return


def search_by_field_menu(manager):
    while True:
        field = choose_from_menu(
            "Choose a field to search:",
            SEARCH_FIELDS,
            "Back to Main Menu"
        )

        if field is None:
            return
        if field == "INVALID":
            continue

        while True:
            keyword = input(
                f"Enter a keyword for {field} "
                "(or 0 to choose another field): "
            ).strip()

            if keyword == "0":
                break

            if not keyword:
                print("Keyword cannot be empty.")
                continue

            results = manager.search_by_field(field, keyword)
            display_search_results(results)
            return


def search_by_time_menu(manager):
    while True:
        field = choose_from_menu(
            "Choose a date/time field:",
            TIME_FIELDS,
            "Back to Main Menu"
        )

        if field is None:
            return
        if field == "INVALID":
            continue

        while True:
            operator = choose_from_menu(
                "Choose a date/time comparison:",
                COMPARISONS,
                "Back to date/time field"
            )

            if operator is None:
                break
            if operator == "INVALID":
                continue

            while True:
                target_time = input(
                    "Enter date/time (e.g. 2026-11-20 18:00), "
                    "or 0 to choose another comparison: "
                ).strip()

                if target_time == "0":
                    break

                try:
                    datetime.fromisoformat(target_time)
                except ValueError:
                    print("Invalid date/time format. Please try again.")
                    continue

                results = manager.search_by_time(
                    field, operator, target_time
                )
                display_search_results(results)
                return




def build_search_condition(manager):
    text_fields = [
        "content",
        "description",
        "name",
        "address",
        "mobile_number"
    ]

    while True:
        condition = choose_from_menu(
            "Choose a search condition:",
            ["Single condition", "AND", "OR", "NOT"],
            "Back"
        )

        if condition is None:
            return None

        if condition == "INVALID":
            continue

        # NOT
        if condition == "NOT":
            results = build_search_condition(manager)

            if results is None:
                continue

            return [
                record for record in manager.records
                if record not in results
            ]

        # AND / OR
        elif condition in ["AND", "OR"]:
            print(f"\nBuild the first condition for {condition}.")

            first_results = build_search_condition(manager)

            if first_results is None:
                continue

            print(f"\nBuild the second condition for {condition}.")

            second_results = build_search_condition(manager)

            if second_results is None:
                continue

            return manager.combine_search_results(
                condition,
                first_results,
                second_results
            )

        # Single condition
        elif condition == "Single condition":

            while True:
                criterion = choose_from_menu(
                    "Choose the type of condition:",
                    ["Record type", "Text field", "Time field"],
                    "Back to condition menu"
                )

                if criterion is None:
                    break

                if criterion == "INVALID":
                    continue

                # Record type
                if criterion == "Record type":

                    while True:
                        record_type = choose_from_menu(
                            "Choose a record type:",
                            RECORD_TYPES,
                            "Back to condition type"
                        )

                        if record_type is None:
                            break

                        if record_type == "INVALID":
                            continue

                        return manager.search_by_type(record_type)

                # Text field
                elif criterion == "Text field":

                    while True:
                        field = choose_from_menu(
                            "Choose a text field:",
                            text_fields,
                            "Back to condition type"
                        )

                        if field is None:
                            break

                        if field == "INVALID":
                            continue

                        while True:
                            keyword = input(
                                f"Enter keyword for {field} "
                                "(or 0 to go back): "
                            ).strip()

                            if keyword == "0":
                                break

                            if not keyword:
                                print("Keyword cannot be empty.")
                                continue

                            return manager.search_by_field(field, keyword)

                # Time field
                elif criterion == "Time field":

                    while True:
                        field = choose_from_menu(
                            "Choose a time field:",
                            TIME_FIELDS,
                            "Back to condition type"
                        )

                        if field is None:
                            break

                        if field == "INVALID":
                            continue

                        while True:
                            operator = choose_from_menu(
                                "Choose a date/time comparison:",
                                COMPARISONS,
                                "Back to time field"
                            )

                            if operator is None:
                                break

                            if operator == "INVALID":
                                continue

                            while True:
                                target_time = input(
                                    "Enter date/time "
                                    "(YYYY-MM-DD HH:MM, or 0 to go back): "
                                ).strip()

                                if target_time == "0":
                                    break

                                try:
                                    datetime.fromisoformat(target_time)
                                except ValueError:
                                    print(
                                        "Invalid date/time format. "
                                        "Please try again."
                                    )
                                    continue

                                return manager.search_by_time(
                                    field,
                                    operator,
                                    target_time
                                )


def logical_search(manager):
    print("\n=== Logical Search ===")
    print("Combine conditions using AND, OR and NOT.")
    print("Enter 0 to return to the previous menu.")

    while True:
        results = build_search_condition(manager)

        if results is None:
            return

        print("\n=== Logical Search Results ===")
        display_search_results(results)

        # Ask whether to start another search.
        choice = choose_from_menu(
            "What would you like to do next?",
            ["Search again", "Return to Main Menu"]
        )

        if choice is None:
            return

        if choice == "INVALID":
            continue

        if choice == "Return to Main Menu":
            return


def display_search_results(results):
    if results:
        print("\nSearch results:")
        for record in results:
            print(record.get_details())
    else:
        print("No matching records found.")


def main():
    manager = PIMManager()

    while True:
        print("\n===== Personal Information Management System =====")
        print("1. Create a record")
        print("2. Display all records")
        print("3. Display one record")
        print("4. Delete a record")
        print("5. Modify a record")
        print("6. Search records by type")
        print("7. Search records by field")
        print("8. Search records by date/time")
        print("9. Search using AND / OR / NOT")
        print("10. Save records")
        print("11. Load records")
        print("12. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            create_record(manager)

        elif choice == "2":
            manager.display_all_records()

        elif choice == "3":
            pir_id = input(
                "Enter record ID (or 0 to return to Main Menu): "
            ).strip()

            if pir_id == "0":
                continue

            manager.display_record(pir_id)

        elif choice == "4":
            pir_id = input(
                "Enter record ID to delete "
                "(or 0 to return to Main Menu): "
            ).strip()

            if pir_id == "0":
                continue

            if manager.delete_record(pir_id):
                print("Record deleted.")
            else:
                print("Record not found.")

        elif choice == "5":
            modify_record(manager)

        elif choice == "6":
            search_by_type_menu(manager)

        elif choice == "7":
            search_by_field_menu(manager)

        elif choice == "8":
            search_by_time_menu(manager)

        elif choice == "9":
            logical_search(manager)

        elif choice == "10":
            filename = input(
                "Enter filename to save (e.g. records.pim), "
                "or 0 to return to Main Menu: "
            ).strip()

            if filename == "0":
                continue
            if not filename:
                print("Filename cannot be empty.")
                continue

            if not filename.endswith(".pim"):
                filename += ".pim"

            FileManager.save_records(manager.records, filename)

        elif choice == "11":
            filename = input(
                "Enter filename to load (e.g. records.pim), "
                "or 0 to return to Main Menu: "
            ).strip()

            if filename == "0":
                continue
            if not filename:
                print("Filename cannot be empty.")
                continue

            if not filename.endswith(".pim"):
                filename += ".pim"

            try:
                manager.records = FileManager.load_records(filename)
                print("Records loaded successfully.")
            except FileNotFoundError:
                print("File not found.")
            except (ValueError, KeyError):
                print("Unable to load the file. Its format may be invalid.")

        elif choice == "12":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
