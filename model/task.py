"""A task with a description and a deadline."""

from model.pir import PIR


class Task(PIR):
    """A to-do item that falls due at a given time."""

    TYPE_NAME = "Task"
    FIELDS = ("description", "deadline")
    TIME_FIELDS = ("deadline",)

    def __init__(self, description, deadline):
        super().__init__()
        self.description = self._validate_field("description", description)
        self.deadline = self._validate_field("deadline", deadline)

    def get_summary(self):
        return (
            f"{self.TYPE_NAME} | ID: {self.pir_id} "
            f"| {self.summarize(self.description)} | due {self.deadline}"
        )

    def get_details(self):
        return (
            f"Task | ID: {self.pir_id}\n"
            f"  Description: {self.description}\n"
            f"  Deadline:    {self.deadline}"
        )
