from abc import ABC, abstractmethod
import uuid


class PIR(ABC):
    """Parent class for all Personal Information Records."""

    def __init__(self):
        self.pir_id = str(uuid.uuid4())[:8]

    @abstractmethod
    def get_details(self):
        """Return the record details as a readable string."""
        pass
