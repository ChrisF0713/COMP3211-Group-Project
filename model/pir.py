"""Abstract base class for all personal information records."""

from abc import ABC, abstractmethod
from datetime import datetime
import uuid

from model.errors import InvalidFieldError, ValidationError

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"


def parse_timestamp(value):
    """Parse 'YYYY-MM-DD HH:MM' into a datetime.

    Raises ValidationError if the value is not a non-empty string in exactly that
    format. strptime alone is too lenient -- it accepts '2026-1-5 9:00' -- so the
    text is re-rendered and compared, which pins the zero padding.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("a timestamp must be a non-empty string")

    text = value.strip()
    try:
        moment = datetime.strptime(text, TIMESTAMP_FORMAT)
    except ValueError:
        raise ValidationError(
            f"{value!r} is not a valid timestamp; expected YYYY-MM-DD HH:MM"
        )

    if moment.strftime(TIMESTAMP_FORMAT) != text:
        raise ValidationError(
            f"{value!r} is not a valid timestamp; expected YYYY-MM-DD HH:MM"
        )
    return moment


class PIR(ABC):
    """A personal information record.

    Subclasses declare their fields in FIELDS, in the same order as their
    constructor arguments. Everything else (validation, conversion to and from
    a dict) is handled here.
    """

    TYPE_NAME = "PIR"
    FIELDS = ()
    TIME_FIELDS = ()

    def __init__(self):
        self.pir_id = str(uuid.uuid4())[:8]

    def __eq__(self, other):
        if not isinstance(other, PIR):
            return NotImplemented
        return type(self) is type(other) and self.pir_id == other.pir_id

    def __hash__(self):
        return hash((type(self).__name__, self.pir_id))

    def __repr__(self):
        return f"{type(self).__name__}(id={self.pir_id!r})"

    def get_field(self, field):
        """Return the value of field, or None if this record has no such field."""
        if field not in self.FIELDS:
            return None
        return getattr(self, field)

    def set_field(self, field, value):
        """Set field on this record, validating the value first."""
        if field not in self.FIELDS:
            raise InvalidFieldError(
                f"{self.TYPE_NAME} has no field {field!r}; "
                f"expected one of {list(self.FIELDS)}"
            )
        setattr(self, field, self._validate_field(field, value))

    def _validate_field(self, field, value):
        """Validate one field value and return it, possibly normalised.

        Every field is text, so a non-string (a JSON null or a number from a
        hand-edited file) is rejected rather than stored as-is.
        """
        if not isinstance(value, str):
            raise ValidationError(
                f"{self.TYPE_NAME}.{field} must be text, "
                f"got {type(value).__name__}"
            )
        if not value.strip():
            raise ValidationError(f"{self.TYPE_NAME}.{field} must not be empty")
        if field in self.TIME_FIELDS:
            parse_timestamp(value)
            return value.strip()
        return value

    def to_dict(self):
        """Return this record as a dict ready for JSON serialisation."""
        data = {"type": self.TYPE_NAME, "pir_id": self.pir_id}
        for name in self.FIELDS:
            data[name] = getattr(self, name)
        return data

    @classmethod
    def from_dict(cls, data):
        """Rebuild a record from a dict produced by to_dict()."""
        if not isinstance(data, dict):
            raise ValidationError(
                f"expected a record object, got {type(data).__name__}"
            )
        try:
            values = [data[name] for name in cls.FIELDS]
            pir_id = data["pir_id"]
        except KeyError as exc:
            raise ValidationError(
                f"{cls.__name__} record is missing required field {exc}"
            )
        record = cls(*values)
        record.pir_id = pir_id
        return record

    @abstractmethod
    def get_details(self):
        """Return a one-line description of this record."""
