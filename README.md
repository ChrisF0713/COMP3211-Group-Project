# Personal Information Management System (PIM)

## 1. Project Description

The Personal Information Management System (PIM) is a command-line application developed using Python and Object-Oriented Programming (OOP).

It provides a centralised way for users to create, manage, search, and store different types of personal information records, including Notes, Tasks, Events, and Contacts.

## 2. Main Features

The system provides the following functions:

1. Create new personal information records.
2. Display all existing records.
3. Display a specific record using its unique ID.
4. Delete existing records.
5. Modify information in existing records.
6. Search records by type.
7. Search records by field and keyword.
8. Search records by date and time using before, after, and equal comparisons.
9. Combine search conditions using AND, OR, and NOT operators, including nested conditions.
10. Save records to `.pim` files.
11. Load records from `.pim` files.

## 3. Record Types

The system supports four types of personal information records:

- **Note:** Stores text content for quick notes.
- **Task:** Stores a task description and deadline.
- **Event:** Stores an event description, starting time, and alarm time.
- **Contact:** Stores a contact's name, address, and mobile number.

Each record is assigned a unique ID when it is created.

## 4. Project Structure

```text
PIM_Project/
├── main.py
├── pim_manager.py
├── file_manager.py
├── test_pim_manager.py
├── test_file_manager.py
├── .gitignore
└── model/
    ├── __init__.py
    ├── pir.py
    ├── note.py
    ├── task.py
    ├── event.py
    └── contact.py
```

## 5. Object-Oriented Programming

The project applies Object-Oriented Programming principles, including inheritance and encapsulation.

A parent class named `PIR` defines the common structure of personal information records. The `Note`, `Task`, `Event`, and `Contact` classes inherit from this parent class and implement their own attributes and methods.

The main components are:

- **PIR and its subclasses:** Define the different types of personal information records.
- **PIMManager:** Manages records and provides functions for adding, finding, modifying, deleting, displaying, and searching records.
- **FileManager:** Handles saving records to and loading records from files.
- **main.py:** Provides the command-line interface through which users interact with the system.

## 6. Requirements

- Python 3
- Visual Studio Code or another Python-compatible code editor
- No third-party Python packages are required. The project uses Python standard libraries.

## 7. How to Run the Program

1. Make sure Python 3 is installed.
2. Open the project folder in Visual Studio Code.
3. Open the integrated terminal.
4. Run the following command:

```bash
python main.py
```

5. Follow the numbered menu displayed in the terminal to use the system.

Enter `0` in supported menus or input prompts to return to the previous menu.

**Date and Time Format**

When entering task deadlines, event starting times, or alarm times, use the following format:

```text
YYYY-MM-DD HH:MM
```

Example:

```text
2026-11-20 18:00
```

## 8. Running Unit Tests

To run all unit tests, execute the following command in the project directory:

```bash
python -m unittest discover -v
```

The test files cover the functionality of `PIMManager` and `FileManager`, including record management, searching, saving, and loading.

## 9. File Storage

The system stores personal information records in files with the `.pim` extension.

The files use JSON format internally to store record information, including record types, IDs, and their corresponding attributes.

Users can save their records and load them again in a later session. Original record IDs are preserved when records are loaded.
