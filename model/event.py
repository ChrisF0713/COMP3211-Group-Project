"""An event with a description, a starting time and an alarm."""

from model.pir import PIR


class Event(PIR):
    """A scheduled occurrence the user is reminded about."""

    TYPE_NAME = "Event"
    FIELDS = ("description", "starting_time", "alarm")
    TIME_FIELDS = ("starting_time", "alarm")

    def __init__(self, description, starting_time, alarm):
        super().__init__()
        self.description = self._validate_field("description", description)
        self.starting_time = self._validate_field("starting_time", starting_time)
        self.alarm = self._validate_field("alarm", alarm)

    def get_details(self):
        return (
            f"Event | ID: {self.pir_id} | Description: {self.description} "
            f"| Starting time: {self.starting_time} | Alarm: {self.alarm}"
        )
