"""An event with a description, a starting time and an alarm."""

from model.errors import ValidationError
from model.pir import PIR, parse_timestamp


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
        self._validate_alarm_before_start()

    def _validate_alarm_before_start(self):
        """Reject an alarm that does not fall strictly before the start.

        An alarm exists to warn the user before the event begins, so a later
        alarm, or one at the same instant, cannot do its job.
        """
        start = parse_timestamp(self.starting_time)
        alarm = parse_timestamp(self.alarm)
        if alarm >= start:
            raise ValidationError(
                f"alarm {self.alarm!r} must be earlier than starting_time "
                f"{self.starting_time!r}"
            )

    def set_field(self, field, value):
        """Set a field, keeping the alarm-before-start rule true.

        The old value is restored if the new one would break the rule, so a
        rejected edit leaves the record exactly as it was.
        """
        previous = getattr(self, field, None)
        super().set_field(field, value)
        try:
            self._validate_alarm_before_start()
        except ValidationError:
            if previous is not None:
                setattr(self, field, previous)
            raise

    def get_summary(self):
        return (
            f"{self.TYPE_NAME} | ID: {self.pir_id} "
            f"| {self.summarize(self.description)} "
            f"| start {self.starting_time} | alarm {self.alarm}"
        )

    def get_details(self):
        return (
            f"Event | ID: {self.pir_id}\n"
            f"  Description:   {self.description}\n"
            f"  Starting time: {self.starting_time}\n"
            f"  Alarm:         {self.alarm}"
        )
