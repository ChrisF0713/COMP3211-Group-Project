"""Console input and output."""


class ConsoleView:
    """Reads from stdin and writes to stdout."""

    TITLE = "Personal Information Management System"

    def show(self, message=""):
        """Print one line."""
        print(message)

    def show_menu(self, title, options, back_label="Back"):
        """Print a numbered menu.

        Pass back_label=None for a menu that has no 'back' entry.
        """
        print(f"\n{title}")
        for number, option in enumerate(options, start=1):
            print(f"{number}. {option}")
        if back_label is not None:
            print(f"0. {back_label}")

    def show_records(self, records, empty_message="No matching records found."):
        """Print each record on its own line, or a message if there are none."""
        if not records:
            print(empty_message)
            return
        for record in records:
            print(record.get_details())

    def show_record(self, record):
        """Print a single record."""
        print(record.get_details())

    def show_error(self, message):
        """Print an error message."""
        print(f"Error: {message}")

    def show_success(self, message):
        """Print a confirmation message."""
        print(message)

    def ask(self, prompt):
        """Read a line of input and strip the surrounding whitespace."""
        return input(prompt).strip()

    def ask_choice(self, options, back_label="Back"):
        """Ask the user to choose one of the options.

        Returns the chosen option, None if the user chose to go back, or
        "INVALID" if the input was not a number in range.
        """
        choice = self.ask("Enter your choice: ")

        if choice == "0":
            return None

        try:
            index = int(choice) - 1
        except ValueError:
            self.show_error("that is not a number")
            return "INVALID"

        if 0 <= index < len(options):
            return options[index]

        self.show_error("choose a number from the menu")
        return "INVALID"
