"""Search criteria, built as an expression tree.

A criterion is a predicate over one record. Leaves test a single value;
And, Or and Not combine criteria, so a tree can express any criterion the
user interface can build.
"""

from model.pir import parse_timestamp
from model.errors import ValidationError

TEXT_FIELDS = ("content", "description", "name", "address", "mobile_number")
TIME_FIELDS = ("deadline", "starting_time", "alarm")
COMPARISONS = ("before", "after", "equal")

_COMPARISON_SYMBOLS = {"before": "<", "after": ">", "equal": "="}


class Criterion:
    """A predicate over a record. Base class for all criteria."""

    def matches(self, record):
        """Return True if the record satisfies this criterion."""
        raise NotImplementedError

    def describe(self):
        """Return a readable form of this criterion."""
        raise NotImplementedError

    def __repr__(self):
        return f"{type(self).__name__}({self.describe()})"


class TextContains(Criterion):
    """Matches when a text field contains the given text, ignoring case."""

    def __init__(self, field, keyword):
        if field not in TEXT_FIELDS:
            raise ValidationError(
                f"{field!r} is not a searchable text field; "
                f"expected one of {list(TEXT_FIELDS)}"
            )
        if not isinstance(keyword, str) or not keyword.strip():
            raise ValidationError("the keyword to search for must not be empty")
        self.field = field
        self.keyword = keyword.strip()

    def matches(self, record):
        value = record.get_field(self.field)
        if value is None:
            return False
        return self.keyword.casefold() in str(value).casefold()

    def describe(self):
        return f'{self.field} contains "{self.keyword}"'


class TimeCompare(Criterion):
    """Matches when a time field is before, after or equal to a given time."""

    def __init__(self, field, operator, target):
        if field not in TIME_FIELDS:
            raise ValidationError(
                f"{field!r} is not a searchable time field; "
                f"expected one of {list(TIME_FIELDS)}"
            )
        if operator not in COMPARISONS:
            raise ValidationError(
                f"{operator!r} is not a comparison; "
                f"expected one of {list(COMPARISONS)}"
            )
        self.field = field
        self.operator = operator
        self.target = parse_timestamp(target)
        self.target_text = target.strip()

    def matches(self, record):
        value = record.get_field(self.field)
        if value is None:
            return False
        try:
            moment = parse_timestamp(value)
        except ValidationError:
            return False

        if self.operator == "before":
            return moment < self.target
        if self.operator == "after":
            return moment > self.target
        return moment == self.target

    def describe(self):
        symbol = _COMPARISON_SYMBOLS[self.operator]
        return f"{self.field} {symbol} {self.target_text}"


class TypeIs(Criterion):
    """Matches when the record is of the given type."""

    def __init__(self, type_name):
        if not isinstance(type_name, str) or not type_name.strip():
            raise ValidationError("a record type name must not be empty")
        self.type_name = type_name.strip()

    def matches(self, record):
        return record.TYPE_NAME.casefold() == self.type_name.casefold()

    def describe(self):
        return f"type = {self.type_name}"


class _Composite(Criterion):
    """Base class for criteria that combine other criteria."""

    SYMBOL = "?"

    def __init__(self, *operands):
        if not operands:
            raise ValidationError(f"{self.SYMBOL} needs at least one operand")
        for operand in operands:
            if not isinstance(operand, Criterion):
                raise ValidationError(
                    f"operands of {self.SYMBOL} must be criteria, "
                    f"got {type(operand).__name__}"
                )
        self.operands = tuple(operands)

    def describe(self):
        parts = [f"({op.describe()})" for op in self.operands]
        return f"({f' {self.SYMBOL} '.join(parts)})"


class And(_Composite):
    """Matches when every operand matches."""

    SYMBOL = "&&"

    def matches(self, record):
        return all(operand.matches(record) for operand in self.operands)


class Or(_Composite):
    """Matches when at least one operand matches."""

    SYMBOL = "||"

    def matches(self, record):
        return any(operand.matches(record) for operand in self.operands)


class Not(Criterion):
    """Matches when its operand does not match."""

    SYMBOL = "!"

    def __init__(self, operand):
        if not isinstance(operand, Criterion):
            raise ValidationError(
                f"the operand of ! must be a criterion, "
                f"got {type(operand).__name__}"
            )
        self.operand = operand

    def matches(self, record):
        return not self.operand.matches(record)

    def describe(self):
        return f"!({self.operand.describe()})"
