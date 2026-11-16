"""A contact with a name, an address and a mobile number."""

from model.pir import PIR


class Contact(PIR):
    """A person the user wants to reach."""

    TYPE_NAME = "Contact"
    FIELDS = ("name", "address", "mobile_number")

    def __init__(self, name, address, mobile_number):
        super().__init__()
        self.name = self._validate_field("name", name)
        self.address = self._validate_field("address", address)
        # Keep the number as a string so leading zeros and '+' survive.
        self.mobile_number = self._validate_field("mobile_number", mobile_number)

    def get_details(self):
        return (
            f"Contact | ID: {self.pir_id} | Name: {self.name} "
            f"| Address: {self.address} | Mobile: {self.mobile_number}"
        )
