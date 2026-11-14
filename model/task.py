from model.pir import PIR


class Task(PIR):
    def __init__(self, description, deadline):
        super().__init__()
        self.description = description
        self.deadline = deadline

    def update_description(self, new_description):
        self.description = new_description

    def update_deadline(self, new_deadline):
        self.deadline = new_deadline

    def get_details(self):
        return (
            f"Task | ID: {self.pir_id} | Description: {self.description} "
            f"| Deadline: {self.deadline}"
        )
