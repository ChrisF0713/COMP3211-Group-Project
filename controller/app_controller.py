"""Connects the three layers and runs the application."""

import sys

from model import (
    COMPARISONS,
    RECORD_CLASSES,
    TEXT_FIELDS,
    TIME_FIELDS,
    And,
    Not,
    Or,
    PIMError,
    PIMRepository,
    RecordNotFoundError,
    TextContains,
    TimeCompare,
    TypeIs,
    ValidationError,
)
from model.storage import with_extension

CREATE_OPTIONS = ("Note", "Task", "Event", "Contact")

# The fields to ask for, and the label to show, for each record type.
# Kept in the same order as the constructor arguments.
FIELD_PROMPTS = {
    "Note": (("content", "content"),),
    "Task": (("description", "description"), ("deadline", "deadline")),
    "Event": (
        ("description", "description"),
        ("starting_time", "starting time"),
        ("alarm", "alarm time"),
    ),
    "Contact": (
        ("name", "name"),
        ("address", "address"),
        ("mobile_number", "mobile number"),
    ),
}


class AppController:
    """Handles the menus and passes user actions to the model."""

    MAIN_MENU = (
        "Create a record",
        "Display all records",
        "Display one record",
        "Delete a record",
        "Modify a record",
        "Search by type",
        "Search by text",
        "Search by time",
        "Search with AND / OR / NOT",
        "Save records",
        "Load records",
        "Exit",
    )

    MAIN_ACTIONS = (
        "create", "display_all", "display_one", "delete", "modify",
        "search_type", "search_text", "search_time", "search_logical",
        "save", "load", "exit",
    )

    def __init__(self, repository=None, view=None, debug=False):
        self.repository = repository if repository is not None else PIMRepository()
        self.view = view
        self.debug = debug

    def run(self):
        """Show the main menu until the user exits."""
        while True:
            self.view.show_menu(
                f"===== {self.view.TITLE} =====",
                self.MAIN_MENU,
                back_label=None,
            )

            action = self._read_main_choice()

            if action == "exit":
                self.view.show("Goodbye!")
                return

            self._dispatch(action)

    def _read_main_choice(self):
        """Read a main-menu number and return the action it stands for."""
        raw = self.view.ask("Enter your choice: ")

        if raw == "0":
            return "exit"

        try:
            index = int(raw) - 1
        except ValueError:
            self.view.show_error("that is not a number")
            return "none"

        if 0 <= index < len(self.MAIN_ACTIONS):
            return self.MAIN_ACTIONS[index]

        self.view.show_error("choose a number from the menu")
        return "none"

    def _dispatch(self, action):
        """Call the handler for the chosen action."""
        handlers = {
            "create": self.create_record,
            "display_all": self.display_all,
            "display_one": self.display_one,
            "delete": self.delete_record,
            "modify": self.modify_record,
            "search_type": self.search_by_type,
            "search_text": self.search_by_text,
            "search_time": self.search_by_time,
            "search_logical": self.search_logical,
            "save": self.save_records,
            "load": self.load_records,
        }

        handler = handlers.get(action)

        if handler is None:
            return

        handler()

        if self.debug:
            # Written to stderr so the normal output stays clean.
            print(
                f"[debug] action={action} records={len(self.repository)}",
                file=sys.stderr,
            )

    def create_record(self):
        """Ask for a record type and its fields, then store the new record."""
        type_name = self._pick("Choose a record type:", CREATE_OPTIONS)

        if type_name is None:
            return

        values = []

        for field, label in FIELD_PROMPTS[type_name]:
            value = self._ask_value(f"Enter {label}", field)
            if value is None:
                return
            values.append(value)

        record_class = self._record_class(type_name)

        try:
            record = record_class(*values)
            self.repository.add(record)
        except ValidationError as exc:
            self.view.show_error(str(exc))
            return

        self.view.show_success(f"Record created. Its ID is {record.pir_id}")

    @staticmethod
    def _record_class(type_name):
        """Return the record class with the given type name."""
        for record_class in RECORD_CLASSES:
            if record_class.TYPE_NAME == type_name:
                return record_class
        raise ValidationError(f"unknown record type {type_name!r}")

    def _ask_value(self, prompt, field):
        """Ask for one field value. Returns None if the user backs out."""
        if field in TIME_FIELDS:
            hint = " (YYYY-MM-DD HH:MM, or 0 to go back)"
        else:
            hint = " (or 0 to go back)"

        value = self.view.ask(f"{prompt}{hint}: ")

        if value == "0":
            return None

        if not value:
            self.view.show_error("the value cannot be empty")
            return None

        return value

    def display_all(self):
        """Print every record."""
        self.view.show_records(
            self.repository.all(),
            "No records have been created yet.",
        )

    def display_one(self):
        """Print one record, chosen by ID."""
        pir_id = self.view.ask("Enter record ID (or 0 to go back): ")

        if pir_id == "0":
            return

        try:
            self.view.show_record(self.repository.get(pir_id))
        except RecordNotFoundError as exc:
            self.view.show_error(str(exc))

    def modify_record(self):
        """Change one field of one record."""
        pir_id = self.view.ask(
            "Enter the ID of the record to modify (or 0 to go back): "
        )

        if pir_id == "0":
            return

        try:
            record = self.repository.get(pir_id)
        except RecordNotFoundError as exc:
            self.view.show_error(str(exc))
            return

        self.view.show("Current record:")
        self.view.show_record(record)

        field = self._pick("Choose a field to modify:", record.FIELDS)

        if field is None:
            return

        value = self._ask_value(f"Enter the new {field}", field)

        if value is None:
            return

        try:
            self.repository.update(pir_id, field, value)
        except (RecordNotFoundError, ValidationError) as exc:
            self.view.show_error(str(exc))
            return

        self.view.show_success("Record updated successfully.")

    def delete_record(self):
        """Delete one record, chosen by ID."""
        pir_id = self.view.ask("Enter record ID to delete (or 0 to go back): ")

        if pir_id == "0":
            return

        try:
            self.repository.delete(pir_id)
        except RecordNotFoundError as exc:
            self.view.show_error(str(exc))
            return

        self.view.show_success("Record deleted.")

    def search_by_type(self):
        """Search for records of a given type."""
        type_name = self._pick("Choose a record type:", CREATE_OPTIONS)

        if type_name is None:
            return

        self.view.show_records(self.repository.search(TypeIs(type_name)))

    def search_by_text(self):
        """Search a text field for a piece of text."""
        field = self._pick("Choose a text field:", TEXT_FIELDS)

        if field is None:
            return

        keyword = self.view.ask(
            f"Enter a keyword for {field} (or 0 to go back): "
        )

        if keyword == "0":
            return

        try:
            self.view.show_records(self.repository.search(TextContains(field, keyword)))
        except ValidationError as exc:
            self.view.show_error(str(exc))

    def search_by_time(self):
        """Search a time field with a before, after or equal comparison."""
        field = self._pick("Choose a time field:", TIME_FIELDS)

        if field is None:
            return

        operator = self._pick("Choose a comparison:", COMPARISONS)

        if operator is None:
            return

        target = self.view.ask(
            "Enter a timestamp (YYYY-MM-DD HH:MM, or 0 to go back): "
        )

        if target == "0":
            return

        try:
            criterion = TimeCompare(field, operator, target)
            self.view.show_records(self.repository.search(criterion))
        except ValidationError as exc:
            self.view.show_error(str(exc))

    def search_logical(self):
        """Build a criterion from several conditions and search with it."""
        criterion = self._build_criterion()

        if criterion is None:
            return

        self.view.show("Criterion:")
        self.view.show(criterion.describe())
        self.view.show_records(self.repository.search(criterion))

    def _build_criterion(self):
        """Ask for a criterion and return it. Returns None if the user backs out."""
        options = ("Single test", "AND (&&)", "OR (||)", "NOT (!)")
        choice = self._pick("Build a search criterion:", options)

        if choice is None:
            return None

        if choice.startswith("NOT"):
            operand = self._build_criterion()
            if operand is None:
                return None
            return Not(operand)

        if choice.startswith("AND") or choice.startswith("OR"):
            combine = And if choice.startswith("AND") else Or

            self.view.show("First operand:")
            first = self._build_criterion()
            if first is None:
                return None

            self.view.show("Second operand:")
            second = self._build_criterion()
            if second is None:
                return None

            return combine(first, second)

        return self._build_leaf()

    def _build_leaf(self):
        """Ask for one simple test and return it."""
        kind = self._pick(
            "Choose the kind of test:",
            ("Record type", "Text field", "Time field"),
        )

        if kind is None:
            return None

        if kind == "Record type":
            type_name = self._pick("Choose a record type:", CREATE_OPTIONS)
            if type_name is None:
                return None
            return TypeIs(type_name)

        if kind == "Text field":
            field = self._pick("Choose a text field:", TEXT_FIELDS)
            if field is None:
                return None

            keyword = self.view.ask(
                f"Enter a keyword for {field} (or 0 to go back): "
            )

            if keyword == "0" or not keyword:
                return None

            try:
                return TextContains(field, keyword)
            except ValidationError as exc:
                self.view.show_error(str(exc))
                return None

        field = self._pick("Choose a time field:", TIME_FIELDS)
        if field is None:
            return None

        operator = self._pick("Choose a comparison:", COMPARISONS)
        if operator is None:
            return None

        target = self.view.ask(
            "Enter a timestamp (YYYY-MM-DD HH:MM, or 0 to go back): "
        )

        if target == "0":
            return None

        try:
            return TimeCompare(field, operator, target)
        except ValidationError as exc:
            self.view.show_error(str(exc))
            return None

    def save_records(self):
        """Save every record to a .pim file."""
        filename = self.view.ask(
            "Enter filename to save (e.g. records.pim, or 0 to go back): "
        )

        if filename == "0":
            return

        if not filename:
            self.view.show_error("the filename cannot be empty")
            return

        try:
            path = self.repository.save(filename)
        except PIMError as exc:
            self.view.show_error(str(exc))
            return

        self.view.show_success(f"Records saved to {path}.")

    def load_records(self):
        """Load records from a .pim file, replacing the current ones."""
        filename = self.view.ask(
            "Enter filename to load (e.g. records.pim, or 0 to go back): "
        )

        if filename == "0":
            return

        if not filename:
            self.view.show_error("the filename cannot be empty")
            return

        # Loading replaces everything, so warn before losing unsaved changes.
        if len(self.repository) > 0:
            answer = self.view.ask(
                f"Loading will replace the {len(self.repository)} record(s) "
                f"currently in memory; unsaved changes will be lost. "
                f"Continue? (y/n): "
            )

            if answer.casefold() != "y":
                self.view.show("Load cancelled.")
                return

        try:
            self.repository.load(filename)
        except FileNotFoundError:
            self.view.show_error(f"file not found: {with_extension(filename)}")
            return
        except PIMError as exc:
            self.view.show_error(str(exc))
            return

        self.view.show_success(f"Records loaded from {with_extension(filename)}.")

    def _pick(self, title, options):
        """Ask the user to choose one option. Returns None if they back out."""
        while True:
            self.view.show_menu(title, options)
            choice = self.view.ask_choice(options)

            if choice is None:
                return None

            if choice != "INVALID":
                return choice
