"""In-memory collection of records and the operations performed on them."""

from model.errors import RecordNotFoundError, ValidationError
from model.pir import PIR
from model.storage import Storage


class PIMRepository:
    """Holds the records and answers queries over them."""

    def __init__(self, storage=None):
        self._records = []
        self._storage = storage if storage is not None else Storage()

    def __len__(self):
        return len(self._records)

    def __iter__(self):
        return iter(self._records)

    @property
    def records(self):
        """A copy of the stored records."""
        return list(self._records)

    def add(self, record):
        """Add a record and return it."""
        if not isinstance(record, PIR):
            raise ValidationError(
                f"only records can be added, got {type(record).__name__}"
            )
        if self._index_of(record.pir_id) is not None:
            raise ValidationError(f"a record with ID {record.pir_id} already exists")
        self._records.append(record)
        return record

    def get(self, pir_id):
        """Return the record with this ID.

        Raises RecordNotFoundError if there is no such record.
        """
        position = self._index_of(pir_id)
        if position is None:
            raise RecordNotFoundError(f"no record with ID {pir_id!r}")
        return self._records[position]

    def all(self):
        """Return every stored record."""
        return list(self._records)

    def update(self, pir_id, field, value):
        """Set one field on one record and return the record.

        The record validates the value, so an invalid value leaves the
        collection unchanged.
        """
        record = self.get(pir_id)
        record.set_field(field, value)
        return record

    def delete(self, pir_id):
        """Remove the record with this ID and return it."""
        record = self.get(pir_id)
        self._records.remove(record)
        return record

    def clear(self):
        """Remove every record."""
        self._records.clear()

    def search(self, criterion):
        """Return the records that satisfy the criterion, in stored order."""
        if not hasattr(criterion, "matches"):
            raise ValidationError(
                f"expected a criterion, got {type(criterion).__name__}"
            )
        return [record for record in self._records if criterion.matches(record)]

    def save(self, filename):
        """Write every record to a .pim file and return the path used."""
        return self._storage.save(self._records, filename)

    def load(self, filename):
        """Replace the collection with the records in a .pim file.

        The file is read in full before anything is replaced, so a bad file
        leaves the existing records untouched.
        """
        self._records = self._storage.load(filename)
        return self

    def _index_of(self, pir_id):
        """Return the position of the record with this ID, or None."""
        for position, record in enumerate(self._records):
            if record.pir_id == pir_id:
                return position
        return None


# Kept so older code that used the previous class name still imports.
PIMManager = PIMRepository
