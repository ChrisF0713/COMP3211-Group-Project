"""Connects the three layers and runs the application."""

import sys

from model import (
    RECORD_CLASSES,
    TIME_FIELDS,
    Contact,
    PIMError,
    PIMRepository,
    RecordNotFoundError,
    ValidationError,
)
from model.expression import parse_criterion
from model.pir import parse_timestamp
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

    #: Main menu labels, in display order.
    MAIN_MENU = (
        "Create a record",
        "Display all records",
        "Display one record",
        "Modify a record",
        "Delete a record",
        "Search records",
        "Save records",
        "Load records",
        "Exit",
    )

    MAIN_ACTIONS = (
        "create", "display_all", "display_one", "modify", "delete",
        "search", "save", "load", "exit",
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
            "modify": self.modify_record,
            "delete": self.delete_record,
            "search": self.search_records,
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
        """Ask for a record type and its fields, then store the new record.

        A rule that spans two fields - an alarm must fall before its start - can
        only be checked once both are known. When the build is rejected, the last
        field is asked again rather than the whole record being discarded.
        """
        type_name = self._pick("Choose a record type:", CREATE_OPTIONS)

        if type_name is None:
            return

        record_class = self._record_class(type_name)
        prompts = FIELD_PROMPTS[type_name]
        values = []
        index = 0

        while index < len(prompts):
            field, label = prompts[index]
            value = self._ask_value(f"Enter {label}", field)

            if value is None:
                return

            if index < len(values):
                values[index] = value
            else:
                values.append(value)

            # The last field completes the record, so try the real build there.
            if index == len(prompts) - 1:
                try:
                    record = record_class(*values)
                except ValidationError as exc:
                    self.view.show_error(str(exc))
                    values.pop()
                    continue

                try:
                    self.repository.add(record)
                except ValidationError as exc:
                    self.view.show_error(str(exc))
                    values.pop()
                    continue

                self.view.show_success(f"Record created. Its ID is {record.pir_id}")
                return

            index += 1

    @staticmethod
    def _record_class(type_name):
        """Return the record class with the given type name."""
        for record_class in RECORD_CLASSES:
            if record_class.TYPE_NAME == type_name:
                return record_class
        raise ValidationError(f"unknown record type {type_name!r}")

    def _ask_value(self, prompt, field):
        """Ask for one field value, re-asking until it is accepted.

        Returns None only when the user backs out with 0. A rejected value is
        reported and the same field is asked again, so one bad date does not
        throw away the fields already entered.
        """
        if field in TIME_FIELDS:
            hint = " (YYYY-MM-DD HH:MM, or 0 to go back)"
        else:
            hint = " (or 0 to go back)"

        while True:
            value = self.view.ask(f"{prompt}{hint}: ")

            if value == "0":
                return None

            error = self._check_value(field, value)
            if error is None:
                return value

            self.view.show_error(error)

    def _check_value(self, field, value):
        """Return an error message for a bad value, or None when it is fine.

        The rule itself lives in the model, so a field is checked by asking the
        record type that owns it rather than restating the rule here.
        """
        if not value:
            return "the value cannot be empty"

        if field in TIME_FIELDS:
            try:
                parse_timestamp(value)
            except ValidationError as exc:
                return str(exc)

        if field == "mobile_number":
            try:
                Contact("placeholder", "placeholder", value)
            except ValidationError as exc:
                return str(exc)

        return None

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

        while True:
            field = self._pick("Choose a field to modify:", record.FIELDS)

            if field is None:
                return

            value = self._ask_value(f"Enter the new {field}", field)

            if value is None:
                continue  # back to the field list, keeping the record chosen

            try:
                self.repository.update(pir_id, field, value)
            except PIMError as exc:
                # The value was accepted by the prompt but the model refused it;
                # report and return to the field list rather than retrying the
                # same field for ever.
                self.view.show_error(str(exc))
                return

            self.view.show_success("Record updated successfully.")
            return

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

    #: Field names the search grammar accepts, grouped for the on-screen help.
    SEARCH_HELP = (
        "Search expression. Type a condition, or combine several.\n"
        "\n"
        "  TEXT fields   content, description, name, address, mobile_number\n"
        "                content contains milk\n"
        "                name contains \"Ali\"         (quotes allow spaces)\n"
        "                milk                        (bare word: any text field)\n"
        "\n"
        "  TIME fields   deadline, starting_time, alarm\n"
        "                deadline < 2026-11-20 18:00\n"
        "                starting_time > 2026-11-20 13:00\n"
        "                alarm = 2026-11-20 13:30\n"
        "\n"
        "  TYPE          type = Note | Task | Event | Contact\n"
        "\n"
        "  COMBINE       && and     || or     ! not     ( ) grouping\n"
        "                type = Task && description contains report\n"
        "                !(type = Contact) || name contains \"Ali\"\n"
        "\n"
        "  Only the test's own record types are searched:\n"
        "    content -> Note        deadline -> Task\n"
        "    name / address / mobile_number -> Contact\n"
        "    description / starting_time / alarm -> Task, Event\n"
    )

    def search_records(self):
        """Read search expressions until the user goes back with 0.

        Each search is independent, so a typo or an empty result does not cost a
        trip back through the main menu.
        """
        self.view.show(self.SEARCH_HELP)

        while True:
            expression = self.view.ask("\nSearch (or 0 to go back): ")

            if expression == "0":
                return

            try:
                criterion = parse_criterion(expression)
            except ValidationError as exc:
                # Keep the user at the prompt so the typo can be corrected.
                self.view.show_error(str(exc))
                continue

            self.view.show("\nCriterion:")
            self.view.show(criterion.describe())
            self.view.show_records(self.repository.search(criterion))

    def save_records(self):
        """Ask for a filename until the records are saved, or 0 to go back."""
        while True:
            filename = self.view.ask(
                "Enter filename to save (e.g. records.pim, or 0 to go back): "
            )

            if filename == "0":
                return

            if not filename:
                self.view.show_error("the filename cannot be empty")
                continue

            try:
                path = self.repository.save(filename)
            except PIMError as exc:
                self.view.show_error(str(exc))
                continue

            self.view.show_success(f"Records saved to {path}.")
            return

    def load_records(self):
        """Ask for a filename until records are loaded, or 0 to go back."""
        while True:
            filename = self.view.ask(
                "Enter filename to load (e.g. records.pim, or 0 to go back): "
            )

            if filename == "0":
                return

            if not filename:
                self.view.show_error("the filename cannot be empty")
                continue

            # Resolve the name before asking to replace anything, so a wrong
            # extension is reported instead of the user confirming and then
            # failing.
            try:
                path = with_extension(filename)
            except PIMError as exc:
                self.view.show_error(str(exc))
                continue

            # Loading replaces everything, so warn before losing unsaved changes.
            if len(self.repository) > 0:
                answer = self.view.ask(
                    f"Loading will replace the {len(self.repository)} record(s) "
                    f"currently in memory; unsaved changes will be lost. "
                    f"Continue? (y/n): "
                )

                if answer.casefold() != "y":
                    self.view.show("Load cancelled.")
                    continue

            try:
                self.repository.load(path)
            except FileNotFoundError:
                self.view.show_error(f"file not found: {path}")
                continue
            except PIMError as exc:
                self.view.show_error(str(exc))
                continue

            self.view.show_success(f"Records loaded from {path}.")
            return

    def _pick(self, title, options):
        """Ask the user to choose one option. Returns None if they back out."""
        while True:
            self.view.show_menu(title, options)
            choice = self.view.ask_choice(options)

            if choice is None:
                return None

            if choice != "INVALID":
                return choice
