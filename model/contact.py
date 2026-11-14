from model.pir import PIR


class Contact(PIR):
    def __init__(self, name, address, mobile_number):
        super().__init__()
        self.name = name
        self.address = address
        # Keep phone numbers as strings to preserve leading zeros and + signs.
        self.mobile_number = mobile_number

    def update_name(self, new_name):
        self.name = new_name

    def update_address(self, new_address):
        self.address = new_address

    def update_mobile_number(self, new_mobile_number):
        self.mobile_number = new_mobile_number

    def get_details(self):
        return (
            f"Contact | ID: {self.pir_id} | Name: {self.name} "
            f"| Address: {self.address} | Mobile: {self.mobile_number}"
        )
