from model.pir import PIR


class Event(PIR):
    def __init__(self, description, starting_time, alarm):
        super().__init__()
        self.description = description
        self.starting_time = starting_time
        self.alarm = alarm

    def update_description(self, new_description):
        self.description = new_description

    def update_starting_time(self, new_starting_time):
        self.starting_time = new_starting_time

    def update_alarm(self, new_alarm):
        self.alarm = new_alarm

    def get_details(self):
        return (
            f"Event | ID: {self.pir_id} | Description: {self.description} "
            f"| Starting time: {self.starting_time} | Alarm: {self.alarm}"
        )
