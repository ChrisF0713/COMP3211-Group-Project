from model.pir import PIR


class Note(PIR):
    def __init__(self, content):
        super().__init__()
        self.content = content

    def update_content(self, new_content):
        self.content = new_content

    def get_details(self):
        return f"Note | ID: {self.pir_id} | Content: {self.content}"
