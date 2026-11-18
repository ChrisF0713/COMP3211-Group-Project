"""A plain text note."""

from model.pir import PIR


class Note(PIR):
    """Free text the user wants to keep."""

    TYPE_NAME = "Note"
    FIELDS = ("content",)

    def __init__(self, content):
        super().__init__()
        self.content = self._validate_field("content", content)

    def get_summary(self):
        return f"{self.TYPE_NAME} | ID: {self.pir_id} | {self.summarize(self.content)}"

    def get_details(self):
        return f"Note | ID: {self.pir_id}\n  Content: {self.content}"
