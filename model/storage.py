"""Reading and writing .pim files.

A .pim file holds a JSON array of record objects. Each object carries its type
so the loader can rebuild the right class.
"""

import json
import os

from model.errors import ValidationError
from model.note import Note
from model.task import Task
from model.event import Event
from model.contact import Contact

FILE_EXTENSION = ".pim"

RECORD_TYPES = {
    cls.TYPE_NAME: cls for cls in (Note, Task, Event, Contact)
}


def with_extension(filename):
    """Return filename with the .pim extension, rejecting any other extension.

    A name that already ends in .pim is kept, and a name with no extension gets
    one added. Any other extension is an error rather than being replaced, so the
    user is told that `notes.txt` is not a .pim file instead of being silently
    redirected to `notes.pim`.
    """
    if filename.lower().endswith(FILE_EXTENSION):
        return filename

    stem, extension = os.path.splitext(filename)
    if extension and stem:
        raise ValidationError(
            f"{filename!r} has the extension {extension!r}; this system reads and "
            f"writes {FILE_EXTENSION} files, so use {stem + FILE_EXTENSION!r}"
        )
    return filename + FILE_EXTENSION


class Storage:
    """Reads and writes record collections in .pim files."""

    def save(self, records, filename):
        """Write the records to a .pim file and return the path used."""
        path = with_extension(filename)
        payload = [record.to_dict() for record in records]
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=4, ensure_ascii=False)
        except OSError as exc:
            raise ValidationError(f"could not write {path}: {exc}")
        return path

    def load(self, filename):
        """Read records from a .pim file and return them as a list.

        Raises FileNotFoundError if the file does not exist, and
        ValidationError if its contents are not a valid record list.
        """
        path = with_extension(filename)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise ValidationError(f"could not read {path}: {exc}")
        except UnicodeDecodeError as exc:
            # A file that is not UTF-8 is a malformed .pim, not a crash.
            raise ValidationError(
                f"{path} is not a valid .pim file: it is not UTF-8 text ({exc.reason})"
            )
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path} is not a valid .pim file: {exc}")

        if not isinstance(payload, list):
            raise ValidationError(
                f"{path} is not a valid .pim file: expected a list of records"
            )

        records = []
        seen_ids = set()

        for position, entry in enumerate(payload, start=1):
            if not isinstance(entry, dict):
                raise ValidationError(f"{path}: record {position} is not an object")

            pir_id = entry.get("pir_id")
            if not isinstance(pir_id, str) or not pir_id.strip():
                raise ValidationError(f"{path}: record {position} has no usable pir_id")

            # Duplicate IDs would make get, update and delete ambiguous.
            if pir_id in seen_ids:
                raise ValidationError(
                    f"{path}: record {position} repeats the ID {pir_id!r} "
                    f"already used by an earlier record"
                )
            seen_ids.add(pir_id)

            type_name = entry.get("type")
            record_class = RECORD_TYPES.get(type_name)
            if record_class is None:
                raise ValidationError(
                    f"{path}: record {position} has unknown type {type_name!r}; "
                    f"expected one of {list(RECORD_TYPES)}"
                )

            try:
                records.append(record_class.from_dict(entry))
            except ValidationError as exc:
                raise ValidationError(f"{path}: record {position}: {exc}")

        return records
