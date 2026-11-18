"""A contact with a name, an address and a mobile number."""

import re

from model.errors import ValidationError
from model.pir import PIR

#: An optional leading '+', then digits, spaces and hyphens, starting and ending
#: with a digit. Letters and stray punctuation are rejected.
_MOBILE = re.compile(r"^\+?[0-9](?:[0-9\s-]*[0-9])?$")


class Contact(PIR):
    """A person the user wants to reach."""

    TYPE_NAME = "Contact"
    FIELDS = ("name", "address", "mobile_number")

    def __init__(self, name, address, mobile_number):
        super().__init__()
        self.name = self._validate_field("name", name)
        self.address = self._validate_field("address", address)
        # Keep the number as a string so leading zeros and '+' survive.
        self.mobile_number = self._validate_mobile(mobile_number)

    def _validate_mobile(self, value):
        """Return a mobile number as typed, or explain why it is not one.

        Stored as text, not a number: a leading zero and a leading '+' both have
        to survive, and a phone number is an identifier rather than a quantity.
        """
        text = self._validate_field("mobile_number", value)
        if not _MOBILE.match(text):
            raise ValidationError(
                f"mobile_number must be digits, spaces, hyphens and an optional "
                f"leading '+', got {text!r}"
            )
        return text

    def get_summary(self):
        return (
            f"{self.TYPE_NAME} | ID: {self.pir_id} "
            f"| {self.summarize(self.name)} | {self.mobile_number}"
        )

    def get_details(self):
        return (
            f"Contact | ID: {self.pir_id}\n"
            f"  Name:   {self.name}\n"
            f"  Address: {self.address}\n"
            f"  Mobile: {self.mobile_number}"
        )
