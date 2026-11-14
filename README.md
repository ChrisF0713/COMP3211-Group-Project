# Personal Information Management System (PIM)

## 1. Project Description

The Personal Information Management System (PIM) is a command-line application developed using Python and Object-Oriented Programming (OOP).

It allows users to manage different types of personal information records, including Notes, Tasks, Events, and Contacts.

## 2. Main Features

The system provides the following functions:

1. Create new records.
2. Display all records.
3. Display a specific record using its ID.
4. Delete records.
5. Modify existing records.
6. Search records by type.
7. Search records by field and keyword.
8. Search records by date and time.
9. Combine search conditions using AND, OR, and NOT.
10. Save records to a file.
11. Load records from a file.

## 3. Record Types

- **Note:** Stores text content.
- **Task:** Stores a task description and deadline.
- **Event:** Stores an event description, starting time, and alarm.
- **Contact:** Stores a contact's name, address, and mobile number.

## 4. Project Structure

```text
PIM_Project/
├── main.py
├── pim_manager.py
├── file_manager.py
├── test_pim_manager.py
├── test_file_manager.py
└── model/
    ├── __init__.py
    ├── pir.py
    ├── note.py
    ├── task.py
    ├── event.py
    └── contact.py
```

## 5. Object-Oriented Programming

The project uses inheritance and encapsulation through a parent class called `PIR`.

The `Note`, `Task`, `Event`, and `Contact` classes inherit from `PIR`.

Each subclass contains its own attributes and methods for managing its specific record information.

The `PIMManager` class manages the records and provides functions for creating, modifying, deleting, displaying, and searching records.

The `FileManager` class handles saving and loading records.

## 6. How to Run the Program

Make sure Python is installed.

Open the project folder in VS Code and run:

```bash
python main.py
```

Follow the numbered menu displayed in the terminal to use the system.

## 7. Running Unit Tests

To run all unit tests, use:

```bash
python -m unittest discover -v
```

The tests cover the PIMManager and FileManager functions.

## 8. File Storage

Records are saved in `.pim` files using JSON format.

Users can save their records and load them again when using the application.