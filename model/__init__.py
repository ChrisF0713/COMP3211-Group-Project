"""The model layer.

Exposes the record types, the search criteria, the repository and the
.pim file format.
"""

from model.contact import Contact
from model.criteria import (
    COMPARISONS,
    TEXT_FIELDS,
    TIME_FIELDS,
    And,
    Criterion,
    Not,
    Or,
    TextContains,
    TimeCompare,
    TypeIs,
)
from model.errors import (
    InvalidFieldError,
    PIMError,
    RecordNotFoundError,
    ValidationError,
)
from model.event import Event
from model.note import Note
from model.pir import TIMESTAMP_FORMAT, PIR, parse_timestamp
from model.repository import PIMManager, PIMRepository
from model.storage import FILE_EXTENSION, RECORD_TYPES, Storage
from model.task import Task

__all__ = [
    "PIR",
    "Note",
    "Task",
    "Event",
    "Contact",
    "Criterion",
    "TextContains",
    "TimeCompare",
    "TypeIs",
    "And",
    "Or",
    "Not",
    "TEXT_FIELDS",
    "TIME_FIELDS",
    "COMPARISONS",
    "PIMRepository",
    "PIMManager",
    "Storage",
    "RECORD_TYPES",
    "FILE_EXTENSION",
    "TIMESTAMP_FORMAT",
    "parse_timestamp",
    "PIMError",
    "ValidationError",
    "RecordNotFoundError",
    "InvalidFieldError",
]

# Every record type, in the order the interface offers them.
RECORD_CLASSES = (Note, Task, Event, Contact)
