"""A plain text note."""

from model.pir import PIR


class Note(PIR):
    """Free text the user wants to keep."""

    TYPE_NAME = "Note"
    FIELDS = ("content",)

    def __init__(self, content):
        super().__init__()
        self.content = self._validate_field("content", content)

    def get_details(self):
        return f"Note | ID: {self.pir_id} | Content: {self.content}"
