from datetime import datetime

class PIMManager:

    def __init__(self):
        self.records = []

    def add_record(self, record):
        self.records.append(record)

    def find_record(self, pir_id):
        for record in self.records:
            if record.pir_id == pir_id:
                return record
        return None

    def delete_record(self, pir_id):
        record = self.find_record(pir_id)
        if record is None:
            return False
        self.records.remove(record)
        return True

    def modify_record(self, pir_id, field, new_value):
        record = self.find_record(pir_id)

        if record is None:
            return False

        update_methods = {
            "Note": {
                "content": "update_content"
            },
            "Task": {
                "description": "update_description",
                "deadline": "update_deadline"
            },
            "Event": {
                "description": "update_description",
                "starting_time": "update_starting_time",
                "alarm": "update_alarm"
            },
            "Contact": {
                "name": "update_name",
                "address": "update_address",
                "mobile_number": "update_mobile_number"
            }
        }

        record_type = type(record).__name__
        method_name = update_methods.get(record_type, {}).get(field)

        if method_name is None:
            return False

        update_method = getattr(record, method_name)
        update_method(new_value)

        return True

    def display_all_records(self):
        if not self.records:
            print("No records have been created yet.")
            return

        for record in self.records:
            print(record.get_details())

    def display_record(self, pir_id):
        record = self.find_record(pir_id)
        if record is None:
            print("Record not found.")
        else:
            print(record.get_details())

    def search_by_type(self, record_type):
        results = []

        for record in self.records:
            if type(record).__name__.lower() == record_type.lower():
                results.append(record)

        return results

    def search_by_field(self, field, keyword):
        results = []

        for record in self.records:
            field_value = getattr(record, field, None)

            if field_value is not None:
                if keyword.lower() in str(field_value).lower():
                    results.append(record)

        return results

    def search_by_time(self, field, operator, target_time):
        results = []

        try:
            target = datetime.fromisoformat(target_time)
        except ValueError:
            print("Invalid date/time format.")
            return results

        for record in self.records:
            value = getattr(record, field, None)

            if value is None:
                continue

            try:
                record_time = datetime.fromisoformat(str(value))
            except ValueError:
                continue

            if operator == "before" and record_time < target:
                results.append(record)

            elif operator == "after" and record_time > target:
                results.append(record)

            elif operator == "equal" and record_time == target:
                results.append(record)

        return results

    def combine_search_results(self, operator, *result_sets):
        operator = operator.upper()

        if not result_sets:
            return []

        if operator == "AND":
            results = []

            for record in self.records:
                if all(
                    record in result_set
                    for result_set in result_sets
                ):
                    results.append(record)

            return results

        elif operator == "OR":
            results = []

            for record in self.records:
                if any(
                    record in result_set
                    for result_set in result_sets
                ):
                    results.append(record)

            return results

        elif operator == "NOT":
            if len(result_sets) != 1:
                return []

            results = []

            for record in self.records:
                if record not in result_sets[0]:
                    results.append(record)

            return results

        else:
            return []